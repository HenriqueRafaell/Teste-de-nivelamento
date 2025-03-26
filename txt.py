import os
import requests
import zipfile
import pandas as pd
import pdfplumber
from bs4 import BeautifulSoup

download_dir = "downloads"
os.makedirs(download_dir, exist_ok=True)

# 1. TESTE DE WEB SCRAPING
url = "https://www.gov.br/ans/pt-br/acesso-a-informacao/participacao-da-sociedade/atualizacao-do-rol-de-procedimentos"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')


anexos = [a['href'] for a in soup.find_all('a', href=True) if 'Anexo' in a.text]

pdf_files = []
for anexo in anexos:
    pdf_url = anexo if anexo.startswith("http") else f"https://www.gov.br{anexo}"
    pdf_name = pdf_url.split("/")[-1]
    pdf_path = os.path.join(download_dir, pdf_name)
    pdf_files.append(pdf_path)
    
    with open(pdf_path, "wb") as f:
        f.write(requests.get(pdf_url).content)


zip_path = os.path.join(download_dir, "anexos.zip")
with zipfile.ZipFile(zip_path, 'w') as zipf:
    for pdf in pdf_files:
        zipf.write(pdf, os.path.basename(pdf))

# 2. TESTE DE TRANSFORMAÇÃO DE DADOS
anexo_i_path = pdf_files[0]  
data = []
with pdfplumber.open(anexo_i_path) as pdf:
    for page in pdf.pages:
        table = page.extract_table()
        if table:
            data.extend(table)

df = pd.DataFrame(data[1:], columns=data[0])  


df.replace({"OD": "Odontológico", "AMB": "Ambulatorial"}, inplace=True)

csv_path = os.path.join(download_dir, "Rol_Procedimentos.csv")
df.to_csv(csv_path, index=False, encoding='utf-8')

zip_csv_path = os.path.join(download_dir, "Teste_seu_nome.zip")
with zipfile.ZipFile(zip_csv_path, 'w') as zipf:
    zipf.write(csv_path, os.path.basename(csv_path))

print("Processo concluído!")
# 3. TESTE DE BANCO DE DADOS

contabeis_url = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"
operadoras_url = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"

def download_file(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)
        print(f"Download concluído: {save_path}")
    else:
        print(f"Erro ao baixar {url}")


operadoras_path = os.path.join(download_dir, "operadoras_ativas.csv")
download_file(operadoras_url, operadoras_path)

# 4. TESTE DE API 

app = FastAPI()

df_operadoras = pd.read_csv(operadoras_path)

class OperadoraResponse(BaseModel):
    registro_ans: str
    nome: str
    cnpj: str
    modalidade: str
    uf: str

@app.get("/operadoras/", response_model=list[OperadoraResponse])
def buscar_operadoras(q: str = Query(..., description="Termo de busca na lista de operadoras")):
    filtro = df_operadoras[df_operadoras["nome"].str.contains(q, case=False, na=False)]
    return filtro.to_dict(orient="records")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

print("API pronta! Acesse em http://127.0.0.1:8000/docs")

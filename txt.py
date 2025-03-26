import os
import requests
import zipfile
import pandas as pd
import pdfplumber
from bs4 import BeautifulSoup

# Diretório para salvar os arquivos
download_dir = "downloads"
os.makedirs(download_dir, exist_ok=True)

# 1. TESTE DE WEB SCRAPING
url = "https://www.gov.br/ans/pt-br/acesso-a-informacao/participacao-da-sociedade/atualizacao-do-rol-de-procedimentos"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Encontrar os links dos anexos
anexos = [a['href'] for a in soup.find_all('a', href=True) if 'Anexo' in a.text]

pdf_files = []
for anexo in anexos:
    pdf_url = anexo if anexo.startswith("http") else f"https://www.gov.br{anexo}"
    pdf_name = pdf_url.split("/")[-1]
    pdf_path = os.path.join(download_dir, pdf_name)
    pdf_files.append(pdf_path)
    
    with open(pdf_path, "wb") as f:
        f.write(requests.get(pdf_url).content)

# Compactar PDFs
zip_path = os.path.join(download_dir, "anexos.zip")
with zipfile.ZipFile(zip_path, 'w') as zipf:
    for pdf in pdf_files:
        zipf.write(pdf, os.path.basename(pdf))

# 2. TESTE DE TRANSFORMAÇÃO DE DADOS
anexo_i_path = pdf_files[0]  # Supondo que o Anexo I seja o primeiro

data = []
with pdfplumber.open(anexo_i_path) as pdf:
    for page in pdf.pages:
        table = page.extract_table()
        if table:
            data.extend(table)

df = pd.DataFrame(data[1:], columns=data[0])  # Usando a primeira linha como cabeçalho

# Substituir abreviações de OD e AMB
df.replace({"OD": "Odontológico", "AMB": "Ambulatorial"}, inplace=True)

# Salvar como CSV
csv_path = os.path.join(download_dir, "Rol_Procedimentos.csv")
df.to_csv(csv_path, index=False, encoding='utf-8')

# Compactar CSV
zip_csv_path = os.path.join(download_dir, "Teste_seu_nome.zip")
with zipfile.ZipFile(zip_csv_path, 'w') as zipf:
    zipf.write(csv_path, os.path.basename(csv_path))

print("Processo concluído!")

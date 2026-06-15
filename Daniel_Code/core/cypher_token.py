import qrcode
import json
import os
from pyzbar.pyzbar import decode
from PIL import Image

class QRCodeJSONHandler:
    def __init__(self, json_data=None):
        self.json_data = json_data

    def gerar_qr_code(self, caminho_saida):
        if not self.json_data:
            print("[Erro] Nenhum dado para gerar o QR Code.")
            return
        dados_str = json.dumps(self.json_data)
        qr = qrcode.make(dados_str)
        qr.save(caminho_saida)
        print(f"[Sucesso] QR Code blindado gerado em: {caminho_saida}")

    def ler_qr_code(self, caminho_imagem):
        try:
            img = Image.open(caminho_imagem)
            resultados = decode(img)
            if resultados:
                dados_str = resultados[0].data.decode('utf-8')
                return json.loads(dados_str)
            else:
                return None
        except Exception as e:
            print(f"[Erro] Falha ao ler QR Code: {e}")
            return None

if __name__ == "__main__":
    # 1. Inteligência de Caminhos: Encontra a raiz do projeto dinamicamente
    # Pega a pasta onde este script está (core) e volta um nível para trás (raiz)
    pasta_core = os.path.dirname(os.path.abspath(__file__))
    raiz_projeto = os.path.dirname(pasta_core)

    # 2. Define exatamente onde ler o JSON e onde salvar a imagem
    caminho_data_json = os.path.join(raiz_projeto, "data.json")
    caminho_qr_code = os.path.join(raiz_projeto, "token_qr.png")

    # 3. Executa a leitura e geração
    if os.path.exists(caminho_data_json):
        with open(caminho_data_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        handler = QRCodeJSONHandler(dados)
        print("[-] Criptografando dados e gerando imagem...")
        handler.gerar_qr_code(caminho_qr_code)
    else:
        print(f"[!] Arquivo base não encontrado: {caminho_data_json}")
        print("Crie o arquivo 'data.json' na raiz do projeto com seus tokens.")
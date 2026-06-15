import json
import os
import qrcode
from PIL import Image
from pyzbar.pyzbar import decode

# ==============================================================================
# 0. GERADOR DE QR CODE DO JSON CON TOKENS DO GITHUB
# ==============================================================================
class QRCodeJSONHandler:
    def __init__(self, json_file_path=None, json_data=None):
        """
        Inicializa a classe carregando os dados de um arquivo JSON ou de um dicionário direto.
        """
        if json_file_path:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        elif json_data is not None:
            self.data = json_data
        else:
            raise ValueError("É necessário fornecer 'json_file_path' ou 'json_data'.")

    def gerar_qr_code(self, caminho_saida="qrcode_saida.png"):
        """
        Converte os dados JSON em uma string e gera uma imagem de QR Code.
        """
        # Converte o dicionário para uma string JSON compacta
        json_string = json.dumps(self.data, ensure_ascii=False, separators=(',', ':'))
        
        # Configura e gera o QR Code
        # ERROR_CORRECT_H é usado para garantir que o QR Code seja legível mesmo se danificado
        qr = qrcode.QRCode(
            version=None, # Permite que a biblioteca escolha o tamanho ideal automaticamente
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(json_string)
        qr.make(fit=True)

        # Cria a imagem e salva
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(caminho_saida)
        print(f"✅ QR Code gerado e salvo com sucesso em: {caminho_saida}")
        return caminho_saida

    def ler_qr_code(self, caminho_imagem):
        """
        Lê a imagem do QR Code e recupera os dados JSON originais.
        """
        try:
            # Abre a imagem
            img = Image.open(caminho_imagem)
            
            # Decodifica os dados do QR Code
            dados_decodificados = decode(img)
            
            if not dados_decodificados:
                raise ValueError("Nenhum QR Code foi encontrado na imagem fornecida.")
            
            # Extrai a string e converte de volta para dicionário Python (JSON)
            string_json = dados_decodificados[0].data.decode('utf-8')
            json_recuperado = json.loads(string_json)
            
            print("✅ JSON recuperado com sucesso!")
            return json_recuperado
            
        except Exception as e:
            print(f"❌ Erro ao ler o QR Code: {e}")
            return None

    @staticmethod
    def write_json(data_dict, path_file: str):
        with open(path_file, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=4, ensure_ascii=False)

    @staticmethod
    def excluir_arquivo(caminho_arquivo):
        """
        Exclui um arquivo de forma segura.
        
        :param caminho_arquivo: Caminho completo ou relativo do arquivo a ser excluído.
        """
        try:
            # Verifica se o caminho existe e é um arquivo
            if os.path.isfile(caminho_arquivo):
                os.remove(caminho_arquivo)
                print(f"Arquivo '{caminho_arquivo}' excluído com sucesso.")
            else:
                print(f"O caminho '{caminho_arquivo}' não existe ou não é um arquivo.")
        except PermissionError:
            print(f"Permissão negada para excluir '{caminho_arquivo}'.")
        except FileNotFoundError:
            print(f"Arquivo '{caminho_arquivo}' não encontrado.")
        except Exception as e:
            print(f"Ocorreu um erro ao excluir o arquivo: {e}")


# ==========================================
# Exemplo de Uso (Teste com o seu data.json)
# ==========================================
if __name__ == "__main__":
    # NOTA: O arquivo data.json deve ter a chave "token" como uma LISTA, ex:
    # {
    #   "token": [
    #               "ghp_...",
    #               "ghp_..."
    #             ],
    #   "target_user": "user",
    #   "target_repo": "repo"
    # }

    # 1. Carrega o JSON
    # handler = QRCodeJSONHandler(json_file_path="data.json")

    # 2. Gera o QR Code
    # caminho_imagem_gerada = handler.gerar_qr_code("meu_qrcode.png")

    # 3. Lê o QR Code e recupera o dict
    dados_recuperados = handler.ler_qr_code(caminho_imagem_gerada)

    # 4. Salva de volta no arquivo
    handler.write_json(dados_recuperados, "data.json")

    print("\n📦 Dados Recuperados do QR Code:")
    for chave in dados_recuperados:
        print(chave)

        valor = dados_recuperados.get(chave)
        if not isinstance(valor, str):
            if isinstance(valor, list):
                for item in valor:
                    if chave == "token":
                        palavra = f"|---------------> Token ...{item[-4:]}"
                        item = palavra
                    print(item)
        else:
            print(f"|---------------> {valor}")
        
           

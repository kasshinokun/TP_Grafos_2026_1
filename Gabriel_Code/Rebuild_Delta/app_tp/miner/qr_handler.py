import json
from PIL import Image
from pyzbar.pyzbar import decode
from typing import Dict, Any, List

def decode_github_qr(image_path: str) -> Dict[str, Any]:
    """
    Decodifica um QR Code contendo tokens do GitHub e informações do repositório.
    Formato esperado do JSON no QR Code:
    {
        "token": ["token1", "token2", ...],
        "target_user": "owner",
        "target_repo": "repo"
    }
    """
    try:
        img = Image.open(image_path)
        decoded_objects = decode(img)
        
        if not decoded_objects:
            raise ValueError("Nenhum QR Code encontrado na imagem.")
            
        # Pega o primeiro QR Code encontrado
        content = decoded_objects[0].data.decode('utf-8')
        data = json.loads(content)
        
        # Validação básica
        if "token" not in data:
            raise ValueError("QR Code não contém a chave 'token'.")
            
        return data
    except Exception as e:
        raise Exception(f"Erro ao processar QR Code: {str(e)}")

def mask_token(token: str) -> str:
    """Retorna uma versão mascarada do token para exibição segura."""
    clean = token.strip()
    if len(clean) >= 8:
        return f"{clean[:4]}...{clean[-4:]}"
    return "****"

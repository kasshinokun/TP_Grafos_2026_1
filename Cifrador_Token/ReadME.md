# 🔐 Cifrador Token

> Ferramenta para cifrar tokens sensíveis (ex.: tokens do GitHub) dentro de imagens QR Code, permitindo armazená-los e transportá-los de forma segura sem expô-los como texto puro.

---

## 💡 Motivação

Tokens de acesso (como `ghp_...` do GitHub) são credenciais sensíveis que nunca devem ficar expostos em arquivos de texto ou repositórios. Este projeto resolve esse problema convertendo os tokens em um QR Code — um formato visual que não é indexado por scanners de credenciais e pode ser armazenado como imagem.

---

## 🗂️ Estrutura do Projeto
## Base
```
Cifrador_Token/
├── cypher_token.py              # Implementação da Aplicação
├── data.json                    # Arquivo de entrada com os tokens 
└── token_qr.png                 # QR Code gerado (saída)
```
## Organização de Cada Versão
```
Daniel/                       # Versão original simplificada
  ├── cypher_token.py         # Implementação inicial da classe QRCodeJSONHandler
  └── README.md

Gabriel/                        # Versão original reconstruída e aprimorada
  ├── cypher_token_rebuild.py   # Versão com correções, melhorias e novos métodos
  └── README.md
```

---

## 📄 Formato do `data.json`

Crie o arquivo `data.json` na **raiz do projeto** com a seguinte estrutura:

```json
{
  "token": [
    "ghp_SeuPrimeiroToken",
    "ghp_SeuSegundoToken"
  ],
  "target_user": "seu-usuario-github",
  "target_repo":  "seu-repositorio"
}
```

> ⚠️ **Atenção:** Adicione `data.json` e `token_qr.png` ao `.gitignore`. Nunca os versione.

---

## ⚙️ Dependências

Instale as dependências com:

```bash
pip install qrcode[pil] pyzbar Pillow
```

| Biblioteca  | Função                              |
|-------------|-------------------------------------|
| `qrcode`    | Geração de imagens QR Code          |
| `Pillow`    | Manipulação de imagens              |
| `pyzbar`    | Leitura/decodificação de QR Codes   |

---

## 🚀 Como Usar

### 1. Crie o `data.json` na raiz com seus tokens

### 2. Escolha a versão e execute:

**Versão Daniel (simplificada):**
```bash
python Daniel/cypher_token.py
```

**Versão Gabriel (recomendada):**
```bash
python Gabriel/cypher_token_rebuild.py
```

### 3. O arquivo `token_qr.png` será gerado na raiz do projeto.

Para recuperar os dados do QR Code, instancie a classe e chame `ler_qr_code()` apontando para a imagem gerada.

---

## 🔄 Versões

| Versão   | Arquivo                       | Descrição                              |
|----------|-------------------------------|----------------------------------------|
| Simplificada | `Daniel/cypher_token.py`      | Implementação similar a inicial, funcional       |
| Rebuild  | `Gabriel/cypher_token_rebuild.py` | Versão aprimorada com correção de erro, mais métodos e melhor robustez |

Consulte o `README.md` dentro de cada pasta para mais detalhes sobre cada versão.

---

## 👥 Autores

| Desenvolvedor | Contribuição                        |
|---------------|-------------------------------------|
| Daniel (release)      | Versão simplificada do cifrador         |
| Gabriel(main)       | Reconstrução e aprimoramento        |

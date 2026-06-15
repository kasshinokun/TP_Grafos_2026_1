# 📁 Daniel — Versão Original

Esta pasta contém a **implementação simplificada** do Cifrador Token feito por Gabriel, sob a lógica de Daniel. É a base conceitual do projeto: lê um arquivo `data.json` da raiz, converte os dados para QR Code e também permite a leitura de volta.

---

## 📄 Arquivo

| Arquivo             | Descrição                            |
|---------------------|--------------------------------------|
| `cypher_token.py`   | Classe `QRCodeJSONHandler` original  |

---

## 🧩 Classe `QRCodeJSONHandler`

### Construtor

```python
QRCodeJSONHandler(json_data=None)
```

| Parâmetro    | Tipo   | Descrição                                  |
|--------------|--------|--------------------------------------------|
| `json_data`  | `dict` | Dicionário Python com os dados a cifrar    |

---

### Métodos

#### `gerar_qr_code(caminho_saida)`

Serializa o dicionário como JSON e gera uma imagem QR Code no caminho indicado.

```python
handler.gerar_qr_code("token_qr.png")
```

| Parâmetro       | Tipo  | Descrição                          |
|-----------------|-------|------------------------------------|
| `caminho_saida` | `str` | Caminho completo do arquivo `.png` |

---

#### `ler_qr_code(caminho_imagem)`

Decodifica uma imagem QR Code e retorna os dados como dicionário Python.

```python
dados = handler.ler_qr_code("token_qr.png")
```

| Parâmetro        | Tipo  | Descrição                           |
|------------------|-------|-------------------------------------|
| `caminho_imagem` | `str` | Caminho da imagem `.png` a ser lida |

**Retorno:** `dict` com os dados originais, ou `None` em caso de erro.

---

## 🚀 Execução

Coloque o `data.json` na raiz do projeto e execute:

```bash
python Daniel/cypher_token.py
```

O script localiza automaticamente a raiz do projeto a partir de sua própria localização, lê o `data.json` e salva o QR Code em `token_qr.png` na raiz.

---

## ⚠️ Limitações desta versão

> Estas limitações foram corrigidas na versão de Gabriel (`/Gabriel`).

- Usa `qrcode.make()` direto, sem configurar nível de correção de erro — QR Codes podem ser menos robustos a danos físicos ou baixa resolução.
- Não suporta passar o caminho do JSON diretamente no construtor; os dados precisam ser pré-carregados externamente.
- Não possui métodos utilitários para salvar JSON ou excluir arquivos gerados.

---

## 📦 Dependências

```bash
pip install qrcode pyzbar Pillow
```

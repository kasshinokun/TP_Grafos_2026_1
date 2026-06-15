# 📁 Gabriel — Versão Reconstruída (Rebuild)

Esta pasta contém a **versão aprimorada** do Cifrador Token, desenvolvida por Gabriel como um rebuild da implementação original. Traz maior robustez, flexibilidade de entrada e métodos utilitários extras.

---

## 📄 Arquivo

| Arquivo                      | Descrição                                        |
|------------------------------|--------------------------------------------------|
| `cypher_token_rebuild.py`    | Classe `QRCodeJSONHandler` reconstruída e aprimorada |

---

## 🆕 Melhorias em Relação à Versão Original

| Aspecto                   | Versão Daniel                   | Versão Gabriel (Rebuild)                          |
|---------------------------|---------------------------------|---------------------------------------------------|
| Entrada de dados          | Apenas `dict` via construtor    | Aceita `dict` **ou** caminho de arquivo `.json`   |
| Correção de erro QR       | Padrão (`ERROR_CORRECT_M`)      | Alta (`ERROR_CORRECT_H`) — mais resistente a danos|
| Configuração do QR Code   | Automática (sem controle)       | Controlada: `box_size=10`, `border=4`, `version=None` (auto) |
| Retorno de `gerar_qr_code`| Nenhum                          | Retorna o caminho da imagem gerada                |
| Métodos utilitários       | Nenhum                          | `write_json()` e `excluir_arquivo()`              |
| Tratamento de erros       | Básico                          | Detalhado, com mensagens específicas por tipo     |

---

## 🧩 Classe `QRCodeJSONHandler`

### Construtor

```python
QRCodeJSONHandler(json_file_path=None, json_data=None)
```

| Parâmetro        | Tipo   | Descrição                                                    |
|------------------|--------|--------------------------------------------------------------|
| `json_file_path` | `str`  | Caminho para um arquivo `.json` a ser lido automaticamente   |
| `json_data`      | `dict` | Dicionário Python passado diretamente                        |

> Ao menos um dos parâmetros deve ser fornecido; caso contrário, um `ValueError` é levantado.

---

### Métodos

#### `gerar_qr_code(caminho_saida="qrcode_saida.png")`

Converte os dados em JSON compacto e gera o QR Code com alta correção de erro (`ERROR_CORRECT_H`).

```python
caminho = handler.gerar_qr_code("token_qr.png")
```

| Parâmetro       | Tipo  | Padrão               | Descrição                      |
|-----------------|-------|----------------------|--------------------------------|
| `caminho_saida` | `str` | `"qrcode_saida.png"` | Caminho da imagem de saída     |

**Retorno:** `str` — o próprio `caminho_saida`, útil para encadear com `ler_qr_code()`.

---

#### `ler_qr_code(caminho_imagem)`

Decodifica a imagem QR Code e retorna os dados como dicionário Python.

```python
dados = handler.ler_qr_code("token_qr.png")
```

| Parâmetro        | Tipo  | Descrição                         |
|------------------|-------|-----------------------------------|
| `caminho_imagem` | `str` | Caminho da imagem `.png` a ser lida |

**Retorno:** `dict` com os dados originais, ou `None` em caso de erro.

---

#### `write_json(data_dict, path_file)` *(estático)*

Salva um dicionário Python como arquivo `.json` formatado.

```python
QRCodeJSONHandler.write_json(dados, "output.json")
```

| Parâmetro   | Tipo   | Descrição                        |
|-------------|--------|----------------------------------|
| `data_dict` | `dict` | Dicionário a ser salvo           |
| `path_file` | `str`  | Caminho do arquivo de saída      |

---

#### `excluir_arquivo(caminho_arquivo)` *(estático)*

Exclui um arquivo de forma segura, verificando existência e tratando permissões.

```python
QRCodeJSONHandler.excluir_arquivo("token_qr.png")
```

| Parâmetro         | Tipo  | Descrição                     |
|-------------------|-------|-------------------------------|
| `caminho_arquivo` | `str` | Caminho completo do arquivo   |

---

## 🚀 Execução

### Configuração do `data.json`

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

### Rodando o script

```bash
python Gabriel/cypher_token_rebuild.py
```

A execução padrão (`__main__`) realiza o fluxo completo:
1. Carrega `data.json`
2. Gera `meu_qrcode.png`
3. Lê o QR Code e exibe os dados recuperados no terminal (mascarando os tokens, mostrando apenas os últimos 4 caracteres)

---

## 📦 Dependências

```bash
pip install qrcode pyzbar Pillow
```

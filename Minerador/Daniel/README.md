# 🔍 Minerador — Daniel

Minerador de dados do GitHub para repositórios públicos, com arquitetura orientada a eventos (Pub/Sub) e coleta paralela via múltiplas threads.

---

## 📁 Estrutura

```
Daniel/
├── main_miner.py          # Ponto de entrada — dispara o evento START_MINING
└── core/
    ├── event_bus.py       # Barramento de eventos Singleton (Pub/Sub nativo)
    └── miner_app.py       # Micro-aplicação de mineração com pool de threads
```

---

## 🏗️ Arquitetura

### `EventBus` (`core/event_bus.py`)

Barramento de eventos implementado como **Singleton** usando apenas a biblioteca padrão do Python. Garante que todas as micro-aplicações compartilhem a mesma instância.

| Método | Descrição |
|---|---|
| `subscribe(event_type, callback)` | Registra um handler para um tipo de evento |
| `publish(event_type, payload)` | Dispara um evento para todos os handlers registrados |

### `MinerApp` (`core/miner_app.py`)

Micro-aplicação que se inscreve no evento `START_MINING` e realiza a coleta de dados da API do GitHub usando **pool de threads**, uma por token de autenticação.

**Fluxo principal:**

```
START_MINING (repo, qr_path)
       │
       ▼
  Lê tokens do QR Code
       │
       ▼
  Monta fila de URLs (todas as páginas de issues)
       │
       ▼
  Lança N threads (uma por token)
       │  ├─ Thread-1 → consome URLs da fila, baixa dados
       │  ├─ Thread-2 → consome URLs da fila, baixa dados
       │  └─ Thread-N → ...
       ▼
  Agrega resultados com Lock (thread-safe)
       │
       ▼
  Salva github_dados_minerados.json
```

**Dados coletados por issue:**
- `issue_number` — número da issue
- `opened_by` — usuário que abriu
- `closed_by` — usuário que fechou

Apenas issues onde `closed_by ≠ opened_by` são incluídas no dataset de grafo.

---

## 🔐 Autenticação via QR Code

Os tokens da API do GitHub são armazenados em um QR Code (`token_qr.png`) e lidos em memória via `QRCodeJSONHandler`. Isso evita expor tokens em texto plano no código ou em arquivos de configuração.

Formato esperado do JSON embutido no QR Code:
```json
{
  "token": ["ghp_token1", "ghp_token2", "..."]
}
```

---

## 🚀 Uso

```python
# main_miner.py — execução direta
python main_miner.py
```

O repositório alvo padrão é `microsoft/TypeScript`. Para alterar, edite a chamada em `main_miner.py`:

```python
bus.publish("START_MINING", {"repo": "owner/repo", "qr_path": "token_qr.png"})
```

---

## 📤 Saída

Após a execução, dois arquivos são gerados:

| Arquivo | Conteúdo |
|---|---|
| `github_dados_minerados.json` | Objetos JSON brutos de cada issue (compatível com o formato esperado pelo Lapidador) |
| _(resultados_grafos)_ | Lista de `{issue_number, opened_by, closed_by}` pronta para construção de grafo |

---

## ⚙️ Requisitos

- Python **3.10+**
- Sem dependências externas (apenas `urllib`, `json`, `threading`, `queue`)
- Token(s) da API do GitHub com permissão de leitura em repositórios públicos
- Biblioteca `qrcode` e `Pillow` para leitura do QR Code (`pip install qrcode pillow`)

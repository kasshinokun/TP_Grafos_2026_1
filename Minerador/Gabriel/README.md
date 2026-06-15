# 🔍 Minerador — Gabriel

Orquestrador híbrido de alta performance para mineração de dados do GitHub, com suporte simultâneo a **modo tokenizado** (aiohttp assíncrono + threads) e **modo sem token** (requisições com controle de rate-limit), interface gráfica opcional e pipeline de pré-processamento integrado.

---

## 📁 Estrutura

```
Gabriel/
├── orchestrator_hibrido_alpha0e.py   # Versão de produção (sem GUI)
└── orchestrator_hibrido_alpha0f.py   # Versão com GUI (CTk + PyQt6)
```

---

## 🏗️ Arquitetura

O orquestrador opera em dois modos de execução paralelos:

### Modo Tokenizado (com token GitHub)

- Utiliza **`aiohttp`** com `asyncio` para múltiplas coroutines por thread
- Configurável via `THREADS_PER_TYPE` (padrão: 2 threads × 4 tipos = 8 threads)
- Cada thread processa até `MAX_ASYNC_CONCURRENCY_PER_THREAD` (padrão: 5) requisições simultâneas
- Tokens lidos de um **QR Code** (`QRCodeJSONHandler`) — nunca expostos em texto plano

### Modo Sem Token (untokenized_runner)

- Utiliza **`requests`** síncronos com controle de cooldown automático
- Exibe tempo restante em minutos quando o rate-limit da API é atingido
- Gerenciado por `ShutdownManager` para encerramento seguro (graceful shutdown)

### Tipos de dados coletados

| Tipo | Descrição |
|---|---|
| `issue_comments` | Comentários em issues |
| `pr_comments` | Comentários em pull requests |
| `closed_issues` | Issues fechadas (com autor e responsável pelo fechamento) |
| `pr_reviews` | Reviews de pull requests (com `_pr_author` e `_pr_url` injetados) |

---

## 🔧 Componentes Principais

### `QRCodeJSONHandler`

Classe responsável por gerar e ler QR Codes contendo tokens GitHub em formato JSON. Garante que credenciais nunca fiquem em texto plano no repositório.

```python
handler = QRCodeJSONHandler(json_data={"token": ["ghp_..."]})
handler.gerar_qr_code("meu_token.png")

# Leitura:
dados = QRCodeJSONHandler.ler_qr_code("meu_token.png")
```

### `ShutdownManager`

Gerencia o encerramento ordenado das threads e coroutines, evitando requisições interrompidas a meio.

### Pipeline pós-mineração

Ao fim da coleta, o evento `MINING_COMPLETE` é publicado e o `Lapidador` (`main_rebuild.py`) é invocado automaticamente para transformar os dados brutos em interações normalizadas.

---

## 🔄 Fluxo Completo

```
Token QR Code
     │
     ▼
Orquestrador Híbrido
     │
     ├─ [Thread Pool Tokenizado]
     │   ├─ asyncio + aiohttp
     │   ├─ issue_comments / pr_comments
     │   ├─ closed_issues
     │   └─ pr_reviews (com injeção de _pr_author/_pr_url)
     │
     └─ [untokenized_runner] (fallback sem token)
         └─ requests + cooldown automático
     │
     ▼
notification_queue → MINING_COMPLETE
     │
     ▼
Lapidador (main_rebuild.py)
     │
     ▼
dados_lapidados.json
```

---

## 🖥️ Versões

| Arquivo | Descrição |
|---|---|
| `alpha0e.py` | Versão de produção — sem GUI, todos os bugs críticos corrigidos |
| `alpha0f.py` | Versão com interface gráfica — importa `gui_ctk` (CustomTkinter) e `gui_pyqt6` |

### Correções da versão alpha0e
- **[BUG CRÍTICO]** Removida chamada dupla de `fetch()` que dobrava o consumo de rate-limit
- **[BUG]** Corrigida injeção de `_pr_author`/`_pr_url` no worker tokenizado de `pr_reviews` (a omissão fazia o Lapidador descartar 100% das reviews)
- **[REFACTOR]** `untokenized_runner` migrado para `ShutdownManager` nativo
- **[UX]** Cooldown exibe tempo restante em minutos

---

## ⚙️ Requisitos

- Python **3.10+**
- Dependências externas:
  ```
  aiohttp
  requests
  qrcode
  Pillow
  pyzbar
  ```
- Para a versão com GUI (`alpha0f`):
  ```
  customtkinter
  PyQt6
  ```
- Token(s) da API do GitHub com permissão de leitura em repositórios públicos

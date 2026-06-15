# 🧪 Testes Unitários — Gabriel

Suite de testes para o **Orchestrator Híbrido** (minerador de dados GitHub), cobrindo os componentes de infraestrutura assíncrona: barramento de eventos, gerenciador de tokens, worker de armazenamento e interface gráfica.

---

## 📁 Estrutura

```
Gabriel/
└── test_cli/
    ├── run_all.py                      # Runner: descobre e executa todos os test_*.py
    ├── test_event_bus.py               # Testes unitários — EventBus (filas separadas)
    ├── test_token_manager.py           # Testes unitários — TokenManager (cooldown)
    ├── test_storage_worker_isolation.py# Testes unitários — BufferedStorageWorker
    ├── test_gui_smoke.py               # Smoke test — importação do módulo GUI
    ├── test_cooldown.py                # Script de integração — notificação de cooldown
    └── test_queue_separation.py        # Script de integração — separação de filas e concorrência
```

---

## 🎯 O que é testado

### `test_event_bus.py` — EventBus (`unittest`)

Valida que o barramento de eventos mantém **três filas completamente independentes**: `task_queue`, `data_queue` e `notification_queue`.

| Teste | O que valida |
|---|---|
| `test_task_roundtrip` | Publicar e consumir uma tarefa (`FETCH`) da fila correta |
| `test_data_roundtrip` | Publicar e consumir um dado (`DATA_EXTRACTED`) da fila correta |
| `test_notification_roundtrip` | Publicar e consumir uma notificação (`TOKEN_COOLDOWN`) da fila correta |
| `test_isolamento_entre_filas` | Publicar em `notification_queue` não contamina `data_queue` nem `task_queue` |

---

### `test_token_manager.py` — TokenManager (`unittest`)

Valida o ciclo de vida dos tokens de API: aquisição, liberação e controle de cooldown.

| Teste | O que valida |
|---|---|
| `test_get_release` | Token disponível é retornado; após liberação fica disponível novamente |
| `test_cooldown_block` | Token em cooldown bloqueia `all_in_cooldown()`; token com reset no passado é liberado |
| `test_next_reset_time` | `get_next_reset_time()` retorna o menor reset time entre tokens em cooldown |

---

### `test_storage_worker_isolation.py` — BufferedStorageWorker (`unittest`)

Verifica que o worker de armazenamento **não consome mensagens da fila de notificações**.

| Teste | O que valida |
|---|---|
| `test_worker_nao_drena_notificacoes` | Após iniciar e parar o worker, a notificação publicada antes ainda está na fila intacta |

---

### `test_gui_smoke.py` — Importação da GUI (`unittest`)

Smoke test mínimo para garantir que o módulo `gui_ctk` pode ser importado sem executar o `mainloop`.

| Teste | O que valida |
|---|---|
| `test_modulo_gui_importavel` | `importlib.util.find_spec("gui_ctk")` encontra o módulo na raiz do projeto |

---

### `test_cooldown.py` — Integração: Notificação de Cooldown (script)

Script de integração com threads que simula o comportamento do orchestrator ao detectar cooldowns de tokens.

| Etapa | O que valida |
|---|---|
| Cooldown individual | `publish_notification` com `TOKEN_COOLDOWN` para um único token |
| Cooldown total | Todos os tokens em cooldown; alerta crítico gerado com tempo de espera |
| Encerramento limpo | `ShutdownManager.request_shutdown()` encerra a thread de monitoramento |

> ⚠️ Este arquivo não usa `unittest.TestCase` — é executado diretamente. O `run_all.py` não o inclui na descoberta automática.

---

### `test_queue_separation.py` — Integração: Separação de Filas e Concorrência (script)

Script de integração que valida separação de filas e comportamento concorrente.

| Função | O que valida |
|---|---|
| `test_queue_separation()` | Dados e notificações são consumidos somente das filas corretas; filas ficam vazias ao final |
| `test_concurrent_producers()` | Dois produtores em threads distintas publicam 5 dados e 5 notificações; todos são consumidos corretamente |
| `test_token_manager_state()` | Estado do `TokenManager` com cooldown parcial e total; `get_next_reset_time()` retorna valor positivo |

> ⚠️ Este arquivo não usa `unittest.TestCase` — é executado diretamente. Retorna código de saída `1` se algum teste falhar.

---

### `run_all.py` — Runner Agregado

Descobre automaticamente todos os arquivos `test_*.py` no diretório `test_cli/` e executa com `unittest` em modo verboso.

```bash
python run_all.py
```

> Adiciona `../app` ao `sys.path` antes da descoberta, permitindo importar o orchestrator sem instalação de pacote.

---

## 🔧 Dependências

Os testes `unittest` importam de `orchestrator_hibrido_alpha0e` (e `alpha0b` nos scripts de integração), que devem estar presentes na pasta-pai de `test_cli/`.

```
Gabriel/
├── orchestrator_hibrido_alpha0e.py   ← importado pelos testes unittest
├── orchestrator_hibrido_alpha0b.py   ← importado pelos scripts de integração
├── gui_ctk.py                         ← necessário para test_gui_smoke.py
└── test_cli/                          ← esta pasta
```

**Sem dependências externas** além da biblioteca padrão (`unittest`, `threading`, `time`, `importlib`, `logging`).

---

## ▶️ Como Executar

**Todos os testes `unittest` via runner:**

```bash
cd Gabriel/
python test_cli/run_all.py
```

**Testes `unittest` individualmente:**

```bash
python -m unittest test_cli.test_event_bus -v
python -m unittest test_cli.test_token_manager -v
python -m unittest test_cli.test_storage_worker_isolation -v
python -m unittest test_cli.test_gui_smoke -v
```

**Scripts de integração (execução direta):**

```bash
python test_cli/test_queue_separation.py
python test_cli/test_cooldown.py
```

---

## 📊 Resumo da Cobertura

| Arquivo | Tipo | Casos de Teste | Componente Testado |
|---|---|---|---|
| `test_event_bus.py` | `unittest` | 4 | `EventBus` — filas e isolamento |
| `test_token_manager.py` | `unittest` | 3 | `TokenManager` — cooldown e reset |
| `test_storage_worker_isolation.py` | `unittest` | 1 | `BufferedStorageWorker` — não drena notificações |
| `test_gui_smoke.py` | `unittest` | 1 | `gui_ctk` — módulo importável |
| `test_queue_separation.py` | script | 3 funções | Separação de filas, concorrência, estado de tokens |
| `test_cooldown.py` | script | 1 fluxo | Notificação de cooldown com threads |
| **Total unittest** | | **9** | |

---

## 🔍 Notas

- Os testes `unittest` usam `orchestrator_hibrido_alpha0e`; os scripts de integração usam `alpha0b`. As duas versões têm interfaces compatíveis para os componentes testados, mas são arquivos distintos.
- `test_storage_worker_isolation.py` usa `time.sleep(0.5)` para dar tempo ao worker de iniciar — em ambientes lentos, pode ser necessário aumentar esse valor.
- `test_gui_smoke.py` verifica apenas a importação do módulo, sem instanciar a janela — seguro para execução em servidores sem display.

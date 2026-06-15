# 👤 Gabriel — Implementação Individual (Python · Java · Go)

Implementação individual de **Gabriel da Silva Cassino** para o Trabalho Prático
de *Teoria dos Grafos e Computabilidade* — PUC Minas, 2026/1.

Esta pasta reúne o **release final em Python** (`Aplicacao_Envio/`), uma série de
**protótipos evolutivos** (release 0 em Java/Python, release multithread em
Java/Python e um apêndice em Go), interfaces gráficas alternativas e a
documentação do trabalho.

---

## 📁 Estrutura da Pasta

```
Gabriel_Code/
├── Aplicacao_Envio/                    # Release final (Python, multithread)
│   ├── grafos/                          # Pacote da API de grafos
│   │   ├── abstract_graph.py            # AbstractGraph + GraphError
│   │   └── implementations.py           # Matriz e lista de adjacência
│   ├── graphs.py                        # Versão autocontida (legada)
│   ├── builder.py                       # Constrói múltiplos grafos a partir de interações
│   ├── analysis.py                      # Métricas de centralidade / coesão / comunidades
│   ├── lapidador_rebuild.py             # Pré-processamento dos JSONs brutos
│   ├── cypher_token_rebuild.py          # QRCodeJSONHandler aprimorado
│   ├── orchestrator_hibrido_alpha0e.py  # Orquestrador EDA com TokenManager + EventBus
│   ├── orchestrator_hibrido_alpha0f.py  # Iteração mais recente do orquestrador
│   ├── main_rebuild.py                  # Entry-point principal
│   ├── grafos_runner.py                 # Varre JSONs e monta um grafo único
│   ├── untokenize_runner.py             # Reverte tokens/IDs para nomes legíveis
│   ├── gui_ctk.py / gui_ctk1d2.py       # GUIs CustomTkinter (versões finais)
│   ├── gui_pyqt6.py / gui_pyqt6_1d2.py  # GUIs PyQt6 (versões finais)
│   ├── scripts/validacao_simulacao.py   # Script de simulação/validação
│   ├── test_cli/                        # Suite de testes (unittest + integração)
│   │   ├── run_all.py                   # Runner agregado
│   │   ├── test_event_bus.py            # EventBus — filas e isolamento
│   │   ├── test_token_manager.py        # TokenManager — cooldown e reset
│   │   ├── test_storage_worker_isolation.py
│   │   ├── test_gui_smoke.py            # Smoke test de importação da GUI
│   │   ├── test_queue_separation.py     # Integração — separação de filas
│   │   └── test_cooldown.py             # Integração — cooldown de tokens
│   ├── data.json                        # Tokens e configuração de mineração
│   ├── meu_qrcode.png                   # QR Code gerado a partir do data.json
│   ├── command.sh                       # Receita de execução
│   └── requirements.txt                 # Dependências Python
├── Interfaces_testes/                   # Iterações de GUI (ctk1a … ctk1d2, pyqt6_1a … 1d2)
├── Prototipo_0_Python/                  # Release 0 em Python (EDA básico)
├── Prototipo_0_Java/                    # Release 0 em Java
├── prototipo_multithread/
│   ├── python/                          # Multithread com rotação de tokens (Python)
│   └── java/                            # Equivalente em Java
├── apendice/prototipo_go/               # Apêndice em Go aplicando as mesmas ideias
├── teste_key/                           # Material de teste (data.json + QR de exemplo)
├── Documentacao/                        # Relatório SBC e versão completa em PDF
└── tp-es_Atualizado.pdf                 # Enunciado/atualização do TP
```

---

## 🧩 Componentes do Release Final (`Aplicacao_Envio/`)

### 1. API de Grafos — `grafos/`
- `AbstractGraph` (camelCase) com `GraphError` para erros de domínio (laços,
  aresta inexistente, índice inválido).
- Duas implementações concretas:
  - `AdjacencyMatrixGraph` — matriz `V×V`.
  - `AdjacencyListGraph` — lista/conjunto de adjacência.
- Métodos completos da especificação: `addEdge`/`removeEdge`/`hasEdge`,
  sucessores/predecessores, relações (`isDivergent`, `isConvergent`,
  `isIncident`), graus de entrada/saída, pesos de vértices e arestas,
  rótulos, `isConnected`/`isCompleteGraph`/`isEmptyGraph` e
  `exportToGEPHI`.
- `graphs.py` mantém uma versão autocontida (legada), usada por scripts
  antigos.

### 2. Builder + Análise — `builder.py` · `analysis.py`
- `builder.py` consome interações lapidadas e gera **múltiplos grafos**
  (por tipo de interação ou por janela temporal).
- `analysis.py` cobre **centralidade** (degree, closeness, betweenness,
  PageRank/Eigenvector), **coesão** (densidade, *clustering coefficient*,
  assortatividade) e **comunidades** (modularidade, *bridging ties*).

### 3. Lapidador — `lapidador_rebuild.py`
Pipeline de pré-processamento dos JSONs brutos da API GitHub:
- Normaliza usuários (`null` ignorado com segurança).
- Cria arestas ponderadas por tipo (comentário, review, fecho, merge).
- Persiste em `dados_lapidados.json`.

### 4. Cifrador de Token — `cypher_token_rebuild.py`
Versão aprimorada do `QRCodeJSONHandler`:
- Aceita `dict` **ou** caminho de arquivo `.json` no construtor.
- QR Code com alta correção de erro (`ERROR_CORRECT_H`).
- Utilitários adicionais: `write_json()` e `excluir_arquivo()`.

### 5. Orquestrador Híbrido — `orchestrator_hibrido_alpha0e.py` / `alpha0f.py`
Arquitetura **EDA** com múltiplos componentes coordenados:
- `EventBus` com **filas separadas** para dados e notificações.
- `TokenManager` controla cooldown e rotação de tokens GitHub.
- `BufferedStorageWorker` consome apenas eventos de dados, sem drenar
  notificações.
- Suporta produtores concorrentes (threads) e mantém estado consistente
  sob carga.

### 6. Interfaces Gráficas
Duas linhas mantidas em paralelo:
- **CustomTkinter** — `gui_ctk.py`, `gui_ctk1d2.py` (final) e iterações em
  `Interfaces_testes/gui_ctk*.py`.
- **PyQt6** — `gui_pyqt6.py`, `gui_pyqt6_1d2.py` (final) e iterações em
  `Interfaces_testes/gui_pyqt6_*.py`.

Cada GUI expõe o fluxo completo: mineração → lapidação → construção de
grafo → métricas → exportação para Gephi.

### 7. Suite de Testes — `test_cli/`
Mistura **unittest** e **scripts de integração**:

| Arquivo | Tipo | Foco |
|---|---|---|
| `test_event_bus.py` | unittest (4) | Isolamento de filas no `EventBus` |
| `test_token_manager.py` | unittest (3) | Cooldown e reset de tokens |
| `test_storage_worker_isolation.py` | unittest (1) | `BufferedStorageWorker` não drena notificações |
| `test_gui_smoke.py` | unittest (1) | `gui_ctk` importável sem display |
| `test_queue_separation.py` | script | Separação de filas + 2 produtores concorrentes |
| `test_cooldown.py` | script | Fluxo de notificação de cooldown com threads |
| `run_all.py` | runner | Descobre e executa todos os `unittest` em modo verboso |

---

## 🧪 Protótipos

| Pasta | Linguagem | Objetivo |
|---|---|---|
| `Prototipo_0_Python/` | Python | Release 0 — EDA básico, fundamentos do EventBus |
| `Prototipo_0_Java/` | Java | Mesmo escopo do release 0, equivalente em Java |
| `prototipo_multithread/python/` | Python | Multithread com rotação de tokens |
| `prototipo_multithread/java/` | Java | Equivalente Java do multithread |
| `apendice/prototipo_go/` | Go | Apêndice — reaplica as ideias do multithread em Go |

---

## 🚀 Como Executar (release final)

### Pré-requisitos
```bash
cd Aplicacao_Envio
pip install -r requirements.txt
```

### Configurar tokens
Edite `data.json` com seus tokens GitHub e o repositório alvo, então gere o QR Code:
```bash
python cypher_token_rebuild.py
```

### Executar a aplicação
```bash
# CLI / orquestrador
python main_rebuild.py

# GUI CustomTkinter
python gui_ctk1d2.py

# GUI PyQt6
python gui_pyqt6_1d2.py
```

### Rodar a suite de testes
```bash
python test_cli/run_all.py
```

---

## 📚 Documentação

`Documentacao/` contém o relatório completo do repositório FastAPI e a versão
no template **SBC** em PDF. `tp-es_Atualizado.pdf` traz o enunciado atualizado
do Trabalho Prático.

---

## 👤 Autor

**Gabriel da Silva Cassino** — PUC Minas, Engenharia de Computação
Disciplina: *Teoria de Grafos e Computabilidade* — Prof. Leonardo Vilela Cardoso — 2026/1

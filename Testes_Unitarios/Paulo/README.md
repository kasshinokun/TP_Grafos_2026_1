# 🧪 Testes Unitários — Paulo

Suite de testes unitários para a **API de Grafos orientada a eventos**, validando operações de grafo, algoritmos de travessia e o pipeline de mineração de dados via `EventBus`.

---

## 📁 Estrutura

```
Paulo/
└── test_suite.py    # Suite completa — 5 casos de teste via EventBus
```

---

## 🎯 O que é testado

### `test_suite.py` — API de Grafos por Eventos (`unittest`)

Todos os testes operam através da arquitetura de eventos do projeto: cada operação de grafo é disparada como um `Event` no `EventBus` da `Application`. Isso valida não apenas a lógica de grafo, mas também a integração entre os handlers e o barramento.

#### Configuração (`setUp`)

```python
self.app      = Application()
self.bus      = self.app.get_bus()
self.registry = self.app.get_registry()
```

Cada teste parte de uma instância limpa de `Application`, com `EventBus` e `GraphRegistry` frescos.

---

#### Casos de teste

| Teste | `EventType` usados | O que valida |
|---|---|---|
| `test_create_graph` | `GRAPH_CREATE` | Grafo criado, registrado com ID correto, `vertex_count == 5`, `rep_type == RepType.LIST` |
| `test_add_edge` | `GRAPH_CREATE`, `GRAPH_ADD_EDGE` | Aresta `0→1` adicionada com sucesso; `has_edge(0,1) == True`; `edge_count == 1` |
| `test_bfs` | `GRAPH_CREATE`, `GRAPH_ADD_EDGE` ×2, `ALGO_BFS` | BFS a partir do vértice `0` retorna `[0, 1, 2]` na ordem correta |
| `test_shortest_path` | `GRAPH_CREATE`, `GRAPH_ADD_EDGE` ×2, `GRAPH_SET_EDGE_WEIGHT` ×2, `ALGO_SHORTEST_PATH` | Caminho mínimo `0→2` é `[0, 1, 2]` com distância total `15.0` (pesos: 10+5) |
| `test_csv_load_and_build` | `MINING_LOAD_CSV`, `MINING_BUILD_INTEGRATED_GRAPH` | CSV com 3 usuários é carregado; grafo integrado construído com 3 vértices e pesos corretos por tipo de interação (`COMMENT_ON_ISSUE_OR_PR=2.0`, `PR_MERGE=5.0`) |

---

#### Detalhes do `test_csv_load_and_build`

O teste cria um arquivo CSV temporário em disco, dispara o pipeline de mineração via eventos e verifica o grafo gerado:

```
actor,target,type
alice,bob,COMMENT_ON_ISSUE_OR_PR
bob,charlie,PR_MERGE
```

**Verificações:**
- O grafo `"graph_integrated"` foi criado no registry.
- `vertex_count == 3` (alice, bob, charlie mapeados para índices 0, 1, 2).
- `get_edge_weight(0, 1) == 2.0` (comentário em issue/PR).
- `get_edge_weight(1, 2) == 5.0` (merge de PR).
- O arquivo CSV temporário é removido após o teste.

---

## 🔧 Dependências

O `test_suite.py` importa de `grafo` (pacote do projeto do Paulo), que deve estar acessível no `sys.path`:

```
Paulo/
├── grafo/                          ← pacote que deve existir
│   ├── core/
│   │   └── application.py         ← Application, get_bus(), get_registry()
│   ├── events/
│   │   ├── event.py               ← Event, with_payload()
│   │   └── event_type.py          ← EventType (enum)
│   └── graph/
│       └── abstract_graph.py      ← RepType (enum)
└── test_suite.py                   ← esta suite
```

**Sem dependências externas** — apenas biblioteca padrão do Python 3.10+.

> ⚠️ **Nota:** o pacote importado é `grafo` (com "a"), porém os módulos de API na pasta `Paulo/graph/` seguem a convenção `graph` (sem "a"). Verificar se existe um pacote `grafo/` separado com a camada de aplicação (`Application`, `EventBus`, `EventType`) ou se é necessário ajustar os imports antes de executar.

---

## ▶️ Como Executar

**A partir da pasta `Paulo/`** (com o pacote `grafo` disponível no path):

```bash
python -m unittest test_suite -v
```

**Diretamente:**

```bash
python test_suite.py
```

**Saída esperada (modo verboso):**

```
test_add_edge (__main__.TestGrafo) ... ok
test_bfs (__main__.TestGrafo) ... ok
test_create_graph (__main__.TestGrafo) ... ok
test_csv_load_and_build (__main__.TestGrafo) ... ok
test_shortest_path (__main__.TestGrafo) ... ok
----------------------------------------------------------------------
Ran 5 tests in X.XXXs
OK
```

---

## 📊 Resumo da Cobertura

| Arquivo | Classe de Teste | Casos de Teste | Componentes Testados |
|---|---|---|---|
| `test_suite.py` | `TestGrafo` | 5 | `GRAPH_CREATE`, `GRAPH_ADD_EDGE`, `ALGO_BFS`, `ALGO_SHORTEST_PATH`, `MINING_LOAD_CSV`, `MINING_BUILD_INTEGRATED_GRAPH` |

---

## 🔍 Notas

- A abordagem orientada a eventos significa que os testes validam a **integração end-to-end** entre os eventos, os handlers e a estrutura de grafo — indo além do teste unitário puro.
- O campo `ev.success` é verificado após operações de mutação (`GRAPH_CREATE`, `GRAPH_ADD_EDGE`), garantindo que o handler processou o evento sem erros.
- O campo `ev.result` carrega a resposta dos algoritmos (`ALGO_BFS` retorna lista de vértices; `ALGO_SHORTEST_PATH` retorna dicionário `{"path": [...], "dist": float}`).
- O teste de CSV usa `open()` com escrita direta no diretório de trabalho; certifique-se de ter permissão de escrita no diretório onde o teste é executado.

# Gabriel — API de Grafos

Módulo Python para modelagem, construção e exportação de grafos dirigidos, com foco em representar **redes de interação entre usuários** (ex: comentários, reviews, fechamentos de issues e merges de pull requests em repositórios GitHub).

## Estrutura do projeto

```
Gabriel/
├── grafos/
│   ├── __init__.py          # Exporta as classes públicas do pacote
│   ├── abstract_graph.py     # Classe base abstrata (AbstractGraph) e GraphError
│   └── implementations.py    # Implementações concretas (matriz e lista de adjacência)
├── graphs.py                 # Versão alternativa/legada do grafo (autocontida)
├── builder.py                 # Construção de múltiplos grafos a partir de interações
├── lapidador_rebuild.py       # Pipeline de pré-processamento dos dados brutos (JSON)
└── grafos_runner.py            # Script utilitário para varrer JSONs e montar um grafo
```

## Módulo `grafos`

### `AbstractGraph` (abstract_graph.py)

Classe abstrata que define a interface e o comportamento comum a qualquer grafo:

- **Vértices**: contagem, rótulos (`get/setVertexLabel`) e pesos (`get/setVertexWeight`).
- **Arestas**: contagem, peso (`get/setEdgeWeight`), validação de índices.
- **Relações topológicas**:
  - `isSucessor(u, v)` / `isPredessor(u, v)` — testa adjacência direta.
  - `isDivergent(u1, v1, u2, v2)` — arestas com mesma origem e destinos diferentes.
  - `isConvergent(u1, v1, u2, v2)` — arestas com destinos iguais e origens diferentes.
  - `isIncident(u, v, x)` — verifica se o vértice `x` participa da aresta `(u, v)`.
- **Graus**: `getVertexInDegree` / `getVertexOutDegree`, calculados a partir de `predecessors`/`successors`.
- **Propriedades do grafo**:
  - `isConnected()` — verifica conectividade (busca em profundidade tratando o grafo como não dirigido).
  - `isEmptyGraph()` / `isCompleteGraph()`.
- **Exportação**: `exportToGEPHI(path)` — gera um arquivo `.gexf` (formato do Gephi) com nós e arestas.

Métodos abstratos que cada implementação concreta deve fornecer: `hasEdge`, `addEdge`, `removeEdge`, `successors`, `predecessors`.

Erros de domínio (ex: aresta inexistente, número de vértices negativo) são sinalizados via `GraphError`.

### Implementações (implementations.py)

| Classe | Estrutura interna | Características |
|---|---|---|
| `AdjacencyMatrixGraph` | Matriz `n x n` de booleanos | Consulta de aresta em O(1); não permite laços (`u == v`) |
| `AdjacencyListGraph` | Lista de `set()` por vértice | Mais eficiente para grafos esparsos; `successors` retorna lista ordenada |

Ambas herdam toda a lógica de `AbstractGraph` e implementam apenas a manipulação de arestas (`hasEdge`, `addEdge`, `removeEdge`) e a obtenção de vizinhos (`successors`, `predecessors`).

## `graphs.py`

Versão alternativa e autocontida (não depende do pacote `grafos`), com a mesma API conceitual (`AbstractGraph`, `AdjacencyMatrixGraph`, `AdjacencyListGraph`), porém:

- Arestas e pesos são armazenados juntos (peso `0.0` = ausência de aresta; peso `> 0` = presença).
- Inclui funções auxiliares (`get_absoluto`, `get_diretory`) para resolver caminhos relativos ao diretório do módulo.
- `exportToGEPHI` grava o arquivo em `app_dir/path` usando o formato GEXF 1.2.

> Observação: este arquivo parece ser uma versão anterior/paralela das classes do pacote `grafos/`. Ao integrar o projeto, recomenda-se padronizar em uma única implementação.

## `builder.py` — Construção de grafos a partir de interações

```python
from builder import build_graphs

graphs, user_index = build_graphs(interactions)
```

- Recebe uma lista de interações no formato `{"source": ..., "target": ..., "type": ...}`.
- Mapeia cada usuário para um índice inteiro (`user_index`).
- Cria múltiplos grafos (`AdjacencyListGraph`), um para cada categoria:
  - `comments` — tipos `comment`, `issue_response`
  - `issues` — tipo `issue_close`
  - `pull_requests` — tipos `review`, `merge`
  - `integrated` — todas as interações combinadas, com peso acumulado por aresta
- Pesos das interações (`INTERACTION_WEIGHTS`):

  | Tipo | Peso |
  |---|---|
  | comment | 2.0 |
  | issue_response | 3.0 |
  | issue_close | 4.0 |
  | review | 4.0 |
  | merge | 5.0 |

- Laços (`source == target`) e tipos desconhecidos são ignorados.
- No grafo `integrated`, o peso de cada aresta é a soma dos pesos de todas as interações entre o mesmo par de usuários.

## `lapidador_rebuild.py` — Pipeline de pré-processamento

Classe `Lapidador`: transforma dados brutos minerados da API do GitHub (arquivos JSON em `./json/`) em uma lista normalizada de interações (`dados_lapidados.json`), pronta para alimentar o `builder.py`.

Fluxo principal (`lapidar()`):

1. **Construção de mapas de autoria** (corrige limitações da API do GitHub):
   - `_build_issue_author_map()` — mapeia `issue_url -> autor` a partir de `closed_issues_part_*.json`.
   - `_build_pr_author_map()` — mapeia `pr_url -> autor` a partir de `pr_reviews_merges_part_*.json` (campos enriquecidos `_pr_url`/`_pr_author`).
2. **Processamento dos arquivos brutos**:
   - `process_issue_comments` → interação `comentador → autor da issue` (tipo `comment`).
   - `process_pr_comments` → interação `comentador → autor do PR` (tipo `comment`).
   - `process_closed_issues` → interação `quem fechou → autor da issue` (tipo `issue_close`).
   - `process_pr_reviews` → interação `revisor → autor do PR` (tipo `review`).
3. **Saída**: grava `dados_lapidados.json` em `work/` contendo:
   ```json
   {
     "metadata": {"total_users": N, "total_interactions": M},
     "users": {"login": id, ...},
     "interactions": [{"source": "...", "target": "...", "type": "..."}, ...]
   }
   ```

Interações com `source == target` ou sem usuário identificado são descartadas. Registros que não puderem ser associados a um autor (ex: issues abertas, PRs não mesclados) são contabilizados como "ignorados" via log.

Uso:
```python
from lapidador_rebuild import Lapidador

lap = Lapidador.initialize_work()  # usa diretório "work"
caminho = lap.lapidar()
```

## `grafos_runner.py` — Utilitário de varredura

Script independente que varre um diretório de arquivos `.json` e monta um `AdjacencyListGraph` a partir de pares de campos comuns (`user/target`, `author/repo`, `from/to`, `source/target`, `login/repo_full_name`).

- Tolerante a falhas: se o módulo `v1d.grafos` não estiver disponível ou o diretório não existir, retorna um sumário vazio com aviso, sem lançar exceção.
- Retorna um dicionário resumo: `{"files": N, "vertices": V, "edges": E}`.
- Execução via linha de comando:
  ```bash
  python grafos_runner.py ./json
  ```

> Observação: este script importa de `v1d.grafos`, enquanto o restante do projeto usa `grafos`/`graphs`. Verificar se há um pacote `v1d` esperado ou se é necessário ajustar o import.

## Exemplo de uso geral

```python
from grafos import AdjacencyListGraph

g = AdjacencyListGraph(4)
g.setVertexLabel(0, "alice")
g.setVertexLabel(1, "bob")

g.addEdge(0, 1)
g.setEdgeWeight(0, 1, 3.0)

print(g.hasEdge(0, 1))          # True
print(g.getVertexOutDegree(0))  # 1
print(g.isConnected())          # False (vértices 2 e 3 isolados)

g.exportToGEPHI("saida/grafo.gexf")
```

## Requisitos

- Python 3.10+ (uso de `dict[str, int]`, `tuple[int, int]`, `from __future__ import annotations`).
- Sem dependências externas — apenas biblioteca padrão (`os`, `json`, `glob`, `logging`, `pathlib`, `collections`, `abc`).

## Possíveis pontos de atenção

- **Duplicação de lógica**: `graphs.py` e `grafos/` implementam conceitos muito semelhantes com pequenas diferenças de API (ex: pesos armazenados na própria matriz vs. dicionário separado). Considerar unificar.
- **Import inconsistente** em `grafos_runner.py` (`v1d.grafos` vs `grafos`).
- **Laços não permitidos**: `addEdge(u, u)` lança erro em ambas implementações de `grafos/implementations.py`.
- **Pesos de aresta**: em `grafos/`, `getEdgeWeight` retorna `1.0` por padrão se nenhum peso explícito foi definido; em `graphs.py`, retorna `0.0`.

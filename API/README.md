# API de Grafos — Visão Geral do Projeto

Este repositório reúne **três implementações independentes** de uma API de grafos dirigidos ponderados, desenvolvidas por diferentes integrantes da equipe (Daniel, Gabriel e Paulo) a partir de um mesmo conjunto de requisitos: representar grafos, oferecer operações topológicas básicas, suportar pesos em vértices/arestas, exportar para o Gephi (GEXF) e processar dados minerados do GitHub ("Lapidador") para construir redes de interação entre usuários.

Cada subpasta possui seu próprio `README.md` com detalhes específicos. Este documento serve como **índice geral** e **comparativo** entre as três abordagens.

```
.
├── Daniel/
│   ├── graph_engine/
│   │   ├── abstract_graph.py
│   │   ├── implementations.py
│   │   ├── analysis.py
│   │   └── lapidador.py
│   └── README.md
├── Gabriel/
│   ├── grafos/
│   │   ├── abstract_graph.py
│   │   ├── implementations.py
│   │   └── __init__.py
│   ├── graphs.py
│   ├── builder.py
│   ├── grafos_runner.py
│   ├── lapidador_rebuild.py
│   └── README.md
└── Paulo/
    ├── graph/
    │   ├── abstract_graph.py
    │   ├── adjacency_list_graph.py
    │   └── adjacency_matrix_graph.py
    └── README.md
```

## Conceito comum

Todas as implementações modelam um **grafo dirigido simples** (sem laços) com:

- Número fixo de vértices definido na criação.
- Rótulos e pesos por vértice.
- Pesos por aresta.
- Duas estruturas de representação intercambiáveis: **matriz de adjacência** e **lista de adjacência**.
- Operações topológicas: sucessores/predecessores, grau de entrada/saída, divergência, convergência, incidência.
- Propriedades globais: conectividade, grafo vazio, grafo completo.
- Exportação para o formato **GEXF** (Gephi).
- Um módulo "Lapidador" que transforma dados brutos de issues/PRs do GitHub em interações para montar o grafo.

## Comparativo entre implementações

| Aspecto | Daniel (`graph_engine`) | Gabriel (`grafos` / `graphs.py`) | Paulo (`graph`) |
|---|---|---|---|
| Convenção de nomes | `camelCase` (`getVertexCount`, `addEdge`) | `camelCase` (igual ao Daniel) | `snake_case` (`get_vertex_count`, `add_edge`) |
| Classe de erro | `GraphError` (subclasse de `ValueError`) | `GraphError` (subclasse de `ValueError`) — apenas no pacote `grafos/`; `graphs.py` usa `ValueError`/`IndexError` puros | `ValueError`/`IndexError` padrão (sem classe própria) |
| Validação `num_vertices` | `>= 0` (zero permitido) | `>= 0` (zero permitido) | `> 0` (obrigatório, zero não permitido) |
| Representação por lista | `list[set[int]]` (sem peso embutido; peso fica em `_edge_weights`) | `list[set[int]]` (`grafos/`) ou `list[dict[int, float]]` (`graphs.py`) | `list[dict[int, float]]` (peso embutido na própria estrutura) |
| Representação por matriz | Matriz `V×V` de booleanos + dicionário de pesos | Matriz `V×V` de booleanos (`grafos/`) ou de floats (`graphs.py`) | Matriz `V×V` de floats (`0.0` = sem aresta) |
| Peso padrão de aresta | `1.0` se não definido | `1.0` (`grafos/`) / `0.0` (`graphs.py`) | `0.0` representa ausência; não há "peso padrão" para aresta existente sem peso definido |
| Seletor de representação | Duas classes distintas (`AdjacencyMatrixGraph`, `AdjacencyListGraph`) | Duas classes distintas, duplicadas em dois módulos (`grafos/` e `graphs.py`) | Duas classes distintas + enum `RepType` (`MATRIX`/`LIST`) para indicar o tipo |
| Módulo de análise/métricas | **`analysis.py`** — centralidade (grau, proximidade, intermediação), PageRank, densidade, clustering, assortatividade, comunidades, "bridging ties" | Não possui módulo de análise dedicado | Não possui módulo de análise dedicado |
| Exportação Gephi | GEXF, cria diretórios automaticamente | GEXF 1.3 (`grafos/abstract_graph.py`) ou GEXF 1.2 (`graphs.py`) | GEXF 1.3, implementado em cada classe concreta |
| Pipeline de dados GitHub | `Lapidador` — processa `closed_issues`, peso fixo 3 por fechamento de issue | `Lapidador` (`lapidador_rebuild.py`) — processa comentários de issue/PR, fechamentos e reviews, com pesos diferenciados por tipo (`builder.py`) | Não possui pipeline de dados (apenas a API de grafo) |
| Dependências | Apenas biblioteca padrão | Apenas biblioteca padrão | Apenas biblioteca padrão |
| Python mínimo | 3.10+ | 3.10+ | 3.10+ |

## Pipeline "Lapidador" — comparação

Os Lapidadores de Daniel e Gabriel resolvem o mesmo problema (transformar dados brutos do GitHub em uma lista de interações entre usuários), mas com escopos diferentes:

- **Daniel**: foco apenas em **fechamento de issues** (`closed_by → user`, peso fixo `3`), produzindo `dados_lapidados.json` com `interactions: [{from, to, weight}]`.
- **Gabriel**: cobre **quatro tipos de interação** — comentários em issues, comentários em PRs, fechamento de issues e reviews de PR — reconstruindo a autoria via mapas auxiliares (`issue_author_map`, `pr_author_map`) para contornar limitações da API do GitHub. Produz `dados_lapidados.json` com `interactions: [{source, target, type}]`, que depois é consumido por `builder.py` para gerar múltiplos grafos por categoria (comentários, issues, pull requests, integrado) com pesos diferenciados por tipo de interação.

Paulo não implementou um pipeline de dados; sua API é focada exclusivamente na estrutura e operações de grafo.

## Pontos de atenção para integração

1. **Convenção de nomenclatura divergente**: Daniel e Gabriel usam `camelCase`; Paulo usa `snake_case`. Qualquer integração entre os módulos exigirá um adaptador ou padronização.
2. **Tratamento de pesos diferente**: em algumas implementações `0.0` significa "sem aresta" (Paulo, `graphs.py` do Gabriel), enquanto em outras a ausência de aresta é controlada por uma estrutura separada da matriz/lista (Daniel, `grafos/` do Gabriel). Isso afeta a interpretação de `getEdgeWeight`/`get_edge_weight` quando a aresta não tem peso explícito.
3. **Duplicação interna no projeto do Gabriel**: existem duas implementações paralelas (`grafos/` e `graphs.py`) com pequenas diferenças de comportamento — recomenda-se escolher uma única versão.
4. **Formatos de saída do Lapidador são incompatíveis entre si**: Daniel usa `{from, to, weight}`, Gabriel usa `{source, target, type}`. Para unificar os pipelines de dados seria necessário um esquema comum.
5. **Validação de `num_vertices = 0`**: aceita por Daniel e Gabriel, rejeitada por Paulo (`ValueError`).
6. **Módulo de análise (`analysis.py`)** existe apenas na implementação do Daniel; caso o projeto final precise de métricas de rede (PageRank, centralidade, comunidades), esse módulo é o ponto de partida natural, mas precisa ser adaptado para operar sobre a implementação de grafo escolhida.

## Requisitos gerais

- Python 3.10 ou superior.
- Nenhuma dependência externa (apenas biblioteca padrão: `os`, `json`, `glob`, `logging`, `collections`, `math`, `pathlib`, `abc`, `enum`).
- Para visualização dos grafos exportados, recomenda-se o [Gephi](https://gephi.org/) (formato `.gexf`).

## Próximos passos sugeridos

- Definir qual implementação (ou combinação) será a base oficial da API.
- Padronizar convenção de nomes (`camelCase` vs `snake_case`) e tratamento de peso de aresta padrão.
- Unificar o formato de saída do Lapidador para alimentar tanto análises (Daniel) quanto a construção de grafos por categoria (Gabriel).
- Portar/adaptar o módulo `analysis.py` (Daniel) para a implementação escolhida, caso métricas de rede sejam necessárias no produto final.

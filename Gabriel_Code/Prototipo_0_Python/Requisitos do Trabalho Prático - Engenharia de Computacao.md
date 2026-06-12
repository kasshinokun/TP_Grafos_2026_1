# Requisitos do Trabalho Prático - Engenharia de Computação

## Objetivo
Desenvolver uma ferramenta computacional que processe dados estruturados como grafos, aplicando conceitos da teoria dos grafos e boas práticas de engenharia de computação.

## Etapas do Trabalho
### Etapa 1: Modelagem e Planejamento
- Escolha de um repositório público no GitHub (> 5.000 estrelas).
- Extração de dados: comentários em issues/PRs, fechamento de issues, abertura/revisão/merge de PRs.
- Modelagem do Grafo: Usuário = Nó, Interação = Aresta (simples e direcionado).
- Pesos sugeridos:
  - Comentário: 2
  - Abertura de issue comentada: 3
  - Revisão/aprovação de PR: 4
  - Merge de PR: 5

### Etapa 2: Desenvolvimento da Ferramenta
- Estrutura de classes:
  - `AbstractGraph` (Abstrata)
  - `AdjacencyMatrixGraph` (Concreta)
  - `AdjacencyListGraph` (Concreta)
- API Obrigatória: `getVertexCount`, `getEdgeCount`, `hasEdge`, `addEdge`, `removeEdge`, `isSucessor`, `isPredessor`, `isDivergent`, `isConvergent`, `isIncident`, `getVertexInDegree`, `getVertexOutDegree`, `setVertexWeight`, `getVertexWeight`, `setEdgeWeight`, `getEdgeWeight`, `isConnected`, `isEmptyGraph`, `isCompleteGraph`.
- Adicional: `exportToGEPHI`.

### Etapa 3: Análise baseada em dados
- Métricas de Centralidade: Grau, Intermediação, Proximidade, PageRank.
- Métricas de Estrutura: Densidade, Coeficiente de Aglomeração, Assortatividade.
- Métricas de Comunidade: Detecção de comunidades, Bridging ties.

## Alunos do Grupo
- Gabriel da Silva Cassino


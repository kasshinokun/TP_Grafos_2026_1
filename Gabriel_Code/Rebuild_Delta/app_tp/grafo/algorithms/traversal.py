"""Algoritmos clássicos de travessia (BFS e DFS) para grafos direcionados.

Implementação nativa, sem dependências externas de grafos (proibidas
pelo PDF do TP — ver Etapa 2, "Restrições").

Ambos algoritmos operam sobre qualquer subclasse de AbstractGraph
(AdjacencyMatrixGraph, AdjacencyListGraph, UndirectedGraph) através dos
métodos auxiliares de duck-typing já usados pelo GraphAdapter:
`get_successors(u)` (sucessores via arestas u->v).

Os algoritmos respeitam a direção das arestas: a partir de um vértice
`source`, só é possível alcançar vértices para os quais existe um
caminho direcionado (u1->u2->...->v). Vértices alcançáveis apenas
"de trás para frente" (via predecessores) não entram no resultado —
esse é o comportamento esperado de BFS/DFS em grafos direcionados.
"""
from collections import deque
from typing import Dict, List, Optional


class TraversalResult:
    """Resultado de uma travessia (BFS ou DFS) a partir de um vértice de
    origem.

    Atributos:
        order: lista de vértices na ordem em que foram visitados.
        predecessor: dict {vertice: predecessor_na_arvore_de_busca}.
                     O vértice de origem tem predecessor None.
        visited: conjunto (set) de todos os vértices alcançados.
    """

    def __init__(self, order: List[int], predecessor: Dict[int, Optional[int]]):
        self.order = order
        self.predecessor = predecessor
        self.visited = set(order)

    def path_to(self, target: int) -> Optional[List[int]]:
        """Reconstrói o caminho da origem até `target` percorrendo o
        dicionário de predecessores. Retorna None se `target` não foi
        alcançado nesta travessia."""
        if target not in self.visited:
            return None
        path = [target]
        node = target
        while self.predecessor.get(node) is not None:
            node = self.predecessor[node]
            path.append(node)
        path.reverse()
        return path

    def __repr__(self):
        return f"TraversalResult(order={self.order})"


def _successors_of(graph, u: int):
    """Obtém os sucessores de `u` (vértices v tais que existe aresta
    u->v) usando o método de duck-typing já adotado pelo projeto
    (get_successors), com fallback via has_edge para qualquer
    implementação de AbstractGraph que não o tenha definido."""
    if hasattr(graph, "get_successors"):
        return graph.get_successors(u)
    # Fallback genérico (funciona para qualquer AbstractGraph, só mais
    # lento: O(V) por vértice em vez de O(grau)).
    return {v for v in range(graph.get_vertex_count())
            if v != u and graph.has_edge(u, v)}


def bfs(graph, source: int) -> TraversalResult:
    """Busca em largura (Breadth-First Search) a partir de `source`,
    respeitando a direção das arestas (só desce por u->v).

    Complexidade: O(V + E) no pior caso.

    Levanta IndexError se `source` estiver fora dos limites do grafo
    (via graph.check_vertex, chamado indiretamente por get_successors).
    """
    graph.check_vertex(source)

    order: List[int] = []
    predecessor: Dict[int, Optional[int]] = {source: None}
    visited = {source}
    queue = deque([source])

    while queue:
        u = queue.popleft()
        order.append(u)
        # sorted() garante uma ordem determinística de visita entre
        # vizinhos (útil para testes e para reprodutibilidade na GUI).
        for v in sorted(_successors_of(graph, u)):
            if v not in visited:
                visited.add(v)
                predecessor[v] = u
                queue.append(v)

    return TraversalResult(order, predecessor)


def dfs(graph, source: int) -> TraversalResult:
    """Busca em profundidade (Depth-First Search) a partir de `source`,
    respeitando a direção das arestas (só desce por u->v).

    Implementação iterativa (pilha explícita) para evitar limite de
    recursão do Python em grafos grandes (ex.: redes de colaboração
    reais minadas do GitHub, que podem ter milhares de nós).

    Complexidade: O(V + E) no pior caso.
    """
    graph.check_vertex(source)

    order: List[int] = []
    predecessor: Dict[int, Optional[int]] = {source: None}
    visited = {source}
    stack = [source]

    while stack:
        u = stack.pop()
        order.append(u)
        # Os sucessores são empilhados em ordem reversa para que, ao
        # desempilhar (LIFO), sejam visitados em ordem crescente —
        # mantém a travessia determinística, igual ao BFS acima.
        for v in sorted(_successors_of(graph, u), reverse=True):
            if v not in visited:
                visited.add(v)
                predecessor[v] = u
                stack.append(v)

    return TraversalResult(order, predecessor)


def dfs_forest(graph) -> List[TraversalResult]:
    """Executa DFS a partir de todo vértice ainda não visitado, na
    ordem 0, 1, 2, ..., formando a "floresta" de busca em profundidade
    que cobre o grafo inteiro (necessário quando o grafo não é
    fortemente conexo a partir de um único vértice — ex.: para depois
    alimentar algoritmos de SCC como Kosaraju/Tarjan).

    Retorna uma lista de TraversalResult, uma por árvore/componente.
    """
    visited_global = set()
    forest: List[TraversalResult] = []

    for start in range(graph.get_vertex_count()):
        if start in visited_global:
            continue
        result = dfs(graph, start)
        visited_global |= result.visited
        forest.append(result)

    return forest

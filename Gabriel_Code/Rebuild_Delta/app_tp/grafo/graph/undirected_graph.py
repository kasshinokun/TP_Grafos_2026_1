# ./grafo/graph/undirected_graph.py

"""Grafo não direcionado (UndirectedGraph).

Implementação nativa (sem bibliotecas de grafos prontas), em
conformidade com a restrição do PDF do TP (Etapa 2).

UndirectedGraph é autônoma: pode ser criada e usada por conta própria,
exatamente como AdjacencyMatrixGraph/AdjacencyListGraph, respeitando a
mesma API obrigatória definida em AbstractGraph (com a particularidade
de que, num grafo não direcionado, has_edge(u, v) == has_edge(v, u),
e cada aresta {u, v} é armazenada e contada uma única vez).

Além disso, ela oferece uma ponte de compatibilidade com grafos
DIRECIONADOS (AdjacencyMatrixGraph / AdjacencyListGraph), pensada para
algoritmos que precisam de uma visão não-direcionada temporária de um
grafo direcionado já existente — por exemplo Kruskal e Prim, que
operam sobre arestas não-direcionadas mesmo quando o grafo de entrada
modela relações direcionadas (ex.: "revisou PR de", "comentou em"):

    g_dirigido = AdjacencyListGraph(5)
    ... (popula g_dirigido) ...

    ug = UndirectedGraph(g_dirigido.get_vertex_count())
    ug.get_subjacente(g_dirigido)   # congela arestas+pesos de g_dirigido
                                     # e monta a versão não-direcionada
    # ... roda Kruskal/Prim sobre ug ...
    g_restaurado = ug.from_subjacente()  # devolve o grafo direcionado
                                          # original e ESVAZIA o cache

Regra de fusão de pesos (definida pela equipe): quando o grafo
direcionado original tem arestas opostas u->v e v->u com pesos w1 e
w2 (possivelmente diferentes), a aresta não-direcionada única {u, v}
recebe peso (w1 + w2) / 2.
"""
from typing import Dict, Optional, Set, Tuple, Type

from .abstract_graph import AbstractGraph, RepType


class UndirectedGraph(AbstractGraph):
    """Grafo simples não direcionado, implementado com listas de
    adjacência simétricas (cada aresta {u, v} é refletida em
    self.adj[u][v] e self.adj[v][u] com o mesmo peso, mas contada uma
    única vez em get_edge_count())."""

    def __init__(self, num_vertices: int):
        super().__init__(num_vertices, RepType.LIST)
        self.adj: list = [dict() for _ in range(num_vertices)]
        self.edge_count_val = 0

        # Cache do grafo direcionado "subjacente" original, preenchido
        # por get_subjacente() e consumido (e esvaziado) por
        # from_subjacente(). Guarda os pesos ORIGINAIS de cada aresta
        # direcionada, não a média usada na versão não-direcionada —
        # é isso que permite reconstruir o grafo direcionado sem
        # perda de informação.
        # Formato: {(u, v): peso_original_de_u_para_v, ...}
        self._subjacente_arestas: Dict[Tuple[int, int], float] = {}
        self._subjacente_cls: Optional[Type[AbstractGraph]] = None
        self._subjacente_num_vertices: Optional[int] = None
        self._subjacente_vertex_weights: Optional[list] = None
        self._subjacente_vertex_labels: Optional[dict] = None

    # ------------------------------------------------------------------
    # API obrigatória (AbstractGraph)
    # ------------------------------------------------------------------

    def get_vertex_count(self) -> int:
        return self.num_vertices

    def get_edge_count(self) -> int:
        return self.edge_count_val

    def has_edge(self, u: int, v: int) -> bool:
        self.check_edge(u, v)
        return v in self.adj[u]  # simétrico: v in adj[u] <=> u in adj[v]

    def add_edge(self, u: int, v: int):  # Idempotente
        self.check_edge(u, v)
        if v not in self.adj[u]:
            self.adj[u][v] = 1.0
            self.adj[v][u] = 1.0
            self.edge_count_val += 1

    def remove_edge(self, u: int, v: int):
        self.check_edge(u, v)
        if v in self.adj[u]:
            del self.adj[u][v]
            del self.adj[v][u]
            self.edge_count_val -= 1

    def get_vertex_in_degree(self, u: int) -> int:
        # Em grafo não direcionado, grau de entrada == grau de saída
        # == grau (número de vizinhos).
        self.check_vertex(u)
        return len(self.adj[u])

    def get_vertex_out_degree(self, u: int) -> int:
        self.check_vertex(u)
        return len(self.adj[u])

    def set_edge_weight(self, u: int, v: int, w: float):
        self.check_edge(u, v)
        if w == 0:
            raise ValueError("Peso 0 reservado para 'sem aresta'.")
        is_new = v not in self.adj[u]
        self.adj[u][v] = w
        self.adj[v][u] = w  # mantém a simetria do peso
        if is_new:
            self.edge_count_val += 1

    def get_edge_weight(self, u: int, v: int) -> float:
        self.check_edge(u, v)
        if v not in self.adj[u]:
            raise ValueError(f"Aresta ({u},{v}) não existe.")
        return self.adj[u][v]

    def is_connected(self) -> bool:
        """Em grafo não direcionado, conectividade fraca == forte."""
        if self.num_vertices == 0:
            return True
        visited = {0}
        queue = [0]
        while queue:
            curr = queue.pop(0)
            for nb in self.adj[curr]:
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        return len(visited) == self.num_vertices

    # is_empty_graph / is_complete_graph: a fórmula padrão de
    # AbstractGraph (n*(n-1)) presume grafo direcionado (cada par
    # ordenado é uma aresta possível). Em grafo não-direcionado o
    # número máximo de arestas é n*(n-1)/2 — por isso sobrescrevemos
    # is_complete_graph aqui (is_empty_graph não depende disso).
    def is_complete_graph(self) -> bool:
        max_edges = self.num_vertices * (self.num_vertices - 1) // 2
        return self.get_edge_count() == max_edges

    # --- Duck-typing para o GraphAdapter (grafo/networkx_pure) ---
    # Em um grafo não direcionado, sucessores e predecessores de um
    # vértice são exatamente o mesmo conjunto: seus vizinhos.
    def get_successors(self, u: int) -> Set[int]:
        self.check_vertex(u)
        return set(self.adj[u].keys())

    def get_predecessors(self, u: int) -> Set[int]:
        self.check_vertex(u)
        return set(self.adj[u].keys())

    def export_to_gephi(self, path: str):
        file_path = path if path.endswith(".gexf") else path + ".gexf"

        def escape_xml(text):
            text = str(text)
            return (text.replace("&", "&amp;").replace("<", "&lt;")
                        .replace(">", "&gt;").replace('"', "&quot;")
                        .replace("'", "&apos;"))

        with open(file_path, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<gexf xmlns="http://gexf.net/1.3" version="1.3">\n')
            # defaultedgetype="undirected": diferente das implementações
            # direcionadas (AdjacencyMatrixGraph/AdjacencyListGraph, que
            # usam "directed") — GEPHI usa este atributo para decidir
            # como desenhar e calcular métricas sobre o grafo importado.
            f.write('  <graph defaultedgetype="undirected">\n')
            f.write('    <nodes>\n')
            for i in range(self.num_vertices):
                f.write(f'      <node id="{i}" label="{escape_xml(self.vertex_labels[i])}"/>\n')
            f.write('    </nodes>\n')
            f.write('    <edges>\n')
            eid = 0
            seen: Set[Tuple[int, int]] = set()
            for u in range(self.num_vertices):
                for v, w in self.adj[u].items():
                    # Cada aresta não-direcionada {u, v} está duplicada
                    # em self.adj (uma vez como adj[u][v], outra como
                    # adj[v][u]) — escreve só uma vez no GEXF.
                    key = (min(u, v), max(u, v))
                    if key in seen:
                        continue
                    seen.add(key)
                    f.write(f'      <edge id="{eid}" source="{u}" target="{v}" weight="{w:.4f}"/>\n')
                    eid += 1
            f.write('    </edges>\n')
            f.write('  </graph>\n')
            f.write('</gexf>\n')

    # ------------------------------------------------------------------
    # Ponte de compatibilidade com grafos direcionados
    # (uso por algoritmos como Kruskal e Prim)
    # ------------------------------------------------------------------

    def get_subjacente(self, grafo_direcionado: AbstractGraph) -> None:
        """Congela as arestas e pesos ORIGINAIS de `grafo_direcionado`
        neste objeto (em self._subjacente_arestas) e reconstrói este
        UndirectedGraph como o "grafo subjacente" não-direcionado
        correspondente: para cada par (u, v) com aresta em pelo menos
        um sentido no grafo direcionado, cria uma única aresta {u, v}.

        Se existirem as duas arestas opostas u->v e v->u (com pesos
        w1 e w2, possivelmente diferentes), o peso da aresta
        não-direcionada {u, v} é a média (w1 + w2) / 2 — regra
        definida pela equipe para não favorecer arbitrariamente um
        dos dois sentidos.

        Este método também redimensiona este UndirectedGraph para
        ter o mesmo número de vértices (e os mesmos rótulos/pesos de
        vértice) do grafo direcionado de origem, e LIMPA qualquer
        aresta não-direcionada que já existisse aqui antes da chamada
        (o estado anterior de self.adj é descartado).
        """
        n = grafo_direcionado.get_vertex_count()

        # Reinicializa este grafo para o tamanho do grafo direcionado.
        self.num_vertices = n
        self.adj = [dict() for _ in range(n)]
        self.edge_count_val = 0
        self.vertex_weights = list(grafo_direcionado.vertex_weights)
        self.vertex_labels = dict(grafo_direcionado.vertex_labels)

        # 1) Congela as arestas + pesos ORIGINAIS do grafo direcionado,
        #    um valor por par ordenado (u, v) com aresta. Isso é o que
        #    permite reconstruir o grafo exatamente depois.
        originais: Dict[Tuple[int, int], float] = {}
        for u in range(n):
            for v in grafo_direcionado.get_successors(u):
                originais[(u, v)] = grafo_direcionado.get_edge_weight(u, v)

        # 2) Monta a versão não-direcionada: para cada par não-ordenado
        #    {u, v} que tenha pelo menos uma aresta original em algum
        #    sentido, cria a aresta única com o peso combinado.
        processados: Set[Tuple[int, int]] = set()
        for (u, v), w_uv in originais.items():
            key = (min(u, v), max(u, v))
            if key in processados:
                continue
            processados.add(key)

            w_vu = originais.get((v, u))
            if w_vu is not None:
                peso_final = (w_uv + w_vu) / 2.0  # regra definida pela equipe
            else:
                peso_final = w_uv

            self.add_edge(u, v)
            self.set_edge_weight(u, v, peso_final)

        # 3) Guarda o cache para a futura chamada de from_subjacente().
        self._subjacente_arestas = originais
        self._subjacente_cls = type(grafo_direcionado)
        self._subjacente_num_vertices = n
        self._subjacente_vertex_weights = list(grafo_direcionado.vertex_weights)
        self._subjacente_vertex_labels = dict(grafo_direcionado.vertex_labels)

    def from_subjacente(self) -> AbstractGraph:
        """Reconstrói e retorna o grafo DIRECIONADO original a partir
        do cache guardado pela última chamada a get_subjacente()
        (mesma classe concreta, mesmo número de vértices, mesmos
        rótulos/pesos de vértice e as mesmas arestas com os pesos
        ORIGINAIS — não a média usada na versão não-direcionada).

        Em seguida, ESVAZIA o cache interno (self._subjacente_arestas
        e os demais metadados), conforme especificado pela equipe —
        ou seja, from_subjacente() só pode ser chamado uma vez por
        get_subjacente(); chamadas repetidas sem um novo
        get_subjacente() levantam RuntimeError.
        """
        if self._subjacente_cls is None:
            raise RuntimeError(
                "Nenhum grafo subjacente disponível: chame get_subjacente(g) "
                "antes de from_subjacente()."
            )

        cls = self._subjacente_cls
        n = self._subjacente_num_vertices
        grafo = cls(n)
        grafo.vertex_weights = list(self._subjacente_vertex_weights)
        grafo.vertex_labels = dict(self._subjacente_vertex_labels)

        for (u, v), w in self._subjacente_arestas.items():
            grafo.add_edge(u, v)
            grafo.set_edge_weight(u, v, w)

        # Esvazia o cache (especificação da equipe): from_subjacente()
        # "restaura o grafo direcionado e esvazia o dicionário de
        # arestas e seus pesos originais".
        self._subjacente_arestas = {}
        self._subjacente_cls = None
        self._subjacente_num_vertices = None
        self._subjacente_vertex_weights = None
        self._subjacente_vertex_labels = None

        return grafo

    def has_subjacente(self) -> bool:
        """True se há um grafo direcionado congelado aguardando
        restauração via from_subjacente()."""
        return self._subjacente_cls is not None

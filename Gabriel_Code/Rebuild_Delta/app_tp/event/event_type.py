# ./event/event_type.py
"""Vocabulário fechado de eventos/comandos da arquitetura EDA.

`EventType` é o contrato único entre todas as fontes de comando
(cliques de botão na GUI, o CLI textual em `./cli`, e qualquer futura
fonte — uma API HTTP, por exemplo) e o backend real do projeto. Nenhum
código deve despachar uma string solta como "tipo de evento"; sempre
um membro deste Enum, para que erros de digitação de comando sejam
detectados na hora (KeyError/ValueError), não silenciosamente
ignorados.

Os valores (strings) são o que aparece no CLI textual (ex.: o usuário
digita "bfs source=0"); os nomes dos membros são o que o código Python
usa (`EventType.RUN_BFS`). Mantidos curtos e em snake_case para serem
digitáveis em uma linha de comando.

Organizado em blocos por área do projeto, na mesma divisão das
categorias já usadas em `gui/bridges/test_orchestrator.py` — não é
coincidência: o vocabulário de "o que o sistema sabe fazer" tende a
seguir a mesma organização do "o que o sistema sabe testar".
"""
from enum import Enum, unique


@unique
class EventType(Enum):
    # --- Ciclo de vida do grafo (./grafo/utils/gexf_parser.py) ---
    LOAD_GRAPH = "load_graph"
    SAVE_GRAPH = "save_graph"
    BUILD_GRAPH_FROM_CSV = "build_graph_from_csv"
    UNLOAD_GRAPH = "unload_graph"

    # --- Algoritmos de travessia/caminho (./grafo/networkx_pure/transversal.py) ---
    RUN_BFS = "run_bfs"
    RUN_DFS = "run_dfs"
    RUN_DIJKSTRA = "run_dijkstra"
    RUN_BELLMAN_FORD = "run_bellman_ford"
    RUN_FLOYD_WARSHALL = "run_floyd_warshall"
    RUN_KRUSKAL = "run_kruskal"
    RUN_PRIM = "run_prim"
    RUN_FORD_FULKERSON = "run_ford_fulkerson"
    RUN_EDMONDS_KARP = "run_edmonds_karp"
    RUN_TOPOLOGICAL_SORT = "run_topological_sort"
    RUN_CONNECTED_COMPONENTS = "run_connected_components"
    RUN_KOSARAJU = "run_kosaraju"
    RUN_TARJAN = "run_tarjan"

    # --- Inspeção estrutural (./grafo/utils/graph_structure.py, ./grafo/networkx_pure/structure.py) ---
    SHOW_GRAPH_INFO = "show_graph_info"
    SHOW_STRUCTURE = "show_structure"

    # --- Testes unitários (./gui/bridges/test_orchestrator.py) ---
    LIST_TEST_CATEGORIES = "list_test_categories"
    LIST_TEST_RUNS = "list_test_runs"
    RUN_TESTS = "run_tests"

    # --- Meta-comandos do próprio CLI (./cli) ---
    HELP = "help"
    ECHO = "echo"

    @classmethod
    def from_value(cls, value: str) -> "EventType":
        """Resolve um EventType a partir do texto digitado pelo
        usuário (ex.: "bfs" como alias de "run_bfs"), tentando
        primeiro o valor exato do Enum e depois um pequeno conjunto de
        aliases comuns. Levanta ValueError com uma mensagem clara se
        nada bater — quem chama (cli_cmd_validator) decide o que fazer
        com isso, esta função não imprime nem registra nada."""
        normalized = value.strip().lower()
        try:
            return cls(normalized)
        except ValueError:
            pass

        alias = _ALIASES.get(normalized)
        if alias is not None:
            return alias

        raise ValueError(f"Comando desconhecido: '{value}'")


# Aliases curtos para o CLI textual — não substituem o valor "oficial"
# do Enum (usado internamente e pela GUI), só tornam a digitação no
# terminal mais rápida. Mantido pequeno deliberadamente: cada alias
# adicionado aqui é mais uma forma de "mesma coisa, nome diferente"
# que quem lê um log precisa lembrar.
_ALIASES = {
    "bfs": EventType.RUN_BFS,
    "dfs": EventType.RUN_DFS,
    "dijkstra": EventType.RUN_DIJKSTRA,
    "kruskal": EventType.RUN_KRUSKAL,
    "prim": EventType.RUN_PRIM,
    "info": EventType.SHOW_GRAPH_INFO,
    "structure": EventType.SHOW_STRUCTURE,
    "load": EventType.LOAD_GRAPH,
    "save": EventType.SAVE_GRAPH,
    "test": EventType.RUN_TESTS,
    "?": EventType.HELP,
}

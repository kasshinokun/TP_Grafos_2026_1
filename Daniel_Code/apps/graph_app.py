from core.event_bus import EventBus
from models.graph_models import AdjacencyListGraph

class GraphApp:
    def __init__(self):
        self.bus = EventBus()
        self.bus.subscribe("MINING_COMPLETE", self.build_graph)
        self.user_to_id = {}
        self.id_to_user = {}
        self.next_id = 0

    def get_or_create_user_id(self, username):
        if username not in self.user_to_id:
            self.user_to_id[username] = self.next_id
            self.id_to_user[self.next_id] = username
            self.next_id += 1
        return self.user_to_id[username]

    def build_graph(self, event_type, payload):
        interactions = payload.get("interactions", [])
        
        if not interactions:
            print("[GraphApp] Sem dados para processar.")
            return

        print("\n[GraphApp] Mapeando usuários e construindo o Grafo...")

        # 1. Primeiro passamos por todas as interações para descobrir quantos usuários únicos existem
        for interaction in interactions:
            self.get_or_create_user_id(interaction["opened_by"])
            self.get_or_create_user_id(interaction["closed_by"])

        total_users = len(self.user_to_id)
        print(f"[GraphApp] Total de usuários únicos encontrados: {total_users}")

        # 2. Inicializamos o grafo com o número de usuários
        graph = AdjacencyListGraph(total_users)

        # 3. Adicionamos as arestas (quem fechou -> quem abriu)
        edges_added = 0
        for interaction in interactions:
            u_closer = self.user_to_id[interaction["closed_by"]]
            v_opener = self.user_to_id[interaction["opened_by"]]
            
            # Só cria aresta se o usuário que fechou for diferente do que abriu
            if u_closer != v_opener:
                # Verifica se a aresta já não existe (para manter o grafo simples)
                if not graph.has_edge(u_closer, v_opener):
                    graph.add_edge(u_closer, v_opener)
                    edges_added += 1

        print(f"[GraphApp] Grafo construído com sucesso!")
        print(f"[GraphApp] Nós (Vértices): {graph.get_vertex_count()}")
        print(f"[GraphApp] Interações (Arestas): {graph.get_edge_count()}")
        print(f"[GraphApp] Total de conexões válidas criadas: {edges_added}")
        print("\n[GraphApp] Amostra de Conexões (Quem fechou a issue -> De quem era a issue):")
        
        count = 0
        for u in range(total_users):
            for v in graph.adj[u]:
                print(f"  - {self.id_to_user[u]} -> {self.id_to_user[v]}")
                count += 1
                if count >= 10: # Mostra apenas as 10 primeiras
                    print("  - ...")
                    return
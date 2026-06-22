from grafo.utils.gexf_parser import load_gexf
from grafo.networkx_pure.adapter import GraphAdapter
from grafo.networkx_pure import centrality, structure, communities

if __name__ == "__main__":
    print("Carregando grafo...")
    G = load_gexf('graph1.gexf.txt')
    print(f"Sucesso: {G.get_vertex_count()} nós, {G.get_edge_count()} arestas.\n")
    
    adapter = GraphAdapter(G)
    
    print("--- API Obrigatória ---")
    print(f"Conectado? {G.is_connected()} | Completo? {G.is_complete_graph()}")
    print(f"0 é sucessor de 2? {G.is_sucessor(2, 0)}\n")
    
    print("--- Centralidade (Top 3 PageRank) ---")
    pr = centrality.pagerank(adapter)
    for u, val in sorted(pr.items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"{G.vertex_labels[u]}: {val:.4f}")
        
    print("\n--- Estrutura ---")
    print(f"Densidade: {structure.density(adapter):.5f}")
    print(f"Assortatividade: {structure.assortativity(adapter):.4f}")
    
    print("\n--- Comunidades ---")
    comms = communities.label_propagation_communities(adapter)
    print(f"Comunidades: {len(comms)} | Modularidade: {communities.modularity(adapter, comms):.4f}")
    
    G.export_to_gephi("saida_gephi.gexf")
    print("\nGrafo exportado para saida_gephi.gexf")
import customtkinter as ctk
import json
import os
import sys

# Garante que o Python ache as nossas pastas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph_engine.lapidador import Lapidador
from graph_engine.implementations import AdjacencyListGraph
import graph_engine.analysis as analysis

# Configuração visual do CTK
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class GraphAnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GraphAnalyzer - Teoria dos Grafos")
        self.geometry("950x650")
        
        self.grafo = None
        # Apontando para a nova pasta 'data'
        self.dados_lapidados_path = os.path.join("data", "dados_lapidados.json")
        self.users_map = {}
        self.id_to_user = {}

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Menu Lateral ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="Painel de Controle", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        self.btn_lapidar = ctk.CTkButton(self.sidebar, text="1. Lapidar JSONs Brutos", command=self.run_lapidador)
        self.btn_lapidar.grid(row=1, column=0, padx=20, pady=10)

        self.btn_build = ctk.CTkButton(self.sidebar, text="2. Construir Grafo", command=self.build_graph)
        self.btn_build.grid(row=2, column=0, padx=20, pady=10)

        self.btn_metrics = ctk.CTkButton(self.sidebar, text="3. Calcular Centralidade", command=self.run_metrics)
        self.btn_metrics.grid(row=3, column=0, padx=20, pady=10)

        self.btn_gephi = ctk.CTkButton(self.sidebar, text="4. Exportar p/ GEPHI", command=self.export_gephi)
        self.btn_gephi.grid(row=4, column=0, padx=20, pady=10)

        # --- Área de Log Central ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(self.main_frame, text="Terminal de Execução", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, pady=20)

        self.console = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(family="Consolas", size=13))
        self.console.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.log_msg("Sistemas iniciados. Aguardando comandos...\n")

    def log_msg(self, msg: str):
        self.console.insert("end", msg + "\n")
        self.console.see("end")

    def run_lapidador(self):
        self.log_msg("[-] Iniciando extração e lapidação dos dados...")
        try:
            lapidador = Lapidador.initialize_work()
            
            # Capturamos o caminho se o lapidador do seu colega o retornar
            caminho_gerado = lapidador.lapidar() 
            
            # A Inteligência de busca: Atualiza o caminho dependendo de onde o arquivo foi parar
            if caminho_gerado and isinstance(caminho_gerado, str) and os.path.exists(caminho_gerado):
                self.dados_lapidados_path = caminho_gerado
            elif os.path.exists("dados_lapidados.json"):
                self.dados_lapidados_path = "dados_lapidados.json" # Achou na raiz
            elif os.path.exists(os.path.join("data", "dados_lapidados.json")):
                self.dados_lapidados_path = os.path.join("data", "dados_lapidados.json") # Achou na pasta data

            self.log_msg(f"[+] Sucesso! Dados lapidados localizados em: {self.dados_lapidados_path}")
        except Exception as e:
            self.log_msg(f"[Erro] Falha ao lapidar dados: {e}")

    def build_graph(self):
        if not self.dados_lapidados_path or not os.path.exists(self.dados_lapidados_path):
            self.log_msg("[!] Erro: Arquivo lapidado não encontrado. Execute o Passo 1.")
            return

        self.log_msg(f"[-] Modelando o Grafo a partir de: {self.dados_lapidados_path}...")
        with open(self.dados_lapidados_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        num_vertices = dados['metadata']['total_users']
        self.users_map = dados['users']
        self.id_to_user = {v: k for k, v in self.users_map.items()}

        self.grafo = AdjacencyListGraph(num_vertices)

        # Atribuir rótulos para o GEPHI
        for user_login, u_id in self.users_map.items():
            self.grafo._vertex_labels[u_id] = user_login

        interacoes = dados['interactions']
        for inter in interacoes:
            u_login = inter.get('from')
            v_login = inter.get('to')
            peso = inter.get('weight', 1)
            
            if u_login and v_login:
                u_id = self.users_map[u_login]
                v_id = self.users_map[v_login]
                
                if u_id != v_id: # Sem auto-laços
                    if not self.grafo.hasEdge(u_id, v_id):
                        # CORREÇÃO APLICADA AQUI:
                        self.grafo.addEdge(u_id, v_id)
                        self.grafo.setEdgeWeight(u_id, v_id, peso)

        self.log_msg(f"[+] Matriz/Lista construída com sucesso!")
        self.log_msg(f"    -> Vértices (Nós): {self.grafo.getVertexCount()}")
        self.log_msg(f"    -> Interações (Arestas): {self.grafo.getEdgeCount()}")

    def run_metrics(self):
        if not self.grafo:
            self.log_msg("[!] Construa o grafo primeiro (Passo 2).")
            return

        self.log_msg("\n[-] Calculando métricas topológicas...")
        
        # Centralidade de Grau
        deg_cent = analysis.degree_centrality(self.grafo)
        top_deg = sorted(deg_cent.items(), key=lambda x: x[1], reverse=True)[:5]
        
        self.log_msg("\n[+] Top 5 - Usuários mais influentes (Grau):")
        for u_id, score in top_deg:
            self.log_msg(f"    {self.id_to_user[u_id]}: {score:.2f}")

    def export_gephi(self):
        if not self.grafo:
            self.log_msg("[!] Construa o grafo primeiro (Passo 2).")
            return
            
        caminho_export = os.path.join("data", "grafo_github.gexf")
        self.grafo.exportToGEPHI(caminho_export)
        self.log_msg(f"\n[+] Sucesso! Arquivo .gexf gerado em: {caminho_export}")
        self.log_msg("    -> Você já pode abrir este arquivo no software GEPHI.")

if __name__ == "__main__":
    app = GraphAnalyzerApp()
    app.mainloop()
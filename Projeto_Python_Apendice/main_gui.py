import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import sys
import io

# Importações do seu minerador e do núcleo do seu sistema
from minerador import minerar_dados, TOKENS_GRUPO, REPO_NAME

# NOTA: Como você tem um interpretador CLI robusto, vamos criar uma classe de ponte 
# para capturar comandos ou instanciar sua classe Application diretamente.
# Caso queira disparar diretamente via texto por trás dos panos, a interface fará isso.
from grafo.core.application import Application
from grafo.cli.cli import CLI

class GraphUltimateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ferramenta de Análise de Grafos – PUC Minas (Versão Integrada)")
        self.root.geometry("1200x800")
        
        # Inicializa o motor REAL do seu projeto exatamente como no seu main.py
        try:
            self.app_core = Application()
            self.cli_core = CLI(self.app_core)  # <--- Instanciamos o seu CLI passando o app
        except Exception as e:
            print(f"Aviso ao carregar Application/CLI Core: {e}")
            self.app_core = None
            self.cli_core = None

        self.setup_styles()
        self.create_tabs()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook.Tab", padding=[15, 8], font=('Helvetica', 10, 'bold'))
        style.configure("TButton", font=('Helvetica', 9, 'bold'))
        style.configure("Header.TLabel", font=('Helvetica', 12, 'bold'), foreground="#2b2d42")

    def create_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # 1. ABA DE EXTRAÇÃO DATA MINING
        self.tab_mine = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_mine, text=" ⛏  1. Mineração ")
        self.setup_mining_tab()

        # 2. ABA DE GERENCIAMENTO E CRIAÇÃO (CONSTRUTORES)
        self.tab_manage = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_manage, text=" 📁 2. Gerenciar Grafos ")
        self.setup_management_tab()

        # 3. ABA DE OPERAÇÕES PRIMITIVAS (API OBRIGATÓRIA)
        self.tab_api = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_api, text=" ⚙  3. API Primitiva ")
        self.setup_api_tab()

        # 4. ABA DE ALGORITMOS CLÁSSICOS (TRAVERSAL & SHORTEST PATH)
        self.tab_alg = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_alg, text=" 🚀 4. Buscas & Caminhos ")
        self.setup_algorithms_tab()

        # 5. ABA DE REDES COMPLEXAS & COMUNIDADES (METRICAS AVANÇADAS)
        self.tab_metrics = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_metrics, text=" 📊 5. Redes Complexas ")
        self.setup_metrics_tab()

        # 6. CONSOLE UNIFICADO INFERIOR
        self.setup_bottom_console()

    # ──────────────────────────────────────────────────────────────────────────
    # MÓDULO 1: MINERAÇÃO
    # ──────────────────────────────────────────────────────────────────────────
    def setup_mining_tab(self):
        lbl = ttk.Label(self.tab_mine, text=f"Pipeline de Dados - Repositório: {REPO_NAME}", style="Header.TLabel")
        lbl.pack(pady=10)

        btn_run = ttk.Button(self.tab_mine, text="INICIAR MINERAÇÃO MULTITHREAD DO REPOSITÓRIO", command=self.run_mining_async)
        btn_run.pack(pady=15, ipady=5)

        info_box = ttk.LabelFrame(self.tab_mine, text=" Instruções e Fluxo ")
        info_box.pack(fill="both", expand=True, padx=20, pady=10)
        
        txt = ("1. Clique no botão acima para iniciar a mineração multithread paralela via API do GitHub.\n"
               "2. O script gerará automaticamente o arquivo 'interacoes_reais.csv' na raiz.\n"
               "3. Após gerar, vá para a aba '2. Gerenciar Grafos' para carregar os dados nas estruturas de dados.")
        ttk.Label(info_box, text=txt, font=("Helvetica", 10), justify="left").pack(padx=15, pady=15, anchor="w")

    # ──────────────────────────────────────────────────────────────────────────
    # MÓDULO 2: GERENCIAMENTO E CARGA DE GRAFOS
    # ──────────────────────────────────────────────────────────────────────────
    def setup_management_tab(self):
        # Frame Criar Grafo do zero
        f_create = ttk.LabelFrame(self.tab_manage, text=" Comando: create <id> <n> [matrix|list] ")
        f_create.pack(fill="x", padx=20, pady=10)
        
        ttk.Label(f_create, text="ID do Grafo:").grid(row=0, column=0, padx=5, pady=5)
        self.ent_m_id = ttk.Entry(f_create, width=8)
        self.ent_m_id.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(f_create, text="Nº Vértices:").grid(row=0, column=2, padx=5, pady=5)
        self.ent_m_n = ttk.Entry(f_create, width=8)
        self.ent_m_n.grid(row=0, column=3, padx=5, pady=5)

        self.combo_m_type = ttk.Combobox(f_create, values=["list", "matrix"], width=10, state="readonly")
        self.combo_m_type.current(0)
        self.combo_m_type.grid(row=0, column=4, padx=5, pady=5)

        ttk.Button(f_create, text="Criar Grafo Vazio", command=self.cmd_create).grid(row=0, column=5, padx=10, pady=5)

        # Carga em lote externa
        f_batch = ttk.LabelFrame(self.tab_manage, text=" Carga em Lote e Automação do Trabalho Prático ")
        f_batch.pack(fill="x", padx=20, pady=10)

        ttk.Button(f_batch, text="Carregar CSV Unitário (load-csv)", command=self.cmd_load_csv).pack(side="left", padx=10, pady=10)
        ttk.Button(f_batch, text="Construir os 4 Grafos do Trabalho (build-graphs)", command=self.cmd_build_graphs, style="TButton").pack(side="left", padx=10, pady=10)
        ttk.Button(f_batch, text="Listar Grafos Ativos (list)", command=self.cmd_list).pack(side="left", padx=10, pady=10)
        ttk.Button(f_batch, text="Gerar Exemplo (sample-csv)", command=self.cmd_sample_csv).pack(side="left", padx=10, pady=10)

    # ──────────────────────────────────────────────────────────────────────────
    # MÓDULO 3: API PRIMITIVA (MÉTODOS DA CLASSE ABSTRATA)
    # ──────────────────────────────────────────────────────────────────────────
    def setup_api_tab(self):
        f_selectors = ttk.Frame(self.tab_api)
        f_selectors.pack(fill="x", padx=20, pady=5)

        ttk.Label(f_selectors, text="ID do Grafo Alvo:").pack(side="left", padx=2)
        self.api_graph_id = ttk.Entry(f_selectors, width=6)
        self.api_graph_id.pack(side="left", padx=5)

        ttk.Label(f_selectors, text="Vértice U / Src:").pack(side="left", padx=2)
        self.api_u = ttk.Entry(f_selectors, width=6)
        self.api_u.pack(side="left", padx=5)

        ttk.Label(f_selectors, text="Vértice V / Dst:").pack(side="left", padx=2)
        self.api_v = ttk.Entry(f_selectors, width=6)
        self.api_v.pack(side="left", padx=5)

        ttk.Label(f_selectors, text="Peso/Weight:").pack(side="left", padx=2)
        self.api_w = ttk.Entry(f_selectors, width=6)
        self.api_w.pack(side="left", padx=5)

        # Grid de botões mapeando as chamadas diretas da imagem do CLI
        f_grid = ttk.LabelFrame(self.tab_api, text=" Operações Atômicas da API ")
        f_grid.pack(fill="both", expand=True, padx=20, pady=10)

        # Linha 1
        ttk.Button(f_grid, text="add-edge", command=lambda: self.execute_cli_action("add-edge")).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(f_grid, text="rem-edge", command=lambda: self.execute_cli_action("rem-edge")).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(f_grid, text="has-edge", command=lambda: self.execute_cli_action("has-edge")).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ttk.Button(f_grid, text="info", command=lambda: self.execute_cli_action("info")).grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        # Linha 2
        ttk.Button(f_grid, text="degree (In/Out)", command=lambda: self.execute_cli_action("degree")).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(f_grid, text="connected ?", command=lambda: self.execute_cli_action("connected")).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(f_grid, text="show estrutura", command=lambda: self.execute_cli_action("show")).grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        ttk.Button(f_grid, text="export GEPHI", command=self.cmd_export_gephi).grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        for i in range(4): f_grid.columnconfigure(i, weight=1)

    # ──────────────────────────────────────────────────────────────────────────
    # MÓDULO 4: BUSCAS E CAMINHOS MÍNIMOS
    # ──────────────────────────────────────────────────────────────────────────
    def setup_algorithms_tab(self):
        f_alg = ttk.LabelFrame(self.tab_alg, text=" Execução de Algoritmos Clássicos de Caminhamento ")
        f_alg.pack(fill="both", expand=True, padx=20, pady=10)

        ttk.Label(f_alg, text="ID Grafo:").grid(row=0, column=0, padx=5, pady=10)
        self.alg_id = ttk.Entry(f_alg, width=8)
        self.alg_id.grid(row=0, column=1, padx=5, pady=10)

        ttk.Label(f_alg, text="Vértice Origem:").grid(row=0, column=2, padx=5, pady=10)
        self.alg_src = ttk.Entry(f_alg, width=8)
        self.alg_src.grid(row=0, column=3, padx=5, pady=10)

        ttk.Label(f_alg, text="Vértice Destino:").grid(row=0, column=4, padx=5, pady=10)
        self.alg_dst = ttk.Entry(f_alg, width=8)
        self.alg_dst.grid(row=0, column=5, padx=5, pady=10)

        # Botões de disparo dos algoritmos
        ttk.Button(f_alg, text="Executar BFS (Busca em Largura)", command=lambda: self.run_traversal("bfs")).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(f_alg, text="Executar DFS (Busca em Profundidade)", command=lambda: self.run_traversal("dfs")).grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(f_alg, text="Caminho Mínimo (Dijkstra)", command=lambda: self.run_traversal("shortest")).grid(row=1, column=4, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Button(f_alg, text="Ordenação Topológica (topsort)", command=lambda: self.run_traversal("topsort")).grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        ttk.Button(f_alg, text="Componentes Fortemente Conexos (scc)", command=lambda: self.run_traversal("scc")).grid(row=2, column=3, columnspan=3, padx=5, pady=5, sticky="ew")

    # ──────────────────────────────────────────────────────────────────────────
    # MÓDULO 5: REDES COMPLEXAS & COMUNIDADES
    # ──────────────────────────────────────────────────────────────────────────
    def setup_metrics_tab(self):
        f_top = ttk.Frame(self.tab_metrics)
        f_top.pack(fill="x", padx=20, pady=10)

        ttk.Label(f_top, text="ID Grafo:").pack(side="left", padx=5)
        self.met_id = ttk.Entry(f_top, width=8)
        self.met_id.pack(side="left", padx=5)

        ttk.Button(f_top, text="Análise Completa (full-analysis)", command=self.cmd_full_analysis).pack(side="left", padx=10)

        # Grid de métricas individuais extraídas da sua imagem do prompt
        f_grid = ttk.LabelFrame(self.tab_metrics, text=" Métricas Individuais e Redes Complexas ")
        f_grid.pack(fill="both", expand=True, padx=20, pady=10)

        # Coluna 1: Centralidades
        ttk.Button(f_grid, text="Centralidade de Grau", command=lambda: self.run_metric("degree-centrality")).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(f_grid, text="Centralidade de Intermediação", command=lambda: self.run_metric("betweenness")).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(f_grid, text="Centralidade de Proximidade", command=lambda: self.run_metric("closeness")).grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(f_grid, text="Algoritmo PageRank", command=lambda: self.run_metric("pagerank")).grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        # Coluna 2: Coesão Estrutural e Comunidades
        ttk.Button(f_grid, text="Densidade da Rede", command=lambda: self.run_metric("density")).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(f_grid, text="Coeficiente de Aglomeração", command=lambda: self.run_metric("clustering")).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(f_grid, text="Assortatividade", command=lambda: self.run_metric("assortativity")).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(f_grid, text="Detecção de Comunidades", command=lambda: self.run_metric("communities")).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        # Bridging Ties
        ttk.Button(f_grid, text="Pontes de Conexão (bridging)", command=lambda: self.run_metric("bridging")).grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        for i in range(2): f_grid.columnconfigure(i, weight=1)

    # ──────────────────────────────────────────────────────────────────────────
    # CONSOLE CONSOLIDADO
    # ──────────────────────────────────────────────────────────────────────────
    def setup_bottom_console(self):
        lbl = ttk.Label(self.root, text="Terminal de Saída Unificado (Logs do Sistema):")
        lbl.pack(anchor="w", padx=15)
        
        self.txt_console = scrolledtext.ScrolledText(self.root, height=12, bg="#1a1a1a", fg="#ffffff", font=('Consolas', 10))
        self.txt_console.pack(fill="x", expand=False, padx=10, pady=5)
        self.txt_console.insert(tk.END, "=== Sistema de Grafos Pronto ===\nDigite parâmetros nas abas e clique nos comandos correspondentes.\n")

    def print_to_console(self, text):
        self.txt_console.insert(tk.END, text + "\n")
        self.txt_console.see(tk.END)

    # ──────────────────────────────────────────────────────────────────────────
    # INTERPRETAÇÃO E EXECUÇÃO DE COMANDOS (PONTE COM SEU MOTOR ORIGINAL)
    # ──────────────────────────────────────────────────────────────────────────
    def run_mining_async(self):
        def task():
            self.print_to_console("\n>>> Iniciando Mineração Paralela...")
            # Captura de logs dinâmica do stdout do script minerador
            class LogCapture:
                def __init__(self, console_func): self.func = console_func
                def write(self, s): self.func(s.replace('\r', '\n'))
                def flush(self): pass
            
            sys.stdout = LogCapture(self.print_to_console)
            try:
                minerar_dados()
                self.root.after(0, lambda: messagebox.showinfo("Mineração", "Arquivo interacoes_reais.csv gerado com segurança!"))
            except Exception as e:
                self.print_to_console(f"\n❌ Erro durante a mineração: {e}")
            finally:
                sys.stdout = sys.__stdout__
                
        threading.Thread(target=task, daemon=True).start()

    def execute_core_command(self, cmd_str):
        """Passa a string de comando pura diretamente para o process_command do CLI real."""
        self.print_to_console(f"\n> {cmd_str}")
        if self.cli_core is None:
            self.print_to_console("⚠️ Erro: Estrutura do CLI Core não inicializada.")
            return

        # Captura o retorno dos prints que o seu CLI jogaria na tela preta
        buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buffer
        
        try:
            # CORREÇÃO CRÍTICA: Passamos a string limpa (cmd_str) 
            # O seu método process_command vai cuidar do split internamente!
            self.cli_core.process_command(cmd_str)
                
        except Exception as e:
            print(f"Erro na execução interna do CLI: {e}")
        finally:
            sys.stdout = old_stdout
            
        output = buffer.getvalue()
        if output:
            self.print_to_console(output.strip())
        else:
            self.print_to_console("Comando executado no barramento de eventos.")

    # Mapeamento individual de cada ação da tela
    def cmd_create(self):
        g_id = self.ent_m_id.get().strip()
        n = self.ent_m_n.get().strip()
        g_type = self.combo_m_type.get()
        if not g_id or not n:
            messagebox.showwarning("Campos Vazios", "Informe o ID do grafo e número de vértices.")
            return
        self.execute_core_command(f"create {g_id} {n} {g_type}")

    def cmd_list(self):
        self.execute_core_command("list")

    def cmd_sample_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            self.execute_core_command(f"sample-csv {path}")

    def cmd_load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            self.execute_core_command(f"load-csv {path}")

    def cmd_build_graphs(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")], title="Selecione o arquivo interacoes_reais.csv")
        if path:
            self.execute_core_command(f"build-graphs {path}")

    def cmd_export_gephi(self):
        g_id = self.api_graph_id.get().strip()
        if not g_id:
            messagebox.showwarning("Aviso", "Informe o ID do grafo na aba de campos superiores.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".gexf", filetypes=[("GEPHI Files", "*.gexf")])
        if path:
            self.execute_core_command(f"export {g_id} {path}")

    def execute_cli_action(self, action):
        g_id = self.api_graph_id.get().strip()
        u = self.api_u.get().strip()
        v = self.api_v.get().strip()
        w = self.api_w.get().strip()

        if not g_id:
            messagebox.showwarning("Aviso", "Identifique o ID do grafo de destino.")
            return

        if action == "info":
            self.execute_core_command(f"info {g_id}")
        elif action == "connected":
            self.execute_core_command(f"connected {g_id}")
        elif action == "show":
            self.execute_core_command(f"show {g_id}")
        elif action == "add-edge":
            cmd = f"add-edge {g_id} {u} {v}"
            if w: cmd += f" {w}"
            self.execute_core_command(cmd)
        elif action == "rem-edge":
            self.execute_core_command(f"rem-edge {g_id} {u} {v}")
        elif action == "has-edge":
            self.execute_core_command(f"has-edge {g_id} {u} {v}")
        elif action == "degree":
            self.execute_core_command(f"degree {g_id} {u}")

    def run_traversal(self, mode):
        g_id = self.alg_id.get().strip()
        src = self.alg_src.get().strip()
        dst = self.alg_dst.get().strip()

        if not g_id:
            messagebox.showwarning("Aviso", "Informe o ID do grafo para algoritmos.")
            return

        if mode == "topsort":
            self.execute_core_command(f"topsort {g_id}")
        elif mode == "scc":
            self.execute_core_command(f"scc {g_id}")
        elif mode == "bfs":
            self.execute_core_command(f"bfs {g_id} {src}")
        elif mode == "dfs":
            self.execute_core_command(f"dfs {g_id} {src}")
        elif mode == "shortest":
            self.execute_core_command(f"shortest {g_id} {src} {dst}")

    def run_metric(self, metric_name):
        g_id = self.met_id.get().strip()
        if not g_id:
            messagebox.showwarning("Aviso", "Especifique o ID do grafo para a métrica.")
            return
        self.execute_core_command(f"{metric_name} {g_id}")

    def cmd_full_analysis(self):
        g_id = self.met_id.get().strip()
        if not g_id:
            messagebox.showwarning("Aviso", "Especifique o ID do grafo para a análise completa.")
            return
        self.execute_core_command(f"full-analysis {g_id}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphUltimateGUI(root)
    root.mainloop()
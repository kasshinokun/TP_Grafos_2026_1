# Interface para trabalhar com PureNetworkX(NertworX feito por Gabriel)


import logging
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Optional
import threading
import sys
import io
import webbrowser
import json

import customtkinter as ctk
from PIL import Image, ImageTk
import qrcode
from pyzbar.pyzbar import decode

from filemanager import FileSet # Filemanager

# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Porcentagem da largura destinada ao terminal (lado direito)
RIGHT_WIDTH_PERCENT = 50

LEFT_WIDTH_PERCENT = 50

REPO_URL = "https://github.com/kasshinokun/TP_Grafos_2026_1"

PATH_D_CSV = FileSet.set_dir("csv")
PATH_D_GEXF = FileSet.set_dir("gexf")
PATH_D_QR = FileSet.set_dir("qr_tokens")
try:
    from minerador_hibrido import minerar_dados
except Exception:
    from minerador import minerar_dados
from minerador import TOKENS_GRUPO, REPO_NAME

from grafo.core.application import Application
from grafo.cli.cli import CLI


class GraphUltimateGUI:
    def __init__(self, root):
        self.root = root
        self.name_interface = f"Pipeline de Dados - Repositório: {REPO_NAME}"
        self.root.title("Ferramenta de Análise de Grafos – PUC Minas (CTk)")
        self.root.geometry("1400x850")
        self.secret_tokens=[]
        try:
            self.app_core = Application()
            self.cli_core = CLI(self.app_core)
        except Exception as e:
            print(f"Aviso ao carregar Application/CLI Core: {e}")
            self.app_core = None
            self.cli_core = None

        self.create_layout()
        self.create_screens()
        self.setup_console()

        # Seleciona a primeira tela por padrão
        self.screen_selector.set(list(self.screens.keys())[0])
        self.show_screen(self.screen_selector.get())

    def create_layout(self):
        """Cria os frames esquerdo e direito com proporções definidas."""
        self.root.grid_columnconfigure(0, weight=LEFT_WIDTH_PERCENT)
        self.root.grid_columnconfigure(1, weight=RIGHT_WIDTH_PERCENT)
        self.root.grid_rowconfigure(0, weight=1)

        # Frame esquerdo (telas)
        self.left_frame = ctk.CTkFrame(self.root)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self.left_frame.grid_rowconfigure(0, weight=0)  # combobox
        self.left_frame.grid_rowconfigure(1, weight=1)  # conteúdo
        self.left_frame.grid_columnconfigure(0, weight=1)

        # Frame direito (console)
        self.right_frame = ctk.CTkFrame(self.root)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        self.right_frame.grid_rowconfigure(0, weight=0)  # label
        self.right_frame.grid_rowconfigure(1, weight=1)  # textbox

        # Combobox para selecionar a tela
        self.screen_selector = ctk.CTkComboBox(
            self.left_frame,
            values=[],  # será preenchido em create_screens
            command=self.show_screen,
            state="readonly",
            width=250
        )
        self.screen_selector.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Frame que conterá o conteúdo da tela selecionada
        self.content_frame = ctk.CTkFrame(self.left_frame)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Dicionário para armazenar os frames de cada tela
        self.screens = {}

    def create_screens(self):
        """Cria todas as telas (frames) e as armazena no dicionário."""
        # Define os nomes das telas (ordem será a da combobox)
        screen_names = [
            "Mineração",
            "Gerenciar Grafos",
            "API Primitiva",
            "Buscas & Caminhos",
            "Redes Complexas",
            "PureNetworkX & Testes",
            "Sobre"
        ]

        # Cria um frame para cada tela e o insere no content_frame
        for name in screen_names:
            frame = ctk.CTkFrame(self.content_frame)
            # Cada tela será configurada com seu respectivo método
            if name == "Mineração":
                self.setup_mining_screen(frame)
            elif name == "Gerenciar Grafos":
                self.setup_management_screen(frame)
            elif name == "API Primitiva":
                self.setup_api_screen(frame)
            elif name == "Buscas & Caminhos":
                self.setup_algorithms_screen(frame)
            elif name == "Redes Complexas":
                self.setup_metrics_screen(frame)
            elif name == "PureNetworkX & Testes":      
                self.setup_networkx_screen(frame)      
            elif name == "Sobre":
                self.setup_about_screen(frame)

            # Guarda o frame no dicionário
            self.screens[name] = frame

        # Atualiza a combobox com os nomes
        self.screen_selector.configure(values=screen_names)

    def show_screen(self, screen_name: str):
        """Exibe a tela selecionada e oculta as demais."""
        for name, frame in self.screens.items():
            if name == screen_name:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    # ============================================================
    # CONSOLE (lado direito)
    # ============================================================
    def setup_console(self):
        lbl = ctk.CTkLabel(self.right_frame, text="📋 Terminal de Saída", font=("Helvetica", 14, "bold"))
        lbl.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.txt_console = ctk.CTkTextbox(
            self.right_frame,
            font=("Consolas", 11),
            wrap="word",
            fg_color="#1a1a1a",
            text_color="#ffffff"
        )
        self.txt_console.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.txt_console.insert("0.0", "=== Sistema de Grafos Pronto (CTk) ===\n")
        self.txt_console.see("end")

    def print_to_console(self, text):
        self.txt_console.insert("end", text + "\n")
        self.txt_console.see("end")
        # print(text)

    def _safe_print(self, text: str) -> None:
        if hasattr(self, "txt_console"):
            self.print_to_console(text)
        print(text)
            

    # ============================================================
    # 1. TELA MINERAÇÃO
    # ============================================================
    def decodificar_qr(self, caminho_imagem: str) -> dict:
        img = Image.open(caminho_imagem)
        dados = decode(img)
        if not dados:
            raise ValueError("Nenhum QR Code encontrado na imagem.")
        conteudo = dados[0].data.decode('utf-8')
        return json.loads(conteudo)

    def carregar_qr(self):
        caminho = filedialog.askopenfilename(
            initialdir=PATH_D_QR,
            title="Selecione a imagem do QR Code",
            filetypes=[("PNG images", "*.png"), ("All files", "*.*")]
        )
        if not caminho:
            return
        try:
            dados = self.decodificar_qr(caminho)
            self.txt_tokens.delete("0.0", "end")
            tokens = dados.get("token", [])
            if isinstance(tokens, list):
                self.secret_tokens = tokens
                self.txt_tokens.insert("0.0", "\n".join(list(self.mask_token(x) for x in tokens)))
            else:
                raise ModuleNotFoundError("Tokens inválidos")
                # self.txt_tokens.insert("0.0", list(self.mask_token(x) for x in tokens))

            self.ent_owner.delete(0, "end")
            self.ent_owner.insert(0, dados.get("target_user", ""))

            self.ent_repo.delete(0, "end")
            self.ent_repo.insert(0, dados.get("target_repo", ""))

            self.print_to_console(
                f"✅ QR Code lido: {len(tokens) if isinstance(tokens, list) else 1} token(s), "
                f"user={dados.get('target_user')}, repo={dados.get('target_repo')}"
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao ler QR Code:\n{e}")
            self.print_to_console(f"❌ Erro: {e}")

    def setup_mining_screen(self, parent):
        
        # Talvez precise se tornar uma variavel nomeada para atualizar em tempo real
        self.lab_mining_screen = ctk.CTkLabel(parent, text=self.name_interface,
                     font=("Helvetica", 16, "bold")).pack(pady=10)

        f_creds = ctk.CTkFrame(parent, border_width=2, border_color="gray")
        f_creds.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(f_creds, text="Tokens (um por linha):").grid(row=0, column=0, sticky="nw", padx=10, pady=5)
        self.txt_tokens = ctk.CTkTextbox(f_creds, height=120, width=400)
        self.txt_tokens.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(f_creds, text="Owner:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.ent_owner = ctk.CTkEntry(f_creds, width=400)
        self.ent_owner.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(f_creds, text="Repo:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.ent_repo = ctk.CTkEntry(f_creds, width=400)
        self.ent_repo.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        btn_qr = ctk.CTkButton(f_creds, text="📷 Carregar QR Code (PNG)", command=self.carregar_qr)
        btn_qr.grid(row=3, column=0, columnspan=2, pady=10)

        ctk.CTkButton(parent, text="🚀 INICIAR MINERAÇÃO MULTITHREAD",
                      command=self.run_mining_async,
                      height=40, font=("Helvetica", 14, "bold")).pack(pady=15)

        f_info = ctk.CTkFrame(parent, border_width=2, border_color="gray")
        f_info.pack(fill="both", expand=True, padx=20, pady=10)
        txt = (
            "1. Preencha os tokens (um por linha) e o repositório desejado.\n"
            "2. Ou carregue um QR Code com o JSON no formato especificado.\n"
            "3. Clique em 'INICIAR MINERAÇÃO...' para coletar os dados.\n"
            "4. Após a geração do CSV, vá para a tela 'Gerenciar Grafos' para carregá-lo."
        )
        ctk.CTkLabel(f_info, text=txt, justify="left", font=("Helvetica", 12)).pack(padx=15, pady=15, anchor="w")

    def mask_token(self, token: str) -> str:
        clean = token.strip()
        if len(clean) >= 4:
            return f"|---------------> Token ...{clean[-4:]}"
        return f"|---------------> Token ...{clean}"

    def run_mining_async(self):
        tokens_list = self.secret_tokens
        if not tokens_list:
            messagebox.showwarning("Campos vazios", "Informe pelo menos um token.")
            return
        #tokens_list = [t.strip() for t in tokens_text.splitlines() if t.strip()]
        #if not tokens_list:
            messagebox.showwarning("Tokens inválidos", "Nenhum token válido encontrado.")
            return

        owner = self.ent_owner.get().strip()
        repo = self.ent_repo.get().strip()
        if not owner or not repo:
            messagebox.showwarning("Campos vazios", "Preencha Owner e Repo.")
            return

        import minerador
        minerador.TOKENS_GRUPO = tokens_list
        minerador.REPO_NAME = f"{owner}/{repo}"
        self.name_interface = f"Pipeline de Dados - Repositório: {REPO_NAME}"
        
        masked = [self.mask_token(t) for t in tokens_list] # precaução
        self.print_to_console(f"🔑 {len(tokens_list)} token(s) carregado(s):")
        for m in masked:
            self.print_to_console(f"   {m}")
        self.print_to_console(f"📁 Repositório alvo: {owner}/{repo}")

        def task():
            self.print_to_console("\n>>> Iniciando Mineração Paralela...")
            class LogCapture:
                def __init__(self, console_func): self.func = console_func
                def write(self, s): self.func(s.replace('\r', '\n'))
                def flush(self): pass

            sys.stdout = LogCapture(self.print_to_console)
            try:
                minerador.minerar_dados()
                self.root.after(0, lambda: messagebox.showinfo("Mineração", "Arquivo interacoes_reais.csv gerado com sucesso!"))
            except Exception as e:
                self.print_to_console(f"\n❌ Erro durante a mineração: {e}")
            finally:
                sys.stdout = sys.__stdout__

        threading.Thread(target=task, daemon=True).start()

    # ============================================================
    # 2. TELA GERENCIAR GRAFOS
    # ============================================================
    def setup_management_screen(self, parent):
        f_create = ctk.CTkFrame(parent, border_width=2, border_color="gray")
        f_create.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(f_create, text="ID do Grafo:").grid(row=0, column=0, padx=5, pady=5)
        #self.ent_m_id = ctk.CTkEntry(f_create, width=100)
        self.ent_m_id = ctk.CTkComboBox(f_create, values=['graph1', 'graph2', 'graph3','graph_integrated'], state="readonly")
        # self.execute_core_command("names-default")
        self.ent_m_id.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(f_create, text="Nº Vértices:").grid(row=0, column=2, padx=5, pady=5)
        self.ent_m_n = ctk.CTkEntry(f_create, width=100)
        self.ent_m_n.grid(row=0, column=3, padx=5, pady=5)

        self.combo_m_type = ctk.CTkComboBox(f_create, values=["list", "matrix"], state="readonly")
        self.combo_m_type.set("list")
        self.combo_m_type.grid(row=0, column=4, padx=5, pady=5)

        ctk.CTkButton(f_create, text="Criar Grafo Vazio", command=self.cmd_create).grid(row=0, column=5, padx=10, pady=5)

        f_batch = ctk.CTkFrame(parent, border_width=2, border_color="gray")
        f_batch.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(f_batch, text="Carregar CSV Unitário (load-csv)", command=self.cmd_load_csv).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(f_batch, text="Construir os 4 Grafos (build-graphs)", command=self.cmd_build_graphs).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(f_batch, text="Listar Grafos Ativos (list)", command=self.cmd_list).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(f_batch, text="Gerar Exemplo (sample-csv)", command=self.cmd_sample_csv).pack(side="left", padx=10, pady=10)

    # ============================================================
    # 3. TELA API PRIMITIVA
    # ============================================================
    def setup_api_screen(self, parent):
        f_selectors = ctk.CTkFrame(parent)
        f_selectors.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(f_selectors, text="ID Grafo:").pack(side="left", padx=2)
        
        #self.api_graph_id = ctk.CTkEntry(f_selectors, width=80)
        self.api_graph_id = ctk.CTkComboBox(f_selectors, values=['graph1', 'graph2', 'graph3','graph_integrated'], state="readonly")
        # self.execute_core_command("names-default")
        
        self.api_graph_id.pack(side="left", padx=5)

        ctk.CTkLabel(f_selectors, text="Vértice U:").pack(side="left", padx=2)
        self.api_u = ctk.CTkEntry(f_selectors, width=80)
        self.api_u.pack(side="left", padx=5)

        ctk.CTkLabel(f_selectors, text="Vértice V:").pack(side="left", padx=2)
        self.api_v = ctk.CTkEntry(f_selectors, width=80)
        self.api_v.pack(side="left", padx=5)

        ctk.CTkLabel(f_selectors, text="Peso:").pack(side="left", padx=2)
        self.api_w = ctk.CTkEntry(f_selectors, width=80)
        self.api_w.pack(side="left", padx=5)

        f_grid = ctk.CTkFrame(parent, border_width=2, border_color="gray")
        f_grid.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkButton(f_grid, text="add-edge", command=lambda: self.execute_cli_action("add-edge")).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="rem-edge", command=lambda: self.execute_cli_action("rem-edge")).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="has-edge", command=lambda: self.execute_cli_action("has-edge")).grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="info", command=lambda: self.execute_cli_action("info")).grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(f_grid, text="degree (In/Out)", command=lambda: self.execute_cli_action("degree")).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="connected ?", command=lambda: self.execute_cli_action("connected")).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="show estrutura", command=lambda: self.execute_cli_action("show")).grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="export GEPHI", command=self.cmd_export_gephi).grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        for i in range(4):
            f_grid.columnconfigure(i, weight=1)

    # ============================================================
    # 4. TELA BUSCAS & CAMINHOS
    # ============================================================
    def setup_algorithms_screen(self, parent):
        f_alg = ctk.CTkFrame(parent, border_width=2, border_color="gray")
        f_alg.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(f_alg, text="ID Grafo:").grid(row=0, column=0, padx=5, pady=10)
        self.alg_id = ctk.CTkComboBox(f_alg, values=['graph1', 'graph2', 'graph3','graph_integrated'], state="readonly")
        
        self.alg_id.grid(row=0, column=1, padx=5, pady=10)

        ctk.CTkLabel(f_alg, text="Vértice Origem:").grid(row=0, column=2, padx=5, pady=10)
        self.alg_src = ctk.CTkEntry(f_alg, width=100)
        self.alg_src.grid(row=0, column=3, padx=5, pady=10)

        ctk.CTkLabel(f_alg, text="Vértice Destino:").grid(row=0, column=4, padx=5, pady=10)
        self.alg_dst = ctk.CTkEntry(f_alg, width=100)
        self.alg_dst.grid(row=0, column=5, padx=5, pady=10)

        ctk.CTkButton(f_alg, text="Executar BFS", command=lambda: self.run_traversal("bfs")).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_alg, text="Executar DFS", command=lambda: self.run_traversal("dfs")).grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_alg, text="Caminho Mínimo (Dijkstra)", command=lambda: self.run_traversal("shortest")).grid(row=1, column=4, columnspan=2, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_alg, text="Ordenação Topológica (topsort)", command=lambda: self.run_traversal("topsort")).grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_alg, text="Componentes Fortemente Conexos (scc)", command=lambda: self.run_traversal("scc")).grid(row=2, column=3, columnspan=3, padx=5, pady=5, sticky="ew")

    # ============================================================
    # 5. TELA REDES COMPLEXAS
    # ============================================================
    def setup_metrics_screen(self, parent):
        f_top = ctk.CTkFrame(parent)
        f_top.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(f_top, text="ID Grafo:").pack(side="left", padx=5)
        self.met_id = ctk.CTkComboBox(f_top, values=['graph1', 'graph2', 'graph3','graph_integrated'], state="readonly")
        self.met_id.pack(side="left", padx=5)

        ctk.CTkButton(f_top, text="Análise Completa (full-analysis)", command=self.cmd_full_analysis).pack(side="left", padx=10)

        f_grid = ctk.CTkFrame(parent, border_width=2, border_color="gray")
        f_grid.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkButton(f_grid, text="Centralidade de Grau", command=lambda: self.run_metric("degree-centrality")).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="Centralidade de Intermediação", command=lambda: self.run_metric("betweenness")).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="Centralidade de Proximidade", command=lambda: self.run_metric("closeness")).grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="Algoritmo PageRank", command=lambda: self.run_metric("pagerank")).grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(f_grid, text="Densidade da Rede", command=lambda: self.run_metric("density")).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="Coeficiente de Aglomeração", command=lambda: self.run_metric("clustering")).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="Assortatividade", command=lambda: self.run_metric("assortativity")).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="Detecção de Comunidades", command=lambda: self.run_metric("communities")).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(f_grid, text="Pontes de Conexão (bridging)", command=lambda: self.run_metric("bridging")).grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

        for i in range(2):
            f_grid.columnconfigure(i, weight=1)

    # ============================================================
    # 6. TELA PURENETWORKX & TESTES
    # ============================================================
    def setup_networkx_screen(self, parent):
        """Carrega a aba convertida de PureNetworkX (CTk)."""
        try:
            # Importação local para evitar crash se o módulo não existir
            from grafo.gui.tab_networkx_ctk import NetworkXTabCTk 
            
            # Instancia a aba passando o frame pai, o core e a função de print
            self.networkx_tab = NetworkXTabCTk(parent, self.app_core, self._safe_print)
            self.networkx_tab.frame.pack(fill="both", expand=True, padx=10, pady=10)
        except Exception as exc:
            ctk.CTkLabel(
                parent, 
                text=f"❌ Falha ao carregar o módulo PureNetworkX:\n{exc}", 
                text_color="red",
                font=("Helvetica", 14)
            ).pack(pady=20)

    # ============================================================
    # 7. TELA SOBRE
    # ============================================================
    def generate_qr_image(self) -> Optional[ImageTk.PhotoImage]:
        try:
            qr = qrcode.QRCode(box_size=8, border=2)
            qr.add_data(REPO_URL)
            qr.make(fit=True)
            img_pil = qr.make_image(fill_color="black", back_color="white")
            img_pil = img_pil.resize((200, 200), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img_pil)
            self._qr_photo = photo
            return photo
        except Exception as e:
            logging.warning(f"Falha ao gerar QR Code: {e}")
            return None

    def setup_about_screen(self, parent):
        main_frame = ctk.CTkFrame(parent)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        info_text = (
            "🏫 Projeto Trabalho Prático de Teoria de Grafos\n"
            "e Computabilidade\n\n"
            "🏛️ Faculdade: Pontifícia Universidade Católica de Minas Gerais - PUC MINAS\n"
            "📍 Campus: Coração Eucarístico\n"
            "👥 Alunos:\n"
            "   • Daniel Lucas Soares Madureira\n"
            "   • Gabriel da Silva Cassino\n"
            "   • Paulo Henrique Rodrigues Neves\n"
            "   • Vinicius Cezar Pereira Menezes\n"
            "👨‍🏫 Professor: Prof. Leonardo Vilela Cardoso\n"
            "📚 Turma: 31.32.101\n"
            "🎓 Graduação: Engenharia de Computação\n"
            "📅 Semestre: 2026/1\n"
        )
        ctk.CTkLabel(main_frame, text=info_text, justify="center").pack(pady=(0, 15))

        qr_photo = self.generate_qr_image()
        if qr_photo is not None:
            lbl_qr = ctk.CTkLabel(main_frame, image=qr_photo, text="")
            lbl_qr.pack(pady=10)

        lbl_url = ctk.CTkLabel(
            main_frame,
            text=f"📂 Repositório: {REPO_URL}",
            text_color="lightblue",
            cursor="hand2",
            font=("Helvetica", 12, "underline")
        )
        lbl_url.pack(pady=10)
        lbl_url.bind("<Button-1>", lambda e: webbrowser.open(REPO_URL))

        ctk.CTkLabel(
            main_frame,
            text="Clique no link acima para acessar o repositório no GitHub.",
            text_color="gray",
            font=("Helvetica", 10)
        ).pack(pady=(5, 0))

    # ============================================================
    # COMANDOS E EXECUÇÃO (mantidos inalterados)
    # ============================================================
    def execute_core_command(self, cmd_str):
        self.print_to_console(f"\n> {cmd_str}")
        if self.cli_core is None:
            self.print_to_console("⚠️ Erro: CLI Core não inicializado.")
            return

        buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buffer
        try:
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
        path = filedialog.askopenfilename(initialdir=PATH_D_CSV,filetypes=[("CSV Files", "*.csv")])
        if path:
            self.execute_core_command(f"load-csv {path}")

    def cmd_build_graphs(self):
        path = filedialog.askopenfilename(initialdir=PATH_D_CSV,filetypes=[("CSV Files", "*.csv")], title="Selecione o arquivo interacoes_reais.csv")
        if path:
            self.execute_core_command(f"build-graphs {path}")

    def cmd_export_gephi(self):
        g_id = self.api_graph_id.get().strip()
        if not g_id:
            messagebox.showwarning("Aviso", "Informe o ID do grafo na aba de campos superiores.")
            return
        path = filedialog.asksaveasfilename(initialfile= f"{g_id}.gexf",initialdir=PATH_D_GEXF,defaultextension=".gexf", filetypes=[("GEPHI Files", "*.gexf")])
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
            if w:
                cmd += f" {w}"
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


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================
if __name__ == "__main__":
    root = ctk.CTk()
    app = GraphUltimateGUI(root)
    root.mainloop()
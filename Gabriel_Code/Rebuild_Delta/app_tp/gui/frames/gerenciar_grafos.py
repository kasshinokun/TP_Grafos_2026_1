import os
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox

from filemanager import PATH_D_GEXF, PATH_D_CSV
from grafo.utils.gexf_parser import load_gexf
from miner import graph_builder


class ManageGraphsFrame(ctk.CTkFrame):
    """Frame para o módulo de Gerenciar Grafos."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.current_graph = None          # grafo atualmente carregado em runtime
        self.current_graph_name = None      # nome de exibição (ex.: nome do .gexf carregado)

        # Layout
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ==================== SIDEBAR ====================
        self.sidebar = ctk.CTkFrame(self, width=300)
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
        self.sidebar.grid_propagate(False)

        # Container rolável para a sidebar (padrão usado também em
        # api_primitiva.py e nas telas screen_home/about/settings)
        self.scrollable_sidebar = ctk.CTkScrollableFrame(
            self.sidebar,
            width=280,
            orientation="vertical"
        )
        self.scrollable_sidebar.pack(fill="both", expand=True, padx=5, pady=5)

        self.title_label = ctk.CTkLabel(
            self.scrollable_sidebar,
            text="Gerenciar Grafos",
            font=("Helvetica", 20, "bold")
        )
        self.title_label.pack(pady=(20, 10))

        # ---------------- Construção de grafos a partir de .csv ----------------
        self.csv_section_label = ctk.CTkLabel(
            self.scrollable_sidebar,
            text="Construção (./csv):",
            font=("Helvetica", 14, "bold")
        )
        self.csv_section_label.pack(pady=(10, 0))

        self.build_graphs_button = ctk.CTkButton(
            self.scrollable_sidebar,
            text="Construir grafos",
            command=self._on_build_graphs_click,
        )
        self.build_graphs_button.pack(fill="x", padx=15, pady=(5, 5))

        self.build_status_label = ctk.CTkLabel(
            self.scrollable_sidebar,
            text="Nenhum .csv processado ainda.",
            font=("Helvetica", 11),
            wraplength=250,
            justify="left",
        )
        self.build_status_label.pack(pady=(0, 15), padx=10)

        # ---------------- Carregar / Salvar grafo (.gexf) ----------------
        self.gexf_section_label = ctk.CTkLabel(
            self.scrollable_sidebar,
            text="Arquivo (./gexf):",
            font=("Helvetica", 14, "bold")
        )
        self.gexf_section_label.pack(pady=(10, 0))

        self.gexf_buttons_row = ctk.CTkFrame(self.scrollable_sidebar, fg_color="transparent")
        self.gexf_buttons_row.pack(fill="x", padx=15, pady=(5, 5))

        self.load_graph_button = ctk.CTkButton(
            self.gexf_buttons_row,
            text="Carregar grafo",
            command=self._on_load_graph_click,
        )
        self.load_graph_button.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.save_graph_button = ctk.CTkButton(
            self.gexf_buttons_row,
            text="Salvar grafo",
            command=self._on_save_graph_click,
        )
        self.save_graph_button.pack(side="left", expand=True, fill="x", padx=(4, 0))

        self.graph_status_label = ctk.CTkLabel(
            self.scrollable_sidebar,
            text="Nenhum grafo carregado.",
            font=("Helvetica", 11),
            wraplength=250,
            justify="left",
        )
        self.graph_status_label.pack(pady=(0, 15), padx=10)

        # ---------------- Edição (placeholders) ----------------
        self.edit_section_label = ctk.CTkLabel(
            self.scrollable_sidebar,
            text="Edição:",
            font=("Helvetica", 14, "bold")
        )
        self.edit_section_label.pack(pady=(10, 0))

        self._not_implemented_buttons = [
            ("Adicionar aresta", self._on_not_implemented_click),
            ("Remover aresta", self._on_not_implemented_click),
            ("Adicionar vértice", self._on_not_implemented_click),
            ("Remover vértice", self._on_not_implemented_click),
        ]
        for text, handler in self._not_implemented_buttons:
            btn = ctk.CTkButton(self.scrollable_sidebar, text=text, command=handler)
            btn.pack(fill="x", padx=15, pady=4)

        # ---------------- Inspeção ----------------
        self.inspect_section_label = ctk.CTkLabel(
            self.scrollable_sidebar,
            text="Inspeção:",
            font=("Helvetica", 14, "bold")
        )
        self.inspect_section_label.pack(pady=(15, 0))

        self.show_info_button = ctk.CTkButton(
            self.scrollable_sidebar,
            text="Mostrar Info",
            command=self._on_show_info_click,
        )
        self.show_info_button.pack(fill="x", padx=15, pady=4)

        self.show_structure_button = ctk.CTkButton(
            self.scrollable_sidebar,
            text="Mostrar estrutura",
            command=self._on_not_implemented_click,
        )
        self.show_structure_button.pack(fill="x", padx=15, pady=4)

        # ==================== ÁREA DE CONTEÚDO ====================
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.output_panel = self._build_output_panel(self.content)
        self.output_panel.grid(row=0, column=0, sticky="nsew")

        self._update_vertex_list()
        self._console_log("Pronto. Use 'Construir grafos' (a partir de um .csv) ou 'Carregar grafo' (a partir de um .gexf).")

    # ------------------------------------------------------------------
    # Construção do painel de saída: pseudo-console + listador de vértices
    # ------------------------------------------------------------------

    def _build_output_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")

        header = ctk.CTkLabel(
            panel, text="Gerenciamento de Grafos", font=("Helvetica", 16, "bold")
        )
        header.pack(anchor="w", pady=(0, 10))

        body = ctk.CTkFrame(panel, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Pseudo-console (saída textual das operações)
        console_label = ctk.CTkLabel(body, text="Console:", font=("Helvetica", 12, "bold"))
        console_label.pack(anchor="w")
        self.console_box = ctk.CTkTextbox(body, height=320, wrap="word", font=("Consolas", 12))
        self.console_box.pack(side="left", fill="both", expand=True, pady=(4, 0))
        self.console_box.configure(state="disabled")

        # Listagem de vértices do grafo atualmente carregado
        vertex_col = ctk.CTkFrame(body, fg_color="transparent", width=220)
        vertex_col.pack(side="left", fill="y", expand=False, padx=(10, 0))
        vertex_col.pack_propagate(False)

        vertex_label = ctk.CTkLabel(vertex_col, text="Vértices:", font=("Helvetica", 12, "bold"))
        vertex_label.pack(anchor="w")
        self.names_vertex_box = ctk.CTkTextbox(vertex_col, width=220, height=320, wrap="word")
        self.names_vertex_box.pack(fill="both", expand=True, pady=(4, 0))
        self.names_vertex_box.configure(state="disabled")

        return panel

    def _console_log(self, text: str):
        """Acrescenta uma linha (com timestamp) ao pseudo-console, sem
        apagar o histórico anterior, e rola até o final."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_box.configure(state="normal")
        self.console_box.insert("end", f"[{timestamp}] {text}\n")
        self.console_box.configure(state="disabled")
        self.console_box.see("end")

    def _update_vertex_list(self):
        self.names_vertex_box.configure(state="normal")
        self.names_vertex_box.delete("1.0", "end")
        if self.current_graph is None:
            self.names_vertex_box.insert("1.0", "Nenhum grafo carregado.")
        else:
            n = self.current_graph.get_vertex_count()
            labels = self.current_graph.vertex_labels
            for i in range(n):
                label = labels.get(i, i)
                self.names_vertex_box.insert("end", f"{i}: {label}\n")
        self.names_vertex_box.configure(state="disabled")

    # ------------------------------------------------------------------
    # Construir grafos (.csv -> 4 grafos .gexf)
    # ------------------------------------------------------------------

    def _on_build_graphs_click(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo .csv de interações",
            initialdir=PATH_D_CSV,  # root_path/csv
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
        )
        if not path:
            return

        filename = os.path.basename(path)
        self._console_log(f"Validando '{filename}'...")

        # 1) Valida e lê o CSV (formato actor,target,type)
        try:
            interactions = graph_builder.load_interactions_csv(path)
        except graph_builder.CSVValidationError as ex:
            self._console_log(f"❌ CSV inválido: {ex}")
            messagebox.showerror("CSV inválido", str(ex))
            return
        except Exception as ex:
            self._console_log(f"❌ Erro inesperado ao ler o CSV: {ex}")
            messagebox.showerror("Erro", f"Erro inesperado ao ler o CSV:\n{ex}")
            return

        self._console_log(f"✅ CSV válido — {len(interactions)} interação(ões) reconhecida(s).")

        # 2) Constrói os 4 grafos padrão (reuso de miner/graph_builder.py,
        # o mesmo módulo já usado pela tela de Mineração)
        try:
            graphs = graph_builder.build_all_graphs(interactions)
        except Exception as ex:
            self._console_log(f"❌ Falha ao construir os grafos: {ex}")
            messagebox.showerror("Erro", f"Falha ao construir os grafos:\n{ex}")
            return

        # 3) Exporta cada grafo para ./gexf
        base_name = os.path.splitext(filename)[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        names = {
            "graph1": "Grafo 1 (comentários)",
            "graph2": "Grafo 2 (fechamentos)",
            "graph3": "Grafo 3 (revisões/merges)",
            "graph_integrado": "Grafo integrado (ponderado)",
        }

        exported = {}
        for key, label in names.items():
            g = graphs.get(key)
            if g is None:
                continue
            out_filename = f"{key}_{base_name}_{timestamp}.gexf"
            out_path = os.path.join(PATH_D_GEXF, out_filename)
            try:
                g.export_to_gephi(out_path)
                exported[label] = (out_filename, g)
            except Exception as ex:
                self._console_log(f"⚠️ Falha ao exportar {label}: {ex}")

        if not exported:
            self._console_log("❌ Nenhum grafo pôde ser exportado.")
            messagebox.showerror("Erro", "Nenhum grafo pôde ser exportado.")
            return

        self._console_log(f"✅ {len(exported)} grafo(s) construído(s) a partir de '{filename}':")
        for label, (out_filename, g) in exported.items():
            self._console_log(
                f"   • {label}: {out_filename} "
                f"({g.get_vertex_count()} vértices, {g.get_edge_count()} arestas)"
            )

        self.build_status_label.configure(
            text=f"✅ {len(exported)} grafo(s) gerado(s) a partir de '{filename}'."
        )

        # Carrega automaticamente o grafo integrado em runtime, como
        # conveniência (mesmo padrão usado pela tela de Mineração).
        integrado = graphs.get("graph_integrado")
        if integrado is not None:
            self.current_graph = integrado
            self.current_graph_name = names["graph_integrado"]
            self.graph_status_label.configure(
                text=f"✅ {self.current_graph_name} carregado em runtime."
            )
            self._update_vertex_list()
            self._console_log(f"ℹ️ '{self.current_graph_name}' carregado automaticamente em runtime.")

    # ------------------------------------------------------------------
    # Carregar / Salvar grafo (.gexf)
    # ------------------------------------------------------------------

    def _on_load_graph_click(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo .gexf",
            initialdir=PATH_D_GEXF,  # root_path/gexf
            filetypes=[("GEXF", "*.gexf *.gexf.txt"), ("Todos", "*.*")],
        )
        if not path:
            return

        filename = os.path.basename(path)
        try:
            graph = load_gexf(path)
        except Exception as ex:
            self._console_log(f"❌ Erro ao carregar '{filename}': {ex}")
            self.graph_status_label.configure(text=f"❌ Erro ao carregar {filename}.")
            messagebox.showerror("Erro ao carregar grafo", str(ex))
            return

        self.current_graph = graph
        self.current_graph_name = filename
        self.graph_status_label.configure(
            text=f"✅ {filename}\n"
                 f"{graph.get_vertex_count()} nós, {graph.get_edge_count()} arestas."
        )
        self._update_vertex_list()

        # "Por enquanto sem visualização gráfica, somente uma notificação
        # no pseudo-console" — reusa a mesma rotina de "Mostrar Info".
        self._show_graph_info()

    def _on_save_graph_click(self):
        if self.current_graph is None:
            messagebox.showwarning("Aviso", "Nenhum grafo carregado para salvar.")
            return

        suggested_name = self.current_graph_name or "grafo.gexf"
        if not suggested_name.endswith(".gexf"):
            suggested_name = os.path.splitext(suggested_name)[0] + ".gexf"

        path = filedialog.asksaveasfilename(
            title="Salvar grafo como",
            initialdir=PATH_D_GEXF,  # root_path/gexf
            initialfile=suggested_name,
            defaultextension=".gexf",
            filetypes=[("GEXF", "*.gexf")],
        )
        if not path:
            return

        try:
            self.current_graph.export_to_gephi(path)
        except Exception as ex:
            self._console_log(f"❌ Erro ao salvar grafo: {ex}")
            messagebox.showerror("Erro ao salvar grafo", str(ex))
            return

        filename = os.path.basename(path)
        self._console_log(f"💾 Grafo salvo em: {filename}")
        self.current_graph_name = filename
        self.graph_status_label.configure(text=f"✅ {filename} (salvo).")

    # ------------------------------------------------------------------
    # Mostrar Info
    # ------------------------------------------------------------------

    def _on_show_info_click(self):
        if self.current_graph is None:
            messagebox.showwarning("Aviso", "Nenhum grafo carregado.")
            return
        self._show_graph_info()

    def _show_graph_info(self):
        """Mostra no pseudo-console as informações do grafo atualmente
        carregado em runtime. Reaproveitada tanto pelo botão 'Mostrar
        Info' quanto por 'Carregar grafo' (que dispara a mesma notificação
        logo após o carregamento)."""
        g = self.current_graph
        name = self.current_graph_name or "(sem nome)"

        n_vertices = g.get_vertex_count()
        n_edges = g.get_edge_count()
        connected = g.is_connected()
        complete = g.is_complete_graph()
        empty = g.is_empty_graph()

        self._console_log(f"Grafo {name} carregado com sucesso.")
        self._console_log(f"   • Quantidade de vértices: {n_vertices}")
        self._console_log(f"   • Quantidade de arestas: {n_edges}")
        self._console_log(f"   • Grafo conectado: {connected}")
        self._console_log(f"   • Grafo completo: {complete}")
        self._console_log(f"   • Grafo vazio: {empty}")

    # ------------------------------------------------------------------
    # Placeholders
    # ------------------------------------------------------------------

    def _on_not_implemented_click(self):
        self._console_log("Função não implementada\nEm desenvolvimento")
        messagebox.showinfo("Função não implementada", "Função não implementada\nEm desenvolvimento")

import os
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox

from filemanager import PATH_D_GEXF
from grafo.utils.gexf_parser import load_gexf
from grafo.utils import graph_structure
from grafo.networkx_pure.adapter import GraphAdapter
from grafo.networkx_pure import structure as nx_structure
from cli.cli_orchestrator import CliOrchestrator


class PrimitiveAPIFrame(ctk.CTkFrame):
    """Frame para o módulo de API Primitiva.

    Responsabilidade desta tela: expor diretamente as operações
    primitivas definidas em `grafo/graph/abstract_graph.py` (a "API
    Obrigatória" do TP) sobre um grafo carregado em runtime — diferente
    de `gerenciar_grafos.py`, que cuida da construção/IO de grafos
    (.csv -> .gexf, carregar/salvar), e de `seek_n_path.py`, que roda
    os algoritmos de alto nível (busca, caminhos, fluxo etc.).

    Cada frame mantém seu próprio `current_graph` em runtime — esse é
    o mesmo padrão usado em todas as telas do `screen_manager` (não há
    estado de grafo compartilhado entre frames).
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.current_graph = None          # grafo atualmente carregado em runtime
        self.current_graph_name = None      # nome de exibição (ex.: nome do .gexf carregado)

        # CLI experimental (./cli + ./event): um campo de texto nesta
        # tela aciona os mesmos comandos que os botões já acionam,
        # via a arquitetura EDA. O CliOrchestrator mantém seu próprio
        # EventOrchestrator com o grafo carregado em runtime — depois
        # de cada comando, `self.current_graph` é sincronizado a
        # partir dele (ver `_sync_graph_from_cli`), para que os botões
        # desta tela continuem funcionando sobre o grafo mais recente,
        # não importa se ele foi carregado pelo CLI ou pelos botões.
        self.cli = CliOrchestrator()
        self._cli_polling_started = False

        # Layout
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ==================== SIDEBAR ====================
        self.sidebar = ctk.CTkFrame(self, width=300)
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
        self.sidebar.grid_propagate(False)

        # Container rolável para a sidebar (necessário aqui pois esta
        # tela concentra mais controles que as demais: IO de .gexf +
        # campos de vértice + operações de edição + inspeção).
        self.scrollable_sidebar = ctk.CTkScrollableFrame(
            self.sidebar,
            width=280,
            orientation="vertical"
        )
        self.scrollable_sidebar.pack(fill="both", expand=True, padx=5, pady=5)

        self.title_label = ctk.CTkLabel(
            self.scrollable_sidebar,
            text="API Primitiva",
            font=("Helvetica", 20, "bold")
        )
        self.title_label.pack(pady=(20, 10))

        # ---------------- Carregamento / Salvamento de grafos ----------------
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

        # ---------------- Edição (operações primitivas sobre arestas) ----------------
        self.edit_section_label = ctk.CTkLabel(
            self.scrollable_sidebar,
            text="Edição (arestas):",
            font=("Helvetica", 14, "bold")
        )
        self.edit_section_label.pack(pady=(10, 0))

        # Campos de vértice U/V compartilhados pelas três operações de
        # aresta abaixo (add_edge / remove_edge / has_edge da API
        # obrigatória).
        self.edge_fields_row = ctk.CTkFrame(self.scrollable_sidebar, fg_color="transparent")
        self.edge_fields_row.pack(fill="x", padx=15, pady=(5, 5))

        self.vertex_u_label = ctk.CTkLabel(self.edge_fields_row, text="U:", font=("Helvetica", 12))
        self.vertex_u_label.pack(side="left")
        self.vertex_u_entry = ctk.CTkEntry(self.edge_fields_row, placeholder_text="índice", width=70)
        self.vertex_u_entry.pack(side="left", padx=(4, 12))

        self.vertex_v_label = ctk.CTkLabel(self.edge_fields_row, text="V:", font=("Helvetica", 12))
        self.vertex_v_label.pack(side="left")
        self.vertex_v_entry = ctk.CTkEntry(self.edge_fields_row, placeholder_text="índice", width=70)
        self.vertex_v_entry.pack(side="left", padx=(4, 0))

        self.edge_buttons_row = ctk.CTkFrame(self.scrollable_sidebar, fg_color="transparent")
        self.edge_buttons_row.pack(fill="x", padx=15, pady=(0, 5))

        self.add_edge_button = ctk.CTkButton(
            self.edge_buttons_row,
            text="Adicionar aresta",
            command=self._on_add_edge_click,
        )
        self.add_edge_button.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.remove_edge_button = ctk.CTkButton(
            self.edge_buttons_row,
            text="Remover aresta",
            command=self._on_remove_edge_click,
        )
        self.remove_edge_button.pack(side="left", expand=True, fill="x", padx=(4, 0))

        self.has_edge_button = ctk.CTkButton(
            self.scrollable_sidebar,
            text="Tem aresta? (U → V)",
            command=self._on_has_edge_click,
        )
        self.has_edge_button.pack(fill="x", padx=15, pady=(0, 10))

        # Operações ainda não suportadas por NENHUMA implementação atual
        # de AbstractGraph: o número de vértices é fixado na criação do
        # grafo (`__init__(self, num_vertices, ...)`), e não existe
        # add_vertex/remove_vertex em abstract_graph.py nem nas
        # subclasses concretas (adjacency_list_graph.py,
        # adjacency_matrix_graph.py, undirected_graph.py). Suportar
        # isso exigiria uma mudança na camada de dados, fora do escopo
        # desta tela — por isso o aviso é específico, não um placeholder
        # genérico de "não implementado".
        self.vertex_edit_buttons = [
            ("Adicionar vértice", self._on_vertex_edit_not_supported),
            ("Remover vértice", self._on_vertex_edit_not_supported),
        ]
        for text, handler in self.vertex_edit_buttons:
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
            command=self._on_show_structure_click,
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
        self._console_log("Pronto. Use 'Carregar grafo' para abrir um arquivo .gexf.")

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

        # --- Campo de comando CLI (./cli + ./event) ---
        # Experimental: aciona os mesmos comandos que os botões da
        # sidebar, digitados como texto (ex.: "bfs source=0 target=5",
        # "load filename=graph1.gexf"). Use "help" para listar todos
        # os comandos disponíveis.
        cli_row = ctk.CTkFrame(panel, fg_color="transparent")
        cli_row.pack(fill="x", pady=(8, 0))

        cli_label = ctk.CTkLabel(cli_row, text=">_", font=("Consolas", 14, "bold"))
        cli_label.pack(side="left", padx=(0, 6))

        self.cli_entry = ctk.CTkEntry(
            cli_row,
            placeholder_text='Comando CLI (ex.: bfs source=0 target=5, help)',
        )
        self.cli_entry.pack(side="left", fill="x", expand=True)
        self.cli_entry.bind("<Return>", self._on_cli_submit)

        self.cli_run_button = ctk.CTkButton(
            cli_row, text="Executar", width=90, command=self._on_cli_submit,
        )
        self.cli_run_button.pack(side="left", padx=(6, 0))

        self._start_cli_polling()

        return panel

    def _console_log(self, text: str):
        """Acrescenta uma linha (com timestamp) ao pseudo-console."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_box.configure(state="normal")
        self.console_box.insert("end", f"[{timestamp}] {text}\n")
        self.console_box.configure(state="disabled")
        self.console_box.see("end")

    # ------------------------------------------------------------------
    # Campo de comando CLI (./cli + ./event)
    # ------------------------------------------------------------------

    def _on_cli_submit(self, _event=None):
        """Lê o texto digitado no campo CLI, executa via
        `CliOrchestrator.execute` (que nunca lança exceção — qualquer
        erro de sintaxe/validação/execução já vem formatado como
        texto), mostra o comando e a resposta no console, e sincroniza
        `self.current_graph` com o que o CLI deixou carregado."""
        text = self.cli_entry.get().strip()
        if not text:
            return
        self.cli_entry.delete(0, "end")

        self._console_log(f"$ {text}")
        output = self.cli.execute(text, source="gui:api_primitiva")
        self._console_log(output)

        self._sync_graph_from_cli()

    def _sync_graph_from_cli(self):
        """Copia o grafo atualmente carregado dentro do
        `EventOrchestrator` do CLI para `self.current_graph` desta
        tela, e atualiza a lista de vértices — assim um `load
        filename=...` digitado no CLI fica imediatamente visível e
        utilizável pelos botões normais da sidebar (Mostrar Info,
        Mostrar estrutura, etc.), exatamente como se o arquivo tivesse
        sido carregado pelo botão "Carregar grafo"."""
        cli_graph = self.cli.event_orchestrator.current_graph
        if cli_graph is not self.current_graph:
            self.current_graph = cli_graph
            self.current_graph_name = self.cli.event_orchestrator.current_graph_name
            self._update_vertex_list()

    def _start_cli_polling(self, interval_ms: int = 200):
        """Inicia o ciclo de polling de resultados assíncronos do CLI
        (comandos como `run_floyd_warshall`, `build_graph_from_csv`,
        `run_tests`, registrados como assíncronos por padrão no
        EventOrchestrator). Roda na thread principal do Tkinter via
        `after`, então é seguro tocar `console_box` diretamente daqui
        — nenhum widget é tocado de dentro de uma worker thread."""
        if self._cli_polling_started:
            return
        self._cli_polling_started = True

        def _tick():
            output = self.cli.poll_async_results()
            if output:
                self._console_log(output)
                self._sync_graph_from_cli()
            self.after(interval_ms, _tick)

        self.after(interval_ms, _tick)

    def _update_vertex_list(self):
        """Atualiza a lista de vértices exibida na área de conteúdo."""
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

    def _refresh_graph_status(self):
        """Atualiza o rótulo de status com a contagem atual de vértices/
        arestas. Usado após operações de edição (add_edge/remove_edge),
        já que o número de arestas pode mudar sem que um novo arquivo
        seja carregado."""
        if self.current_graph is None:
            return
        name = self.current_graph_name or "(sem nome)"
        self.graph_status_label.configure(
            text=f"✅ {name}\n"
                 f"{self.current_graph.get_vertex_count()} nós, "
                 f"{self.current_graph.get_edge_count()} arestas."
        )

    # ------------------------------------------------------------------
    # Carregar / Salvar grafo (.gexf)
    # ------------------------------------------------------------------

    def _on_load_graph_click(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo .gexf",
            initialdir=PATH_D_GEXF,
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
        # Índices U/V do grafo anterior podem não existir no novo grafo.
        self.vertex_u_entry.delete(0, "end")
        self.vertex_v_entry.delete(0, "end")
        self._update_vertex_list()
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
            initialdir=PATH_D_GEXF,
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
    # Mostrar estrutura (matriz/lista de adjacência + heurísticas)
    # ------------------------------------------------------------------

    def _on_show_structure_click(self):
        """Exibe, no pseudo-console, a representação estrutural
        completa do grafo carregado: matriz de adjacência, lista de
        adjacência, sequência de graus e um resumo heurístico da
        topologia (regularidade, densidade, vértices isolados/fonte/
        sorvedouro, hub de maior grau).

        Reusa duas camadas novas, criadas para este botão:
        - `grafo.utils.graph_structure`: opera direto sobre
          AbstractGraph e formata matriz/lista/graus como texto.
        - `grafo.networkx_pure.structure`: opera sobre GraphAdapter e
          calcula as heurísticas estruturais (densidade, regularidade,
          classificação qualitativa da topologia).
        """
        if self.current_graph is None:
            messagebox.showwarning("Aviso", "Nenhum grafo carregado.")
            return

        g = self.current_graph
        name = self.current_graph_name or "(sem nome)"
        adapter = GraphAdapter(g)
        summary = nx_structure.structural_summary(adapter)

        self._console_log(f"📐 Estrutura de {name}:")
        self._console_log(f"   • Classificação: {summary['topology_classification']}")
        self._console_log(f"   • Densidade: {summary['density']:.4f}")
        self._console_log(f"   • Grafo regular: {summary['is_regular']}")

        if summary["max_degree_vertex"] is not None:
            label_max = g.vertex_labels.get(summary["max_degree_vertex"], summary["max_degree_vertex"])
            label_min = g.vertex_labels.get(summary["min_degree_vertex"], summary["min_degree_vertex"])
            self._console_log(
                f"   • Maior grau: {label_max} ({summary['max_degree_vertex']}), "
                f"grau total {summary['max_degree']}"
            )
            self._console_log(
                f"   • Menor grau: {label_min} ({summary['min_degree_vertex']}), "
                f"grau total {summary['min_degree']}"
            )

        self._log_vertex_group("Vértices isolados", summary["isolated_vertices"], g)
        self._log_vertex_group("Vértices fonte (sem entrada)", summary["source_vertices"], g)
        self._log_vertex_group("Vértices sorvedouro (sem saída)", summary["sink_vertices"], g)

        self._console_log("")
        self._console_log("— Sequência de graus —")
        self._console_log(graph_structure.format_degree_sequence(g))

        self._console_log("")
        self._console_log("— Lista de adjacência —")
        self._console_log(graph_structure.format_adjacency_list(g))

        self._console_log("")
        self._console_log("— Matriz de adjacência —")
        self._console_log(graph_structure.format_adjacency_matrix(g))

    def _log_vertex_group(self, title: str, vertices, g):
        """Loga uma lista de vértices (ex.: isolados, fonte, sorvedouro)
        de forma compacta, evitando uma linha vazia/poluída quando o
        grupo não tiver nenhum vértice."""
        if not vertices:
            self._console_log(f"   • {title}: nenhum")
            return
        labels = ", ".join(
            f"{g.vertex_labels.get(v, v)} ({v})" for v in vertices
        )
        self._console_log(f"   • {title} ({len(vertices)}): {labels}")

    # ------------------------------------------------------------------
    # Edição: operações primitivas sobre arestas
    # (add_edge / remove_edge / has_edge — API Obrigatória do TP)
    # ------------------------------------------------------------------

    def _read_vertex_indices(self):
        """Lê e converte os índices digitados em U/V. Levanta ValueError
        com mensagem amigável se algum campo estiver vazio ou não for
        um inteiro — a validação de limites (vértice existe?) e de
        laços (u == v) fica a cargo de check_edge/check_vertex, do
        próprio backend (AbstractGraph), para não duplicar regras."""
        raw_u = self.vertex_u_entry.get().strip()
        raw_v = self.vertex_v_entry.get().strip()
        if not raw_u or not raw_v:
            raise ValueError("Informe os índices dos vértices U e V.")
        try:
            return int(raw_u), int(raw_v)
        except ValueError:
            raise ValueError("Os campos U e V devem conter números inteiros.")

    def _on_add_edge_click(self):
        if self.current_graph is None:
            messagebox.showwarning("Aviso", "Nenhum grafo carregado.")
            return
        try:
            u, v = self._read_vertex_indices()
            self.current_graph.add_edge(u, v)
        except (ValueError, IndexError) as ex:
            self._console_log(f"❌ Não foi possível adicionar a aresta: {ex}")
            messagebox.showerror("Erro ao adicionar aresta", str(ex))
            return

        self._console_log(f"➕ add_edge({u}, {v}) — aresta {u} → {v} adicionada (operação idempotente).")
        self._refresh_graph_status()

    def _on_remove_edge_click(self):
        if self.current_graph is None:
            messagebox.showwarning("Aviso", "Nenhum grafo carregado.")
            return
        try:
            u, v = self._read_vertex_indices()
            self.current_graph.remove_edge(u, v)
        except (ValueError, IndexError) as ex:
            self._console_log(f"❌ Não foi possível remover a aresta: {ex}")
            messagebox.showerror("Erro ao remover aresta", str(ex))
            return

        self._console_log(f"➖ remove_edge({u}, {v}) — aresta {u} → {v} removida (caso existisse).")
        self._refresh_graph_status()

    def _on_has_edge_click(self):
        """Verifica a existência de aresta entre dois vértices usando
        has_edge(u, v) do grafo carregado em runtime."""
        if self.current_graph is None:
            messagebox.showwarning("Aviso", "Nenhum grafo carregado.")
            return
        try:
            u, v = self._read_vertex_indices()
            exists = self.current_graph.has_edge(u, v)
        except (ValueError, IndexError) as ex:
            self._console_log(f"❌ Não foi possível verificar a aresta: {ex}")
            messagebox.showerror("Erro ao verificar aresta", str(ex))
            return

        resultado = "SIM" if exists else "NÃO"
        self._console_log(f"🔎 has_edge({u}, {v}) → {resultado}")
        messagebox.showinfo("Tem aresta?", f"Aresta {u} → {v}: {resultado}")

    def _on_vertex_edit_not_supported(self):
        """Adicionar/remover vértice não é suportado por nenhuma
        implementação atual de AbstractGraph: o número de vértices é
        fixado na criação do grafo. Suportar isso exigiria mudanças na
        camada de dados (grafo/graph/*.py), fora do escopo desta tela."""
        self._console_log(
            "Adicionar/remover vértice ainda não é suportado pela estrutura "
            "de dados do grafo (número de vértices é fixo na criação)."
        )
        messagebox.showinfo(
            "Funcionalidade não suportada pela estrutura atual",
            "Nenhuma implementação de grafo do projeto (lista de adjacência, "
            "matriz de adjacência ou não direcionado) permite inserir ou "
            "remover vértices após a criação — o número de vértices é fixo.\n\n"
            "Adicionar esse suporte exigiria alterar a camada de dados em "
            "grafo/graph/*.py, o que está fora do escopo desta tela."
        )

    # ------------------------------------------------------------------
    # Placeholders genéricos
    # ------------------------------------------------------------------

    def _on_not_implemented_click(self):
        self._console_log("Função não implementada\nEm desenvolvimento")
        messagebox.showinfo("Função não implementada", "Função não implementada\nEm desenvolvimento")

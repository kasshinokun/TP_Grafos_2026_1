"""Tela de métricas — calcula e exibe as 11 métricas de redes complexas."""
import customtkinter as ctk
import queue
from tkinter import filedialog, messagebox
from typing import Optional, Callable
from gui.screen_base import BaseScreen
from gui.metrics_panel import MetricsPanel
from gui.graph_canvas import GraphCanvas
from gui.workers import GraphWorker
from grafo.networkx_pure import centrality, structure, communities
from grafo.networkx_pure.centrality import _bfs_distances
from filemanager import PATH_D_GEXF


class MetricsScreen(BaseScreen):
    """Tela dedicada ao cálculo e visualização das 11 métricas."""

    def __init__(self, master,
                 on_back: Optional[Callable] = None,
                 on_colors_computed: Optional[Callable] = None,
                 on_load_gexf: Optional[Callable] = None,
                 **kwargs):
        self.adapter = None
        self.on_load_gexf = on_load_gexf
        self.worker: Optional[GraphWorker] = None
        self.result_queue = queue.Queue()
        self.on_colors_computed = on_colors_computed  # callback p/ colorir canvas
        self.canvas: Optional[GraphCanvas] = None
        self.zoom_slider: Optional[ctk.CTkSlider] = None
        super().__init__(
            master,
            title="📊 Métricas de Redes Complexas",
            subtitle="11 métricas divididas em Centralidade · Estrutura · Comunidade",
            on_back=on_back,
            **kwargs
        )
        self._poll_queue()

    def _build_content(self):
        # Painel esquerdo — botões de cálculo
        left = ctk.CTkFrame(self, width=220)
        left.pack(side="left", fill="y", padx=6, pady=6)
        left.pack_propagate(False)

        # Ações de grafo (Carregar GEXF · Exportar Gephi · Recalcular Layout)
        ctk.CTkButton(left, text="📂 Carregar GEXF",
                      command=self._do_load_gexf, anchor="w"
                      ).pack(fill="x", padx=10, pady=(12, 2))
        self.btn_export = ctk.CTkButton(left, text="💾 Exportar Gephi",
                      command=self._export_gephi, state="disabled", anchor="w")
        self.btn_export.pack(fill="x", padx=10, pady=2)
        self.btn_relayout = ctk.CTkButton(left, text="🔄 Recalcular Layout",
                      command=self._relayout, state="disabled", anchor="w")
        self.btn_relayout.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(left, text="Centralidade",
                     font=("Arial", 12, "bold")).pack(pady=(12, 4), anchor="w", padx=10)

        self._buttons = []
        for label, cmd in [
            ("📊 Degree Centrality",  lambda: self._run(self._calc_degree)),
            ("📈 PageRank",           lambda: self._run(self._calc_pagerank)),
            ("🌉 Betweenness",        lambda: self._run(self._calc_betweenness)),
            ("🎯 Closeness",          lambda: self._run(self._calc_closeness)),
        ]:
            b = ctk.CTkButton(left, text=label, state="disabled",
                              command=cmd, anchor="w")
            b.pack(fill="x", padx=10, pady=2)
            self._buttons.append(b)

        ctk.CTkLabel(left, text="Estrutura",
                     font=("Arial", 12, "bold")).pack(pady=(14, 4), anchor="w", padx=10)

        b = ctk.CTkButton(left, text="🔗 Densidade · Clustering · Assort.",
                          state="disabled",
                          command=lambda: self._run(self._calc_structure),
                          anchor="w")
        b.pack(fill="x", padx=10, pady=2)
        self._buttons.append(b)

        ctk.CTkLabel(left, text="Comunidade",
                     font=("Arial", 12, "bold")).pack(pady=(14, 4), anchor="w", padx=10)

        for label, cmd in [
            ("👥 Label Propagation",  lambda: self._run(self._calc_communities)),
            ("🌐 Bridging Ties",      lambda: self._run(self._calc_bridging)),
        ]:
            b = ctk.CTkButton(left, text=label, state="disabled",
                              command=cmd, anchor="w")
            b.pack(fill="x", padx=10, pady=2)
            self._buttons.append(b)

        self.lbl_status = ctk.CTkLabel(left, text="Carregue um grafo primeiro",
                                       text_color="#888", wraplength=190,
                                       font=("Arial", 10))
        self.lbl_status.pack(pady=(20, 0), padx=10, anchor="w")

        # Painel central — grafo (igual à tela de Métricas do v1: ao lado
        # do microconsole de métricas), com controle de zoom (scroll ou slider)
        center = ctk.CTkFrame(self)
        center.pack(side="left", fill="both", expand=True, padx=6, pady=6)

        toolbar = ctk.CTkFrame(center, height=36, fg_color="#1A1A2E")
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        ctk.CTkLabel(
            toolbar, text="🔍 Zoom", text_color="#AAA", font=("Arial", 10)
        ).pack(side="left", padx=(10, 4), pady=4)
        self.zoom_slider = ctk.CTkSlider(
            toolbar, from_=0.2, to=4.0, number_of_steps=38, width=140,
            command=self._on_zoom_slider)
        self.zoom_slider.set(1.0)
        self.zoom_slider.pack(side="left", padx=4, pady=4)

        self.canvas_container, self.canvas = GraphCanvas.with_scrollbars(
            center, adapter=None,
            on_zoom_change=self._sync_zoom_slider,
            bg="#F5F5F5", highlightthickness=0)
        self.canvas_container.pack(fill="both", expand=True)
        self.canvas.bind("<<NodeSelected>>", self._on_node_selected)

        # Painel direito — resultados (microconsole de métricas)
        self.panel = MetricsPanel(self, width=360)
        self.panel.pack(side="left", fill="y", expand=False, padx=6, pady=6)
        self.panel.pack_propagate(False)

    def _on_zoom_slider(self, value):
        if self.canvas:
            self.canvas.set_zoom_level(float(value))

    def _sync_zoom_slider(self, zoom_level: float):
        """Mantém o slider sincronizado quando o zoom é feito via scroll."""
        if self.zoom_slider:
            self.zoom_slider.set(zoom_level)

    def _on_node_selected(self, _event):
        if not self.canvas or not self.canvas.adapter:
            return
        node = self.canvas.get_selected_node()
        if node is not None:
            label = self.canvas.adapter._g.vertex_labels.get(node, str(node))
            in_d = self.canvas.adapter.in_degree(node)
            out_d = self.canvas.adapter.out_degree(node)
            self.lbl_status.configure(
                text=f"Selecionado: {label} | in={in_d} out={out_d}")

    # ------------------------------------------------------------------

    def load_adapter(self, adapter):
        self.adapter = adapter
        for b in self._buttons:
            b.configure(state="normal")
        self.btn_export.configure(state="normal")
        self.btn_relayout.configure(state="normal")
        n = adapter.number_of_nodes()
        e = adapter.number_of_edges()
        self.lbl_status.configure(text=f"Grafo: {n} nós · {e} arestas")
        self.panel.clear_all()
        if self.canvas:
            self.canvas.load_adapter(adapter)
        if self.zoom_slider:
            self.zoom_slider.set(1.0)

    def set_node_colors(self, colors: dict):
        """Aplica cores por nó (ex.: por comunidade) no grafo desta tela."""
        if self.canvas:
            self.canvas.set_node_colors(colors)

    def _do_load_gexf(self):
        """Delega o carregamento de GEXF para a MainWindow (mesma lógica
        usada na tela Grafo), que distribui o adapter para todas as telas."""
        if self.on_load_gexf:
            self.on_load_gexf()

    def _relayout(self):
        if self.adapter and self.canvas:
            self.canvas.load_adapter(self.adapter)
            if self.zoom_slider:
                self.zoom_slider.set(1.0)

    def _export_gephi(self):
        if not self.adapter:
            return
        path = filedialog.asksaveasfilename(
            title="Exportar para Gephi",
            initialdir=PATH_D_GEXF,  # root_path/gexf
            defaultextension=".gexf",
            filetypes=[("GEXF", "*.gexf")])
        if not path:
            return
        try:
            self.adapter._g.export_to_gephi(path)
            self.lbl_status.configure(text=f"💾 Exportado: {path}")
        except Exception as ex:
            messagebox.showerror("Erro ao exportar", str(ex))

    def _run(self, task):
        if not self.adapter:
            return
        if self.worker and self.worker.is_alive():
            self.lbl_status.configure(text="⏳ Aguarde...")
            return
        self.lbl_status.configure(text="⏳ Calculando...")
        for b in self._buttons:
            b.configure(state="disabled")

        def on_done(result, error=None):
            self.result_queue.put(('done', result, error))

        self.worker = GraphWorker(task=task, on_complete=on_done)
        self.worker.start()

    def _poll_queue(self):
        try:
            while True:
                _, result, error = self.result_queue.get_nowait()
                for b in self._buttons:
                    b.configure(state="normal")
                if error:
                    self.lbl_status.configure(text=f"❌ {error}")
                else:
                    self.lbl_status.configure(text="✅ Concluído")
                    self._dispatch(result)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    def _dispatch(self, result):
        if not result:
            return
        labels = self.adapter._g.vertex_labels
        t = result.get('type')
        if t == 'degree':
            self.panel.show_degree_centrality(result['data'], labels)
        elif t == 'pagerank':
            self.panel.show_pagerank(result['data'], labels)
        elif t == 'betweenness':
            self.panel.show_betweenness(result['data'], labels)
        elif t == 'closeness':
            self.panel.show_closeness(result['data'], labels)
        elif t == 'structure':
            self.panel.show_structure_metrics(**{k: v for k, v in result.items() if k != 'type'})
        elif t == 'communities':
            self.panel.show_communities(result['communities'], result['modularity'], labels)
            palette = ["#4A90E2","#E74C3C","#2ECC71","#F39C12","#9B59B6","#1ABC9C"]
            colors = {n: palette[i % len(palette)]
                      for i, comm in enumerate(result['communities']) for n in comm}
            self.set_node_colors(colors)
            if self.on_colors_computed:
                self.on_colors_computed(colors)
        elif t == 'bridging':
            self.panel.show_bridging_ties(result['data'], labels)

    # --- tarefas ---
    def _calc_degree(self):
        return {'type': 'degree', 'data': centrality.degree_centrality(self.adapter)}

    def _calc_pagerank(self):
        return {'type': 'pagerank', 'data': centrality.pagerank(self.adapter)}

    def _calc_betweenness(self):
        return {'type': 'betweenness', 'data': centrality.betweenness_centrality(self.adapter)}

    def _calc_closeness(self):
        return {'type': 'closeness', 'data': centrality.closeness_centrality(self.adapter)}

    def _calc_structure(self):
        nodes = self.adapter.nodes()
        max_d = total = count = 0
        for s in nodes:
            for v, d in _bfs_distances(self.adapter, s, directed=False).items():
                if d > 0:
                    max_d = max(max_d, d); total += d; count += 1
        return {
            'type': 'structure',
            'density': structure.density(self.adapter),
            'avg_clustering': structure.average_clustering(self.adapter),
            'assortativity': structure.assortativity(self.adapter),
            'diameter': max_d,
            'avg_path': total / count if count else 0.0,
        }

    def _calc_communities(self):
        comms = communities.label_propagation_communities(self.adapter)
        return {'type': 'communities', 'communities': comms,
                'modularity': communities.modularity(self.adapter, comms)}

    def _calc_bridging(self):
        return {'type': 'bridging', 'data': communities.bridging_ties(self.adapter)}

"""Tela de visualização do grafo."""
import customtkinter as ctk
from typing import Optional, Callable
from gui.screen_base import BaseScreen
from gui.graph_canvas import GraphCanvas


class GraphScreen(BaseScreen):
    """Tela que exibe o canvas do grafo com controles de layout."""

    def __init__(self, master,
                 on_back: Optional[Callable] = None,
                 on_load_gexf: Optional[Callable] = None,
                 **kwargs):
        self.on_load_gexf = on_load_gexf
        self.canvas: Optional[GraphCanvas] = None
        self.zoom_slider: Optional[ctk.CTkSlider] = None
        super().__init__(
            master,
            title="🕸️ Visualização do Grafo",
            subtitle="Layout force-directed interativo — arraste nós, "
                     "zoom com scroll/slider/botões, navegue com as barras de rolagem",
            on_back=on_back,
            **kwargs
        )

    def _build_content(self):
        # Barra de ferramentas
        toolbar = ctk.CTkFrame(self, height=44, fg_color="#1A1A2E")
        toolbar.pack(fill="x", padx=0, pady=0)
        toolbar.pack_propagate(False)

        ctk.CTkButton(
            toolbar, text="📂 Carregar GEXF", width=150,
            command=self._do_load
        ).pack(side="left", padx=8, pady=6)

        ctk.CTkButton(
            toolbar, text="🔄 Recalcular Layout", width=160,
            command=self._relayout
        ).pack(side="left", padx=4, pady=6)

        self.lbl_info = ctk.CTkLabel(
            toolbar, text="Nenhum grafo carregado",
            text_color="#888", font=("Arial", 11))
        self.lbl_info.pack(side="left", padx=12, pady=6)

        self.lbl_node = ctk.CTkLabel(
            toolbar, text="", text_color="#AAA", font=("Arial", 10))
        self.lbl_node.pack(side="right", padx=12, pady=6)

        ctk.CTkLabel(
            toolbar, text="🔍 Zoom", text_color="#AAA", font=("Arial", 10)
        ).pack(side="right", padx=(12, 4), pady=6)
        self.zoom_slider = ctk.CTkSlider(
            toolbar, from_=0.2, to=4.0, number_of_steps=38, width=140,
            command=self._on_zoom_slider)
        self.zoom_slider.set(1.0)
        self.zoom_slider.pack(side="right", padx=4, pady=6)

        # Canvas principal (com scrollbars + botões de zoom embutidos)
        self.canvas_container, self.canvas = GraphCanvas.with_scrollbars(
            self, adapter=None,
            on_zoom_change=self._sync_zoom_slider,
            bg="#F5F5F5", highlightthickness=0)
        self.canvas_container.pack(fill="both", expand=True)
        self.canvas.bind("<<NodeSelected>>", self._on_node_selected)

    def _on_zoom_slider(self, value):
        if self.canvas:
            self.canvas.set_zoom_level(float(value))

    def _sync_zoom_slider(self, zoom_level: float):
        """Mantém o slider sincronizado quando o zoom é feito via scroll."""
        if self.zoom_slider:
            self.zoom_slider.set(zoom_level)

    def _do_load(self):
        if self.on_load_gexf:
            self.on_load_gexf()

    def _relayout(self):
        if self.canvas and self.canvas.adapter:
            self.canvas.load_adapter(self.canvas.adapter)

    def load_adapter(self, adapter):
        """Chamado pela MainWindow após carregar um grafo."""
        if self.canvas:
            self.canvas.load_adapter(adapter)
            n = adapter.number_of_nodes()
            e = adapter.number_of_edges()
            self.lbl_info.configure(text=f"{n} nós · {e} arestas")
        if self.zoom_slider:
            self.zoom_slider.set(1.0)

    def set_node_colors(self, colors: dict):
        if self.canvas:
            self.canvas.set_node_colors(colors)

    def _on_node_selected(self, _event):
        if not self.canvas or not self.canvas.adapter:
            return
        node = self.canvas.get_selected_node()
        if node is not None:
            label = self.canvas.adapter._g.vertex_labels.get(node, str(node))
            in_d  = self.canvas.adapter.in_degree(node)
            out_d = self.canvas.adapter.out_degree(node)
            self.lbl_node.configure(
                text=f"Selecionado: {label}  |  in={in_d}  out={out_d}")

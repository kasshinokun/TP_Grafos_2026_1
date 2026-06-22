"""Canvas interativo com layout force-directed.

Inclui zoom (scroll do mouse, slider externo ou botões +/- embutidos) e
navegação via scrollbars horizontal/vertical, que aparecem automaticamente
quando o grafo desenhado (após zoom) excede a área visível do canvas.
"""
import customtkinter as ctk
import math
import random
from typing import Dict, Tuple, Optional
from viz.force_directed import ForceDirectedLayout


class GraphCanvas(ctk.CTkCanvas):
    """Canvas que renderiza grafos com layout force-directed.

    Pode ser criado com adapter=None (estado vazio inicial).
    Chame load_adapter(adapter) após carregar um grafo.

    Para obter scrollbars + botões de zoom embutidos automaticamente,
    prefira instanciar via `GraphCanvas.with_scrollbars(parent, ...)`
    em vez do construtor direto — veja o docstring do classmethod.
    """

    # Margem (em pixels de tela) deixada ao redor do grafo dentro da
    # scrollregion, para que nós/labels não fiquem colados na borda
    # quando o usuário rola até o fim.
    SCROLL_MARGIN = 60

    def __init__(self, master, adapter=None, on_zoom_change=None, **kwargs):
        super().__init__(master, **kwargs)
        self.adapter = adapter
        self.layout: Optional[ForceDirectedLayout] = None
        self.positions: Dict[int, Tuple[float, float]] = {}
        self.selected_node: Optional[int] = None
        self.node_colors: Dict[int, str] = {}
        self.node_radius = 12
        self._graph_bounds = None

        # `scale` é o valor efetivo usado para desenhar (base_scale * zoom_level).
        self.scale = 1.0
        self.base_scale = 1.0      # escala calculada para enquadrar o grafo (fit)
        self.zoom_level = 1.0      # fator de zoom relativo ao fit (1.0 = 100%)
        self.min_zoom = 0.2
        self.max_zoom = 4.0
        self.zoom_step = 1.2       # fator usado por zoom_in()/zoom_out() e pelos botões +/-
        self.offset_x = 0
        self.offset_y = 0

        # Callback opcional chamado quando o zoom muda (scroll do mouse,
        # botões +/- embutidos), usado para manter um slider externo
        # sincronizado.
        self.on_zoom_change = on_zoom_change

        self._setup_bindings()

        # Só computa layout se já tiver adapter válido
        if adapter is not None:
            self._init_layout()

    # ------------------------------------------------------------------
    # Fábrica conveniente: canvas + scrollbars + botões de zoom embutidos
    # ------------------------------------------------------------------

    @classmethod
    def with_scrollbars(cls, master, adapter=None, on_zoom_change=None,
                         show_zoom_buttons: bool = True, **kwargs):
        """Cria o canvas já encapsulado em um frame com scrollbars
        horizontal/vertical e (opcionalmente) botões de zoom +/- no
        canto inferior direito.

        Retorna (container, canvas):
        - `container` é o widget que deve ser empacotado/posicionado
          no layout do chamador (ex.: `container.pack(fill="both", expand=True)`).
        - `canvas` é a instância de GraphCanvas, com toda a API usual
          (`load_adapter`, `set_node_colors`, `set_zoom_level`,
          `get_selected_node`, evento `<<NodeSelected>>`, etc.) — é o
          mesmo objeto que antes era criado e empacotado diretamente.

        As scrollbars ficam habilitadas o tempo todo, mas só têm efeito
        prático quando o conteúdo desenhado (após zoom) excede a área
        visível; quando o grafo cabe inteiro na viewport elas
        permanecem com a "alça" ocupando 100% do espaço (sem navegação
        necessária).
        """
        container = ctk.CTkFrame(master, fg_color="transparent")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        canvas = cls(container, adapter=adapter, on_zoom_change=on_zoom_change, **kwargs)
        canvas.grid(row=0, column=0, sticky="nsew")

        v_scroll = ctk.CTkScrollbar(container, orientation="vertical", command=canvas.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll = ctk.CTkScrollbar(container, orientation="horizontal", command=canvas.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        canvas._scrollbars = (h_scroll, v_scroll)

        if show_zoom_buttons:
            canvas._build_zoom_buttons(container)

        return container, canvas

    def _build_zoom_buttons(self, container):
        """Cria os botões de zoom +/- como um pequeno painel flutuante
        sobre o canto inferior direito do canvas (usando `place`, então
        não interfere no grid do container)."""
        zoom_box = ctk.CTkFrame(container, fg_color="#222233", corner_radius=8)
        # Ancorado ao canto inferior direito do canvas, com uma margem
        # para não colar na scrollbar vertical.
        zoom_box.place(in_=self, relx=1.0, rely=1.0, x=-14, y=-14, anchor="se")

        ctk.CTkButton(
            zoom_box, text="−", width=28, height=28, font=("Arial", 16, "bold"),
            command=self.zoom_out,
        ).pack(side="left", padx=(4, 2), pady=4)
        ctk.CTkButton(
            zoom_box, text="+", width=28, height=28, font=("Arial", 16, "bold"),
            command=self.zoom_in,
        ).pack(side="left", padx=(2, 4), pady=4)
        self._zoom_box = zoom_box

    # ------------------------------------------------------------------
    # Layout / dados
    # ------------------------------------------------------------------

    def _init_layout(self):
        """Inicializa o layout force-directed com o adapter atual."""
        self.layout = ForceDirectedLayout(self.adapter)
        self.compute_layout()

    def load_adapter(self, adapter):
        """Carrega um novo adapter e recalcula o layout."""
        self.adapter = adapter
        self.node_colors = {}
        self.selected_node = None
        self.zoom_level = 1.0
        self._init_layout()

    def _setup_bindings(self):
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<MouseWheel>", self._on_zoom)
        self.bind("<Button-4>", self._on_zoom)   # Linux scroll up
        self.bind("<Button-5>", self._on_zoom)   # Linux scroll down
        # Pan do canvas com o botão do meio do mouse (não interfere no
        # arraste de nós, que usa o botão esquerdo / <B1-Motion>).
        self.bind("<ButtonPress-2>", self._on_pan_start)
        self.bind("<B2-Motion>", self._on_pan_move)
        # Recalcula o enquadramento inicial quando o widget é
        # redimensionado (ex.: janela maximizada).
        self.bind("<Configure>", self._on_resize)

    def compute_layout(self, iterations: int = 100):
        """Computa layout force-directed e redesenha."""
        if self.adapter is None or self.layout is None:
            return
        self.positions = self.layout.compute(iterations=iterations)
        self._center_layout()
        self.redraw()
        self._center_view()

    def _center_layout(self):
        """Calcula a escala de enquadramento (fit) do grafo na viewport
        atual. `offset_x/offset_y` passam a ser fixos em relação ao
        grafo (não mais recalculados para centralizar visualmente a
        cada redraw) — a centralização visual agora é responsabilidade
        do scroll nativo (`_center_view`), o que permite navegar pelo
        conteúdo quando o zoom o torna maior que a viewport."""
        if not self.positions:
            return
        xs = [p[0] for p in self.positions.values()]
        ys = [p[1] for p in self.positions.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        self._graph_bounds = (min_x, min_y, max_x, max_y)

        canvas_w = self.winfo_width() or 800
        canvas_h = self.winfo_height() or 600

        graph_w = max_x - min_x
        graph_h = max_y - min_y

        self.base_scale = min(
            (canvas_w - 2 * self.SCROLL_MARGIN) / max(graph_w, 1),
            (canvas_h - 2 * self.SCROLL_MARGIN) / max(graph_h, 1)
        )
        self.scale = self.base_scale * self.zoom_level
        # Deslocamento fixo: apenas traz o grafo para coordenadas
        # positivas, com uma margem — não depende do tamanho do canvas,
        # então não recentraliza sozinho a cada zoom (isso cabe ao
        # scroll nativo via scrollregion).
        self.offset_x = self.SCROLL_MARGIN - min_x * self.scale
        self.offset_y = self.SCROLL_MARGIN - min_y * self.scale

    def _content_size(self) -> Tuple[float, float]:
        """Largura/altura do conteúdo desenhado (grafo escalado +
        margens), usado tanto para o scrollregion quanto para decidir
        o deslocamento de centralização inicial."""
        if not self._graph_bounds:
            return (0.0, 0.0)
        min_x, min_y, max_x, max_y = self._graph_bounds
        w = (max_x - min_x) * self.scale + 2 * self.SCROLL_MARGIN
        h = (max_y - min_y) * self.scale + 2 * self.SCROLL_MARGIN
        return (w, h)

    def _update_scrollregion(self):
        """Atualiza a scrollregion do Canvas nativo conforme o
        bounding box atual do grafo (já escalado pelo zoom). Quando o
        conteúdo é menor que a viewport, a scrollregion fica do
        tamanho da própria viewport (sem espaço de navegação extra)."""
        content_w, content_h = self._content_size()
        canvas_w = self.winfo_width() or 800
        canvas_h = self.winfo_height() or 600
        region_w = max(content_w, canvas_w)
        region_h = max(content_h, canvas_h)
        self.configure(scrollregion=(0, 0, region_w, region_h))

    def _center_view(self):
        """Centraliza a posição inicial do scroll para que o grafo
        apareça centralizado na viewport, mesmo usando scrollregion
        nativo (chamado após carregar um grafo ou recalcular layout)."""
        content_w, content_h = self._content_size()
        canvas_w = self.winfo_width() or 800
        canvas_h = self.winfo_height() or 600
        if content_w <= canvas_w:
            self.xview_moveto(0.0)
        else:
            frac_x = max(0.0, (content_w - canvas_w) / 2 / content_w)
            self.xview_moveto(frac_x)
        if content_h <= canvas_h:
            self.yview_moveto(0.0)
        else:
            frac_y = max(0.0, (content_h - canvas_h) / 2 / content_h)
            self.yview_moveto(frac_y)

    def _on_resize(self, _event=None):
        """Quando o canvas é redimensionado (ex.: janela maximizada) e
        ainda não há zoom manual aplicado, recalcula o enquadramento
        para continuar preenchendo bem a área disponível."""
        if not self.positions:
            return
        self._center_layout()
        self.redraw()

    def _to_screen(self, x: float, y: float) -> Tuple[float, float]:
        return (x * self.scale + self.offset_x, y * self.scale + self.offset_y)

    def _from_screen(self, sx: float, sy: float) -> Tuple[float, float]:
        return ((sx - self.offset_x) / self.scale, (sy - self.offset_y) / self.scale)

    def set_node_colors(self, colors: Dict[int, str]):
        """Define cores por nó (ex.: por comunidade)."""
        self.node_colors = colors
        self.redraw()

    def redraw(self):
        """Redesenha todo o grafo e atualiza a scrollregion."""
        self.delete("all")

        # Sem grafo carregado: exibe mensagem de boas-vindas
        if self.adapter is None or not self.positions:
            self.configure(scrollregion=(0, 0, 0, 0))
            cw = self.winfo_width() or 800
            ch = self.winfo_height() or 600
            self.create_text(
                cw // 2, ch // 2,
                text="📂  Carregue um arquivo GEXF para visualizar o grafo",
                font=("Arial", 14), fill="#888"
            )
            return

        # Desenha arestas
        for u in self.adapter.nodes():
            if u not in self.positions:
                continue
            for v in self.adapter.successors(u):
                if v not in self.positions:
                    continue
                x1, y1 = self._to_screen(*self.positions[u])
                x2, y2 = self._to_screen(*self.positions[v])
                weight = 1.0
                try:
                    weight = self.adapter._g.get_edge_weight(u, v)
                except Exception:
                    pass
                width = max(0.5, min(3.0, weight * 0.5))
                self.create_line(x1, y1, x2, y2, fill="#999", width=width, arrow="last")

        # Desenha nós
        for node, (x, y) in self.positions.items():
            sx, sy = self._to_screen(x, y)
            color = self.node_colors.get(node, "#4A90E2")
            r = self.node_radius
            if node == self.selected_node:
                r = self.node_radius * 1.3
                color = "#FF6B6B"
            self.create_oval(sx - r, sy - r, sx + r, sy + r,
                             fill=color, outline="#333", width=1)

            label = self.adapter._g.vertex_labels.get(node, str(node))
            if len(label) > 8:
                label = label[:7] + "…"
            self.create_text(sx, sy + r + 9, text=label, font=("Arial", 7), fill="#333")

        self._update_scrollregion()

    def _on_click(self, event):
        """Seleciona nó ao clicar."""
        if not self.positions:
            return
        cx, cy = self.canvasx(event.x), self.canvasy(event.y)
        x, y = self._from_screen(cx, cy)
        closest = self._find_closest_node(x, y)
        if closest is not None:
            self.selected_node = closest
            self.redraw()
            self.event_generate("<<NodeSelected>>")

    def _on_drag(self, event):
        """Arrasta nó selecionado."""
        if self.selected_node is not None and self.positions:
            cx, cy = self.canvasx(event.x), self.canvasy(event.y)
            x, y = self._from_screen(cx, cy)
            self.positions[self.selected_node] = (x, y)
            self.redraw()

    def _on_pan_start(self, event):
        """Início do pan do canvas com o botão do meio do mouse."""
        self.scan_mark(event.x, event.y)

    def _on_pan_move(self, event):
        """Continuação do pan — usa o utilitário nativo `scan_dragto`,
        que desloca a viewport conforme o scrollregion configurado."""
        self.scan_dragto(event.x, event.y, gain=1)

    def _on_zoom(self, event):
        """Zoom com scroll do mouse (Windows/Linux)."""
        if not self.positions:
            return
        if event.num == 4 or getattr(event, "delta", 0) > 0:
            factor = 1.1
        else:
            factor = 0.9
        self.set_zoom_level(self.zoom_level * factor, _notify=True)

    def zoom_in(self):
        """Aumenta o zoom em um passo fixo (`zoom_step`). Pensado para
        ser usado pelo botão "+" embutido, mas pode ser chamado por
        qualquer controle externo (atalho de teclado, menu, etc.)."""
        if not self.positions:
            return
        self.set_zoom_level(self.zoom_level * self.zoom_step, _notify=True)

    def zoom_out(self):
        """Reduz o zoom em um passo fixo (`zoom_step`). Pensado para
        ser usado pelo botão "−" embutido."""
        if not self.positions:
            return
        self.set_zoom_level(self.zoom_level / self.zoom_step, _notify=True)

    def set_zoom_level(self, value: float, _notify: bool = False):
        """Define o zoom (1.0 = 100%, enquadrado ao canvas) — usado pelo
        slider de zoom, pelos botões +/- e pelo scroll do mouse. `value`
        é limitado entre min_zoom e max_zoom. A view do scroll é mantida
        centralizada no ponto médio da viewport atual."""
        old_scale = self.scale
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, value))
        self.scale = self.base_scale * self.zoom_level
        self.redraw()
        self._recenter_after_zoom(old_scale)
        if _notify and self.on_zoom_change:
            self.on_zoom_change(self.zoom_level)

    def _recenter_after_zoom(self, old_scale: float):
        """Ajusta a posição do scroll após uma mudança de zoom, mantendo
        o mesmo ponto do grafo aproximadamente centralizado na viewport
        em vez de pular para o canto superior esquerdo."""
        if not old_scale or not self.positions:
            self._center_view()
            return
        canvas_w = self.winfo_width() or 800
        canvas_h = self.winfo_height() or 600
        # Centro da viewport atual, em coordenadas do "mundo" (antes do
        # zoom ser aplicado), usando a escala anterior.
        old_left = self.canvasx(0)
        old_top = self.canvasy(0)
        center_world_x = (old_left + canvas_w / 2 - self.offset_x) / old_scale
        center_world_y = (old_top + canvas_h / 2 - self.offset_y) / old_scale

        # Mesma posição do mundo, na nova escala — ponto que deve ficar
        # centralizado na viewport após o zoom.
        new_center_x = center_world_x * self.scale + self.offset_x
        new_center_y = center_world_y * self.scale + self.offset_y

        content_w, content_h = self._content_size()
        if content_w > 0:
            frac_x = (new_center_x - canvas_w / 2) / content_w
            self.xview_moveto(max(0.0, min(1.0, frac_x)))
        if content_h > 0:
            frac_y = (new_center_y - canvas_h / 2) / content_h
            self.yview_moveto(max(0.0, min(1.0, frac_y)))

    def _find_closest_node(self, x: float, y: float,
                           threshold: float = 20) -> Optional[int]:
        """Encontra nó mais próximo da posição (x, y)."""
        min_dist = float('inf')
        closest = None
        for node, (nx, ny) in self.positions.items():
            dist = math.hypot(x - nx, y - ny)
            if dist < min_dist:
                min_dist = dist
                closest = node
        return closest if min_dist < threshold / self.scale else None

    def get_selected_node(self) -> Optional[int]:
        return self.selected_node

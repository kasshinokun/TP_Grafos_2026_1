"""Janela principal — navegação entre as telas da aplicação."""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional

from grafo.utils.gexf_parser import load_gexf
from grafo.networkx_pure.adapter import GraphAdapter
from filemanager import PATH_D_GEXF

from gui.screen_home     import HomeScreen
from gui.screen_graph    import GraphScreen
from gui.screen_metrics  import MetricsScreen
from gui.screen_miner    import MinerScreen
from gui.screen_about    import AboutScreen
from gui.screen_settings import SettingsScreen
from gui.screen_manager import ManagerScreen


# Mapeamento: id_tela → (classe, kwargs_extras)
SCREENS = {
    "home":     HomeScreen,
    "miner":    MinerScreen,
    "manager":  ManagerScreen,
    "graph":    GraphScreen,
    "metrics":  MetricsScreen,
    "settings": SettingsScreen,
    "about":    AboutScreen
}

NAV_ITEMS = [
    ("🏠", "Início",      "home"),
    ("⛏️", "Mineração",   "miner"),
    ("🛠️", "Módulos",     "manager"),
    ("🕸️", "Grafo",       "graph"),
    ("📊", "Métricas",    "metrics"),
    ("⚙️", "Config.",     "settings"),
    ("ℹ️", "Sobre",       "about")
]


class MainWindow(ctk.CTk):
    """Janela principal com barra de navegação lateral e área de telas."""

    def __init__(self):
        super().__init__()
        self.title("TP Grafos 2026/1 — Análise de Redes Complexas")
        self.geometry("1400x820")
        self.minsize(960, 640)

        self.adapter: Optional[GraphAdapter] = None
        self._screens: dict = {}
        self._current: Optional[str] = None
        self._nav_buttons: dict = {}

        self._build_layout()
        self._build_nav()
        self._build_screens()

        self.navigate("home")

    # ------------------------------------------------------------------
    # LAYOUT RAIZ
    # ------------------------------------------------------------------

    def _build_layout(self):
        # Barra lateral de navegação (fixa)
        self.nav = ctk.CTkFrame(self, width=130, corner_radius=0,
                                fg_color="#12122A")
        self.nav.pack(side="left", fill="y")
        self.nav.pack_propagate(False)

        # Área de conteúdo (telas empilhadas)
        self.content = ctk.CTkFrame(self, corner_radius=0,
                                    fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True)

    # ------------------------------------------------------------------
    # NAVEGAÇÃO LATERAL
    # ------------------------------------------------------------------

    def _build_nav(self):
        ctk.CTkLabel(
            self.nav, text="TP\nGrafos", font=("Arial", 15, "bold"),
            text_color="#7C7CFA"
        ).pack(pady=(20, 16))

        ctk.CTkFrame(self.nav, height=1, fg_color="#2A2A4A").pack(
            fill="x", padx=10, pady=(0, 10))

        for icon, label, screen_id in NAV_ITEMS:
            btn = ctk.CTkButton(
                self.nav,
                text=f"{icon}\n{label}",
                font=("Arial", 11),
                height=60, width=110,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#2A2A5A",
                text_color="#CCCCDD",
                command=lambda sid=screen_id: self.navigate(sid),
            )
            btn.pack(padx=10, pady=3)
            self._nav_buttons[screen_id] = btn

        # Separador e botão carregar GEXF no rodapé da nav
        ctk.CTkFrame(self.nav, height=1, fg_color="#2A2A4A").pack(
            fill="x", padx=10, pady=(10, 6))

        ctk.CTkButton(
            self.nav, text="📂\nCarregar\nGEXF",
            font=("Arial", 10), height=64, width=110,
            corner_radius=8, fg_color="#1E3A5F",
            hover_color="#2A4A7A", text_color="#AAD4FF",
            command=self._load_gexf
        ).pack(padx=10, pady=3, side="bottom")

    # ------------------------------------------------------------------
    # INSTANCIAÇÃO DAS TELAS
    # ------------------------------------------------------------------

    def _build_screens(self):
        self._screens["home"] = HomeScreen(
            self.content,
            on_load_gexf  = self._load_gexf,
            on_go_miner   = lambda: self.navigate("miner"),
            on_go_graph   = lambda: self.navigate("graph"),
            on_go_metrics = lambda: self.navigate("metrics"),
        )
        self._screens["miner"] = MinerScreen(
            self.content,
            on_back         = lambda: self.navigate("home"),
            on_graph_ready  = self._on_graph_ready,
        )
        self._screens["manager"] = ManagerScreen(
            self.content,
            on_back = lambda: self.navigate("home"),
        )
        self._screens["graph"] = GraphScreen(
            self.content,
            on_back       = lambda: self.navigate("home"),
            on_load_gexf  = self._load_gexf,
        )
        self._screens["metrics"] = MetricsScreen(
            self.content,
            on_back             = lambda: self.navigate("home"),
            on_colors_computed  = self._apply_community_colors,
            on_load_gexf        = self._load_gexf,
        )
        self._screens["settings"] = SettingsScreen(
            self.content,
            on_back = lambda: self.navigate("home"),
            on_save = self._apply_settings,
        )
        self._screens["about"] = AboutScreen(
            self.content,
            on_back = lambda: self.navigate("home"),
        )
        

        # Coloca todas as telas no mesmo espaço (só uma visível por vez)
        for screen in self._screens.values():
            screen.place(relx=0, rely=0, relwidth=1, relheight=1)

    # ------------------------------------------------------------------
    # NAVEGAÇÃO
    # ------------------------------------------------------------------

    def navigate(self, screen_id: str):
        if screen_id not in self._screens:
            return

        # Esconde tela atual
        if self._current and self._current in self._screens:
            self._screens[self._current].place_forget()
            # Restaura cor do botão anterior
            prev_btn = self._nav_buttons.get(self._current)
            if prev_btn:
                prev_btn.configure(fg_color="transparent", text_color="#CCCCDD")

        # Exibe nova tela
        self._current = screen_id
        self._screens[screen_id].place(relx=0, rely=0, relwidth=1, relheight=1)
        self._screens[screen_id].lift()
        self._screens[screen_id].refresh()

        # Destaca botão ativo
        active_btn = self._nav_buttons.get(screen_id)
        if active_btn:
            active_btn.configure(fg_color="#2A2A6A", text_color="#FFFFFF")

    # ------------------------------------------------------------------
    # CARREGAMENTO DE GEXF
    # ------------------------------------------------------------------

    def _load_gexf(self):
        path = filedialog.askopenfilename(
            title="Selecione arquivo GEXF",
            initialdir=PATH_D_GEXF,  # root_path/gexf
            filetypes=[("GEXF", "*.gexf *.gexf.txt"), ("Todos", "*.*")])
        if not path:
            return
        try:
            G = load_gexf(path)
            self._set_adapter(GraphAdapter(G))
            n = self.adapter.number_of_nodes()
            e = self.adapter.number_of_edges()
            messagebox.showinfo("Grafo carregado",
                                f"✅ {n} nós e {e} arestas carregados com sucesso.")
            self.navigate("graph")
        except Exception as ex:
            messagebox.showerror("Erro ao carregar GEXF", str(ex))

    # ------------------------------------------------------------------
    # PROPAGAÇÃO DO ADAPTER
    # ------------------------------------------------------------------

    def _set_adapter(self, adapter: GraphAdapter):
        """Distribui o adapter para todas as telas que precisam dele."""
        self.adapter = adapter
        self._screens["graph"].load_adapter(adapter)
        self._screens["metrics"].load_adapter(adapter)

    def _on_graph_ready(self, adapter: GraphAdapter):
        """Callback do MinerScreen quando a mineração termina."""
        self._set_adapter(adapter)
        messagebox.showinfo("Mineração concluída",
                            "Grafo construído! Navegue para Grafo ou Métricas.")
        self.navigate("graph")

    def _apply_community_colors(self, colors: dict):
        """Recebe cores por nó do MetricsScreen e aplica nos grafos das telas
        Grafo e Métricas (o canvas de Métricas já se colore sozinho)."""
        self._screens["graph"].set_node_colors(colors)

    # ------------------------------------------------------------------
    # CONFIGURAÇÕES
    # ------------------------------------------------------------------

    def _apply_settings(self, config: dict):
        ctk.set_appearance_mode(config.get('theme', 'dark'))
        # Aplica raio dos nós nos canvases do GraphScreen e do MetricsScreen
        for screen_id in ("graph", "metrics"):
            canvas = getattr(self._screens[screen_id], 'canvas', None)
            if canvas:
                canvas.node_radius = config.get('node_radius', 12)
                canvas.redraw()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = MainWindow()
    app.mainloop()

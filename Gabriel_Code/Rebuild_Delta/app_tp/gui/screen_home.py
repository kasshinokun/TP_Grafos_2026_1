"""Tela inicial / Dashboard da aplicação."""
import customtkinter as ctk
from typing import Callable, Optional
from gui.screen_base import BaseScreen


class HomeScreen(BaseScreen):
    """Tela de boas-vindas com acesso rápido às funcionalidades."""

    def __init__(self, master,
                 on_load_gexf: Optional[Callable] = None,
                 on_go_miner: Optional[Callable] = None,
                 on_go_graph: Optional[Callable] = None,
                 on_go_metrics: Optional[Callable] = None,
                 **kwargs):
        self.on_load_gexf  = on_load_gexf
        self.on_go_miner   = on_go_miner
        self.on_go_graph   = on_go_graph
        self.on_go_metrics = on_go_metrics
        super().__init__(
            master,
            title="TP Grafos 2026/1",
            subtitle="Análise de Redes Complexas — PUC-MG",
            **kwargs
        )

    def _build_content(self):
        # Área central com scroll
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            scroll,
            text="Bem-vindo ao Sistema de Análise de Grafos",
            font=("Arial", 16, "bold")
        ).pack(pady=(10, 4))

        ctk.CTkLabel(
            scroll,
            text="Carregue um arquivo GEXF ou mine um repositório do GitHub para começar.",
            font=("Arial", 12), text_color="#888"
        ).pack(pady=(0, 24))

        # Cards de acesso rápido
        cards_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        cards_frame.pack(fill="x")

        self._card(cards_frame,
                   "📂", "Carregar GEXF",
                   "Abra um arquivo de grafo local (.gexf)",
                   self.on_load_gexf, "#2563EB").grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self._card(cards_frame,
                   "⛏️", "Minerador GitHub",
                   "Mine interações de repositórios públicos",
                   self.on_go_miner, "#16A34A").grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self._card(cards_frame,
                   "🕸️", "Visualizar Grafo",
                   "Veja o grafo com layout force-directed",
                   self.on_go_graph, "#7C3AED").grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self._card(cards_frame,
                   "📊", "Métricas",
                   "Calcule as 11 métricas de redes complexas",
                   self.on_go_metrics, "#B45309").grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)

        # Rodapé informativo
        ctk.CTkLabel(
            scroll,
            text="Prof. Leonardo V. Cardoso  ·  Disciplina: Teoria de Grafos e Computabilidade",
            font=("Arial", 10), text_color="#666"
        ).pack(pady=(30, 0))

    @staticmethod
    def _card(parent, icon: str, title: str, desc: str,
              command: Optional[Callable], color: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, corner_radius=12, border_width=1,
                            border_color="#333")
        card.configure(cursor="hand2" if command else "")

        ctk.CTkLabel(card, text=icon, font=("Arial", 32)).pack(pady=(18, 4))
        ctk.CTkLabel(card, text=title, font=("Arial", 14, "bold")).pack()
        ctk.CTkLabel(card, text=desc, font=("Arial", 11),
                     text_color="#888", wraplength=200).pack(pady=(4, 10))

        if command:
            ctk.CTkButton(
                card, text="Abrir →", fg_color=color,
                command=command, width=120
            ).pack(pady=(0, 16))

        return card

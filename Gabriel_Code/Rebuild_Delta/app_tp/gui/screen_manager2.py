"""Tela de gerenciamento modular com ComboBox para frames em branco."""
import customtkinter as ctk
from typing import Optional, Callable
from gui.screen_base import BaseScreen
from gui.frames.empty_frames import (
    ManageGraphsFrame, 
    PrimitiveAPIFrame, 
    SearchPathsFrame, 
    PureNetworkXFrame
)

class ManagerScreen(BaseScreen):
    """Tela que gerencia a exibição de múltiplos frames via ComboBox."""

    def __init__(self, master, on_back: Optional[Callable] = None, **kwargs):
        super().__init__(
            master,
            title="🛠️ Gerenciador de Módulos",
            subtitle="Selecione um módulo para visualizar (Frames em desenvolvimento)",
            on_back=on_back,
            **kwargs
        )

    def _build_content(self):
        # Frame superior para o seletor
        self.selector_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.selector_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.selector_frame, text="Módulo Ativo:", font=("Arial", 12, "bold")).pack(side="left", padx=10)

        self.options = [
            "Gerenciar Grafos", 
            "API Primitiva", 
            "Busca & Caminhos", 
            "PureNetworkX & Testes"
        ]
        
        self.combo = ctk.CTkComboBox(
            self.selector_frame, 
            values=self.options,
            command=self._on_change,
            width=250,
            state="readonly"
        )
        self.combo.pack(side="left", padx=10)
        self.combo.set(self.options[0])

        # Container para os frames
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Dicionário de frames
        self.frames = {
            "Gerenciar Grafos": ManageGraphsFrame(self.container),
            "API Primitiva": PrimitiveAPIFrame(self.container),
            "Busca & Caminhos": SearchPathsFrame(self.container),
            "PureNetworkX & Testes": PureNetworkXFrame(self.container)
        }

        # Inicializa o primeiro frame
        self._on_change(self.options[0])

    def _on_change(self, choice):
        """Troca o frame visível no container."""
        for name, frame in self.frames.items():
            if name == choice:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

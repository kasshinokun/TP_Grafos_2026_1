"""Tela base reutilizável para todas as telas da aplicação."""
import customtkinter as ctk
from typing import Optional, Callable


class BaseScreen(ctk.CTkFrame):
    """Frame base com título, subtítulo e área de conteúdo padronizados.
    
    Todas as telas da aplicação herdam desta classe.
    Basta sobrescrever `_build_content()` para adicionar widgets.
    """

    TITLE_FONT  = ("Arial", 18, "bold")
    SUBTITLE_FONT = ("Arial", 11)
    BG_HEADER   = "#1E1E2E"
    FG_TITLE    = "#FFFFFF"
    FG_SUBTITLE = "#AAAACC"

    def __init__(self, master,
                 title: str = "Tela",
                 subtitle: str = "",
                 on_back: Optional[Callable] = None,
                 **kwargs):
        super().__init__(master, **kwargs)

        self.title_text    = title
        self.subtitle_text = subtitle
        self.on_back       = on_back

        self._build_header()
        self._build_content()

    # ------------------------------------------------------------------
    # HEADER PADRONIZADO
    # ------------------------------------------------------------------

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=self.BG_HEADER, corner_radius=0)
        header.pack(fill="x")

        # Botão voltar (opcional)
        if self.on_back:
            ctk.CTkButton(
                header, text="← Voltar", width=80,
                fg_color="transparent", text_color="#AAAACC",
                hover_color="#333355", command=self.on_back
            ).pack(side="left", padx=10, pady=8)

        text_col = ctk.CTkFrame(header, fg_color="transparent")
        text_col.pack(side="left", padx=(10 if not self.on_back else 0, 10), pady=8)

        ctk.CTkLabel(
            text_col, text=self.title_text,
            font=self.TITLE_FONT, text_color=self.FG_TITLE
        ).pack(anchor="w")

        if self.subtitle_text:
            ctk.CTkLabel(
                text_col, text=self.subtitle_text,
                font=self.SUBTITLE_FONT, text_color=self.FG_SUBTITLE
            ).pack(anchor="w")

        # Separador
        ctk.CTkFrame(self, height=2, fg_color="#333355").pack(fill="x")

    # ------------------------------------------------------------------
    # ÁREA DE CONTEÚDO — sobrescreva nas subclasses
    # ------------------------------------------------------------------

    def _build_content(self):
        """Sobrescreva para adicionar widgets à tela."""
        ctk.CTkLabel(
            self,
            text="(conteúdo a ser implementado)",
            text_color="#666", font=("Arial", 13)
        ).pack(expand=True)

    # ------------------------------------------------------------------
    # UTILITÁRIOS
    # ------------------------------------------------------------------

    def set_title(self, title: str):
        self.title_text = title

    def refresh(self):
        """Chamado pela MainWindow ao exibir esta tela. Sobrescreva se necessário."""
        pass

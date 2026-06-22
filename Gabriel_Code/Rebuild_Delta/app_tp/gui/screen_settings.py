"""Tela de Configurações da aplicação."""
import customtkinter as ctk
from typing import Optional, Callable
from gui.screen_base import BaseScreen


class SettingsScreen(BaseScreen):
    """Preferências de visualização, tema e caminhos padrão."""

    def __init__(self, master,
                 on_back: Optional[Callable] = None,
                 on_save: Optional[Callable] = None,
                 **kwargs):
        self.on_save = on_save
        super().__init__(
            master,
            title="⚙️ Configurações",
            subtitle="Preferências de tema, layout e exportação",
            on_back=on_back,
            **kwargs
        )

    def _build_content(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=30, pady=16)

        def section(title: str):
            ctk.CTkLabel(scroll, text=title,
                         font=("Arial", 13, "bold")).pack(anchor="w", pady=(16, 4))
            ctk.CTkFrame(scroll, height=1, fg_color="#333").pack(fill="x", pady=(0, 8))

        # ---------- Aparência ----------
        section("🎨 Aparência")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="Tema da interface:", width=200,
                     anchor="w").pack(side="left")
        self.theme_var = ctk.StringVar(value="dark")
        ctk.CTkSegmentedButton(
            row, values=["dark", "light", "system"],
            variable=self.theme_var,
            command=self._apply_theme
        ).pack(side="left")

        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill="x", pady=4)
        ctk.CTkLabel(row2, text="Cor de destaque:", width=200,
                     anchor="w").pack(side="left")
        self.color_var = ctk.StringVar(value="blue")
        ctk.CTkOptionMenu(row2, values=["blue", "green", "dark-blue"],
                          variable=self.color_var).pack(side="left")

        # ---------- Layout do Grafo ----------
        section("🕸️ Layout do Grafo")

        row3 = ctk.CTkFrame(scroll, fg_color="transparent")
        row3.pack(fill="x", pady=4)
        ctk.CTkLabel(row3, text="Iterações do layout:", width=200,
                     anchor="w").pack(side="left")
        self.iterations_var = ctk.IntVar(value=100)
        ctk.CTkSlider(row3, from_=20, to=300, number_of_steps=28,
                      variable=self.iterations_var).pack(side="left", padx=8)
        self.lbl_iter = ctk.CTkLabel(row3, text="100", width=40)
        self.lbl_iter.pack(side="left")
        self.iterations_var.trace_add("write",
            lambda *_: self.lbl_iter.configure(text=str(self.iterations_var.get())))

        row4 = ctk.CTkFrame(scroll, fg_color="transparent")
        row4.pack(fill="x", pady=4)
        ctk.CTkLabel(row4, text="Raio dos nós (px):", width=200,
                     anchor="w").pack(side="left")
        self.radius_var = ctk.IntVar(value=12)
        ctk.CTkSlider(row4, from_=6, to=24, number_of_steps=18,
                      variable=self.radius_var).pack(side="left", padx=8)
        self.lbl_radius = ctk.CTkLabel(row4, text="12", width=40)
        self.lbl_radius.pack(side="left")
        self.radius_var.trace_add("write",
            lambda *_: self.lbl_radius.configure(text=str(self.radius_var.get())))

        self.show_labels_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(scroll, text="Exibir rótulos dos nós no canvas",
                        variable=self.show_labels_var).pack(anchor="w", pady=4)

        # ---------- Mineração ----------
        section("⛏️ Mineração")

        row5 = ctk.CTkFrame(scroll, fg_color="transparent")
        row5.pack(fill="x", pady=4)
        ctk.CTkLabel(row5, text="Intervalo de checkpoint (s):", width=200,
                     anchor="w").pack(side="left")
        self.checkpoint_var = ctk.IntVar(value=60)
        ctk.CTkEntry(row5, textvariable=self.checkpoint_var, width=80).pack(side="left")

        self.use_hybrid_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(scroll, text="Usar minerador híbrido por padrão",
                        variable=self.use_hybrid_var).pack(anchor="w", pady=4)

        # ---------- Botão Salvar ----------
        ctk.CTkButton(
            scroll, text="💾 Salvar Configurações",
            command=self._save, width=200
        ).pack(pady=(24, 4))

        self.lbl_saved = ctk.CTkLabel(scroll, text="", text_color="#22C55E",
                                      font=("Arial", 11))
        self.lbl_saved.pack()

    def _apply_theme(self, value: str):
        ctk.set_appearance_mode(value)

    def _save(self):
        config = {
            'theme':        self.theme_var.get(),
            'color':        self.color_var.get(),
            'iterations':   self.iterations_var.get(),
            'node_radius':  self.radius_var.get(),
            'show_labels':  self.show_labels_var.get(),
            'checkpoint':   self.checkpoint_var.get(),
            'use_hybrid':   self.use_hybrid_var.get(),
        }
        if self.on_save:
            self.on_save(config)
        self.lbl_saved.configure(text="✅ Configurações salvas!")
        self.after(2500, lambda: self.lbl_saved.configure(text=""))

    def get_config(self) -> dict:
        return {
            'iterations': self.iterations_var.get(),
            'node_radius': self.radius_var.get(),
            'show_labels': self.show_labels_var.get(),
        }

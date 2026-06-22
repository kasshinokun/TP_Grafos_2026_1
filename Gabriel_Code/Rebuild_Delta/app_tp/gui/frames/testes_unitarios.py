# ./gui/frames/testes_unitarios.py
"""Tela de Testes Unitários.

Interface gráfica para a suíte de testes do projeto (`./tests`), sem
reimplementar nenhuma lógica de teste — toda a descoberta/organização/
execução é delegada ao bridge `gui.bridges.test_orchestrator.TestOrchestrator`,
e toda a formatação de resultado para texto é delegada a
`gui.utils.test_formatting`. Esta tela só monta os widgets e conecta os
eventos (seleção nos comboboxes, clique no botão) às chamadas do bridge.

Layout: sidebar à esquerda com dois comboboxes —
  1) Categoria: um módulo de teste (ex.: "Algoritmos de grafos")
  2) Execução: "Todos da categoria" ou uma classe de teste específica
     dentro da categoria escolhida (a granularidade de "execução" é
     decidida pelo próprio TestOrchestrator, daí o nome bridge: esta
     tela não sabe nada sobre TestCase/TestSuite, só pede ao
     orchestrator "quais execuções existem para esta categoria" e "rode
     esta execução").
— e um pseudo-console (CTkTextbox) ocupando a área principal, mostrando
o relatório de cada execução.
"""
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox

from gui.bridges.test_orchestrator import TestOrchestrator, ALL_CLASSES_LABEL
from gui.utils.test_formatting import format_full_report, format_category_summary


class UnitTestFrame(ctk.CTkFrame):
    """Frame para o módulo de Testes Unitários."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.orchestrator = TestOrchestrator()

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_console()

        # Seleciona a primeira categoria por padrão, já populando o
        # segundo combobox de acordo — o usuário abre a tela e já vê
        # uma combinação válida pronta para rodar, sem precisar
        # escolher os dois comboboxes manualmente antes do primeiro uso.
        categories = self.orchestrator.list_categories()
        if categories:
            self.category_combo.set(categories[0].label)
            self._on_category_change(categories[0].label)

        self._console_log("Pronto. Escolha uma categoria e uma execução, depois clique em 'Rodar testes'.")

    # ------------------------------------------------------------------
    # Construção da UI
    # ------------------------------------------------------------------

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=300)
        self.sidebar.grid(row=0, column=0, sticky="nswe", padx=10, pady=10)
        self.sidebar.grid_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.sidebar,
            text="Testes Unitários",
            font=("Helvetica", 20, "bold"),
        )
        self.title_label.pack(pady=(20, 10))

        # --- 1º combobox: categoria ---
        self.category_label = ctk.CTkLabel(
            self.sidebar, text="Categoria:", font=("Helvetica", 14, "bold")
        )
        self.category_label.pack(pady=(10, 0))

        self._categories = self.orchestrator.list_categories()
        category_labels = [cat.label for cat in self._categories]
        self.category_combo = ctk.CTkComboBox(
            self.sidebar,
            values=category_labels if category_labels else ["(nenhuma categoria)"],
            width=260,
            state="readonly",
            command=self._on_category_change,
        )
        self.category_combo.pack(pady=(5, 5))

        # --- 2º combobox: execução (orquestrada pelo TestOrchestrator) ---
        self.run_label_widget = ctk.CTkLabel(
            self.sidebar, text="Execução:", font=("Helvetica", 14, "bold")
        )
        self.run_label_widget.pack(pady=(10, 0))

        self.run_combo = ctk.CTkComboBox(
            self.sidebar,
            values=["(selecione uma categoria)"],
            width=260,
            state="readonly",
        )
        self.run_combo.pack(pady=(5, 5))

        # --- Status da categoria selecionada (ex.: aviso de pytest ausente) ---
        self.category_status_label = ctk.CTkLabel(
            self.sidebar,
            text="",
            font=("Helvetica", 11),
            wraplength=260,
            text_color="#E0A030",
            justify="left",
        )
        self.category_status_label.pack(pady=(0, 10))

        # --- Botões de ação ---
        self.run_button = ctk.CTkButton(
            self.sidebar, text="▶ Rodar testes", command=self._on_run_click,
        )
        self.run_button.pack(fill="x", padx=15, pady=(10, 4))

        self.run_all_categories_button = ctk.CTkButton(
            self.sidebar, text="⏩ Rodar todas as categorias",
            command=self._on_run_all_categories_click,
            fg_color="#444466",
        )
        self.run_all_categories_button.pack(fill="x", padx=15, pady=4)

        self.clear_console_button = ctk.CTkButton(
            self.sidebar, text="🧹 Limpar console",
            command=self._on_clear_console_click,
            fg_color="#555555",
        )
        self.clear_console_button.pack(fill="x", padx=15, pady=4)

        # --- Resumo rápido (contagem total de testes na suíte) ---
        self.summary_label = ctk.CTkLabel(
            self.sidebar,
            text=self._build_static_summary_text(),
            font=("Helvetica", 11),
            wraplength=260,
            justify="left",
            text_color="#999",
        )
        self.summary_label.pack(pady=(20, 10), padx=10)

    def _build_console(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=0, column=1, sticky="nswe", padx=(0, 10), pady=10)

        header = ctk.CTkLabel(
            body, text="Console de execução", font=("Helvetica", 16, "bold")
        )
        header.pack(anchor="w", pady=(0, 6))

        self.console_box = ctk.CTkTextbox(
            body, wrap="word", font=("Consolas", 12)
        )
        self.console_box.pack(fill="both", expand=True)
        self.console_box.configure(state="disabled")

    def _build_static_summary_text(self) -> str:
        """Conta, sem executar nada, quantos testes existem em cada
        categoria baseada em unittest (a categoria pytest não é
        contada aqui, pois sua descoberta de testes é interna ao
        próprio pytest — listamos só que ela existe)."""
        lines = ["Categorias disponíveis:"]
        for cat in self._categories:
            if cat.uses_pytest:
                lines.append(f"  • {cat.label}: requer pytest")
                continue
            try:
                methods = self.orchestrator.list_test_methods(cat.key, ALL_CLASSES_LABEL)
                lines.append(f"  • {cat.label}: {len(methods)} teste(s)")
            except Exception:
                lines.append(f"  • {cat.label}: (erro ao listar)")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def _on_category_change(self, _selected_label=None):
        """Repopula o 2º combobox (execuções) conforme a categoria
        escolhida no 1º — é aqui que o bridge decide o que aparece:
        esta tela não sabe se é uma classe, um módulo pytest, etc."""
        category = self._current_category()
        if category is None:
            self.run_combo.configure(values=["(nenhuma categoria)"])
            self.run_combo.set("(nenhuma categoria)")
            self.category_status_label.configure(text="")
            return

        runs = self.orchestrator.list_runs(category.key)
        self.run_combo.configure(values=runs if runs else ["(nenhuma execução)"])
        self.run_combo.set(runs[0] if runs else "(nenhuma execução)")

        if category.uses_pytest:
            self.category_status_label.configure(
                text="⚠️ Esta categoria depende do pacote 'pytest'. "
                     "Se não estiver instalado, o relatório indicará "
                     "isso ao rodar, em vez de travar a tela."
            )
        else:
            self.category_status_label.configure(text="")

    def _on_run_click(self):
        category = self._current_category()
        if category is None:
            messagebox.showwarning("Aviso", "Nenhuma categoria selecionada.")
            return

        run_label = self.run_combo.get()
        if not run_label or run_label.startswith("("):
            messagebox.showwarning("Aviso", "Nenhuma execução válida selecionada.")
            return

        self._console_log(f"▶ Executando: {category.label} → {run_label} ...")
        try:
            report = self.orchestrator.run(category.key, run_label)
        except Exception as ex:
            self._console_log(f"❌ Erro inesperado ao executar os testes: {ex}")
            return

        self._console_log(format_full_report(report))

    def _on_run_all_categories_click(self):
        """Roda 'Todos da categoria' para cada categoria disponível,
        uma após a outra, e mostra um resumo agregado seguido de cada
        relatório individual — útil para uma checagem geral rápida da
        suíte inteira sem precisar trocar a categoria manualmente
        várias vezes."""
        self._console_log("⏩ Executando todas as categorias ...")
        reports = []
        for category in self._categories:
            try:
                report = self.orchestrator.run(category.key, ALL_CLASSES_LABEL)
            except Exception as ex:
                self._console_log(f"❌ Erro inesperado em '{category.label}': {ex}")
                continue
            reports.append(report)

        if not reports:
            self._console_log("Nenhuma categoria pôde ser executada.")
            return

        self._console_log(format_category_summary(reports))
        for report in reports:
            self._console_log("")
            self._console_log(format_full_report(report, show_raw_output=False))

    def _on_clear_console_click(self):
        self.console_box.configure(state="normal")
        self.console_box.delete("1.0", "end")
        self.console_box.configure(state="disabled")

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------

    def _current_category(self):
        selected_label = self.category_combo.get()
        for cat in self._categories:
            if cat.label == selected_label:
                return cat
        return None

    def _console_log(self, text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_box.configure(state="normal")
        self.console_box.insert("end", f"[{timestamp}] {text}\n")
        self.console_box.configure(state="disabled")
        self.console_box.see("end")

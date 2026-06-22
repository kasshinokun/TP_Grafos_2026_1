"""Painel de controle do minerador na GUI."""
import customtkinter as ctk
from tkinter import scrolledtext
from typing import Optional, Callable
import threading


class MinerControlPanel(ctk.CTkFrame):
    """Painel para controlar a mineração de repositórios."""
    
    def __init__(self, master, on_start_mining: Callable, on_cancel_mining: Callable, **kwargs):
        super().__init__(master, **kwargs)
        
        self.on_start_mining = on_start_mining
        self.on_cancel_mining = on_cancel_mining
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura interface do painel."""
        # Título
        title_label = ctk.CTkLabel(self, text="⛏️ Mineração de Repositório", 
                                   font=("Arial", 14, "bold"))
        title_label.pack(pady=(10, 5), padx=10, anchor="w")
        
        # Campos de entrada
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(input_frame, text="Proprietário:").pack(anchor="w", pady=(5, 0))
        self.owner_entry = ctk.CTkEntry(input_frame, placeholder_text="ex: microsoft")
        self.owner_entry.pack(fill="x", pady=2)
        
        ctk.CTkLabel(input_frame, text="Repositório:").pack(anchor="w", pady=(5, 0))
        self.repo_entry = ctk.CTkEntry(input_frame, placeholder_text="ex: TypeScript")
        self.repo_entry.pack(fill="x", pady=2)
        
        ctk.CTkLabel(input_frame, text="Token GitHub:").pack(anchor="w", pady=(5, 0))
        self.token_entry = ctk.CTkEntry(input_frame, placeholder_text="ghp_...", show="*")
        self.token_entry.pack(fill="x", pady=2)
        
        # Botões de controle
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_start = ctk.CTkButton(button_frame, text="▶️ Iniciar Mineração", 
                                       command=self._on_start, fg_color="#2ECC71")
        self.btn_start.pack(side="left", expand=True, fill="x", padx=2)
        
        self.btn_cancel = ctk.CTkButton(button_frame, text="⏹️ Cancelar", 
                                        command=self._on_cancel, state="disabled", 
                                        fg_color="#E74C3C")
        self.btn_cancel.pack(side="left", expand=True, fill="x", padx=2)
        
        # Barra de progresso
        self.progress_label = ctk.CTkLabel(self, text="Progresso: 0%")
        self.progress_label.pack(padx=10, anchor="w")
        
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        # Área de logs
        log_label = ctk.CTkLabel(self, text="Logs:", font=("Arial", 11, "bold"))
        log_label.pack(padx=10, anchor="w", pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(self, height=8, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
    
    def _on_start(self):
        """Handler do botão iniciar."""
        owner = self.owner_entry.get().strip()
        repo = self.repo_entry.get().strip()
        token = self.token_entry.get().strip()
        
        if not owner or not repo or not token:
            self._log("❌ Preencha todos os campos!")
            return
        
        self.btn_start.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.progress_bar.set(0)
        self._log(f"🚀 Iniciando mineração de {owner}/{repo}...")
        
        self.on_start_mining(owner, repo, [token])
    
    def _on_cancel(self):
        """Handler do botão cancelar."""
        self._log("⏹️ Cancelando mineração...")
        self.on_cancel_mining()
        self.btn_start.configure(state="normal")
        self.btn_cancel.configure(state="disabled")
    
    def update_progress(self, progress: float, message: str):
        """Atualiza barra de progresso e log."""
        self.progress_bar.set(progress)
        self.progress_label.configure(text=f"Progresso: {progress*100:.1f}%")
        self._log(message)
    
    def _log(self, message: str):
        """Adiciona mensagem ao log."""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
    
    def mining_completed(self, success: bool, message: str):
        """Notifica conclusão da mineração."""
        self.btn_start.configure(state="normal")
        self.btn_cancel.configure(state="disabled")
        
        if success:
            self._log(f"✅ {message}")
            self.progress_bar.set(1.0)
            self.progress_label.configure(text="Progresso: 100%")
        else:
            self._log(f"❌ {message}")
            self.progress_bar.set(0)
            self.progress_label.configure(text="Progresso: 0%")
import customtkinter as ctk

class PureNetworkXFrame(ctk.CTkFrame):
    """Frame para o módulo de PureNetworkX & Testes."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Título do Frame
        self.title_label = ctk.CTkLabel(
            self, 
            text="Pure NetworkX & Testes", 
            font=("Helvetica", 20, "bold")
        )
        self.title_label.pack(pady=(20, 10))
        
        

import customtkinter as ctk

class BaseEmptyFrame(ctk.CTkFrame):
    def __init__(self, master, title, **kwargs):
        super().__init__(master, **kwargs)
        self.label = ctk.CTkLabel(self, text=title, font=("Helvetica", 20, "bold"))
        self.label.pack(pady=20)
        self.info = ctk.CTkLabel(self, text="Frame em branco (Aguardando implementação)", font=("Helvetica", 14))
        self.info.pack(pady=10)

class ManageGraphsFrame(BaseEmptyFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, "Gerenciar Grafos", **kwargs)

class PrimitiveAPIFrame(BaseEmptyFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, "API Primitiva", **kwargs)

class SearchPathsFrame(BaseEmptyFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, "Busca & Caminhos", **kwargs)

class PureNetworkXFrame(BaseEmptyFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, "PureNetworkX & Testes", **kwargs)

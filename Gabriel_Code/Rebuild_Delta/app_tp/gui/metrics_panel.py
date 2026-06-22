"""Painel de exibição de métricas do grafo."""
import customtkinter as ctk
from tkinter import ttk
from typing import Dict, List, Optional


class MetricsPanel(ctk.CTkFrame):
    """Painel para exibir métricas calculadas."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._setup_ui()

    def _setup_ui(self):
        """Configura interface do painel."""
        title_label = ctk.CTkLabel(self, text="📊 Métricas do Grafo",
                                   font=("Arial", 14, "bold"))
        title_label.pack(pady=(10, 5), padx=10, anchor="w")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Aba 1: Centralidade
        self.centrality_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.centrality_frame, text="Centralidade")
        self.centrality_text = ctk.CTkTextbox(self.centrality_frame, font=("Consolas", 10))
        self.centrality_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Aba 2: Estrutura
        self.structure_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.structure_frame, text="Estrutura")
        self.structure_text = ctk.CTkTextbox(self.structure_frame, font=("Consolas", 10))
        self.structure_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Aba 3: Comunidades
        self.community_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.community_frame, text="Comunidades")
        self.community_text = ctk.CTkTextbox(self.community_frame, font=("Consolas", 10))
        self.community_text.pack(fill="both", expand=True, padx=5, pady=5)

    # ==========================================
    # MÉTRICAS DE CENTRALIDADE
    # ==========================================

    def show_pagerank(self, pagerank_values: Dict[int, float], labels: Dict[int, str]):
        """Exibe resultados do PageRank."""
        self.centrality_text.delete("1.0", "end")
        self.centrality_text.insert("1.0", "📈 PageRank (Top 20)\n")
        self.centrality_text.insert("end", "=" * 50 + "\n\n")
        sorted_nodes = sorted(pagerank_values.items(), key=lambda x: x[1], reverse=True)
        for rank, (node, pr) in enumerate(sorted_nodes[:20], 1):
            label = labels.get(node, str(node))
            self.centrality_text.insert("end", f"{rank:2d}. {label:25s} {pr:.6f}\n")

    def show_betweenness(self, betweenness_values: Dict[int, float], labels: Dict[int, str]):
        """Exibe resultados do Betweenness Centrality."""
        self.centrality_text.delete("1.0", "end")
        self.centrality_text.insert("1.0", "🌉 Betweenness Centrality (Top 20)\n")
        self.centrality_text.insert("end", "=" * 50 + "\n\n")
        sorted_nodes = sorted(betweenness_values.items(), key=lambda x: x[1], reverse=True)
        for rank, (node, bc) in enumerate(sorted_nodes[:20], 1):
            label = labels.get(node, str(node))
            self.centrality_text.insert("end", f"{rank:2d}. {label:25s} {bc:.6f}\n")

    def show_closeness(self, closeness_values: Dict[int, float], labels: Dict[int, str]):
        """Exibe resultados do Closeness Centrality."""
        self.centrality_text.delete("1.0", "end")
        self.centrality_text.insert("1.0", "🎯 Closeness Centrality (Top 20)\n")
        self.centrality_text.insert("end", "=" * 50 + "\n\n")
        sorted_nodes = sorted(closeness_values.items(), key=lambda x: x[1], reverse=True)
        for rank, (node, cc) in enumerate(sorted_nodes[:20], 1):
            label = labels.get(node, str(node))
            self.centrality_text.insert("end", f"{rank:2d}. {label:25s} {cc:.6f}\n")

    def show_degree_centrality(self, degree_values: Dict[int, dict], labels: Dict[int, str]):
        """Exibe Degree Centrality (in e out)."""
        self.centrality_text.delete("1.0", "end")
        self.centrality_text.insert("1.0", "📊 Degree Centrality (Top 20 por In-Degree)\n")
        self.centrality_text.insert("end", "=" * 50 + "\n\n")
        self.centrality_text.insert("end", f"{'Nó':<25} {'In':>5} {'Out':>5} {'In%':>8} {'Out%':>8}\n")
        self.centrality_text.insert("end", "-" * 55 + "\n")
        sorted_nodes = sorted(degree_values.items(), key=lambda x: x[1]['in'], reverse=True)
        for node, metrics in sorted_nodes[:20]:
            label = labels.get(node, str(node))
            self.centrality_text.insert(
                "end",
                f"{label:<25} {metrics['in']:>5d} {metrics['out']:>5d} "
                f"{metrics['in_norm']:>7.4f} {metrics['out_norm']:>7.4f}\n"
            )

    # ==========================================
    # MÉTRICAS DE ESTRUTURA
    # ==========================================

    def show_structure_metrics(self, density: float, avg_clustering: float,
                               assortativity: float, diameter: int = None,
                               avg_path: float = None):
        """Exibe métricas de estrutura e coesão."""
        self.structure_text.delete("1.0", "end")
        self.structure_text.insert("1.0", "🔗 Métricas de Estrutura e Coesão\n")
        self.structure_text.insert("end", "=" * 50 + "\n\n")

        self.structure_text.insert("end", f"{'Densidade da Rede:':<35} {density:.6f}\n")
        self.structure_text.insert("end", f"{'Coef. Aglomeração Médio:':<35} {avg_clustering:.6f}\n")
        self.structure_text.insert("end", f"{'Assortatividade (Pearson):':<35} {assortativity:.6f}\n")

        if diameter is not None:
            self.structure_text.insert("end", f"\n{'Diâmetro do Grafo:':<35} {diameter}\n")
        if avg_path is not None:
            self.structure_text.insert("end", f"{'Comprimento Médio do Caminho:':<35} {avg_path:.4f}\n")

        # Interpretações
        self.structure_text.insert("end", "\n📋 Interpretação:\n")
        self.structure_text.insert("end", "-" * 50 + "\n")
        if density < 0.01:
            self.structure_text.insert("end", "• Rede esparsa — poucas conexões relativas.\n")
        elif density < 0.1:
            self.structure_text.insert("end", "• Rede moderadamente densa.\n")
        else:
            self.structure_text.insert("end", "• Rede densa — muitas conexões relativas.\n")

        if assortativity > 0.1:
            self.structure_text.insert("end", "• Rede assortativa: hubs tendem a se conectar entre si.\n")
        elif assortativity < -0.1:
            self.structure_text.insert("end", "• Rede dissortativa: hubs tendem a conectar periféricos.\n")
        else:
            self.structure_text.insert("end", "• Assortatividade neutra.\n")

    # ==========================================
    # MÉTRICAS DE COMUNIDADE
    # ==========================================

    def show_communities(self, communities: List[List[int]], modularity: float,
                         labels: Optional[Dict[int, str]] = None):
        """Exibe resultados de detecção de comunidades."""
        self.community_text.delete("1.0", "end")
        self.community_text.insert("1.0", f"👥 Comunidades Detectadas: {len(communities)}\n")
        self.community_text.insert("end", f"📊 Modularidade Q:          {modularity:.4f}\n")
        self.community_text.insert("end", "=" * 50 + "\n\n")

        # Ordena comunidades por tamanho (maior primeiro)
        sorted_comms = sorted(communities, key=len, reverse=True)

        for idx, comm in enumerate(sorted_comms[:10], 1):
            self.community_text.insert("end", f"Comunidade {idx} — {len(comm)} membros:\n")
            if labels:
                member_names = [labels.get(m, str(m)) for m in comm[:8]]
            else:
                member_names = [str(m) for m in comm[:8]]
            members_str = ", ".join(member_names)
            if len(comm) > 8:
                members_str += f" ... (+{len(comm) - 8} mais)"
            self.community_text.insert("end", f"  {members_str}\n\n")

        if len(sorted_comms) > 10:
            self.community_text.insert("end", f"... e mais {len(sorted_comms) - 10} comunidades.\n")

    def show_bridging_ties(self, bridging_values: Dict[int, int], labels: Dict[int, str]):
        """Exibe Bridging Ties (nós conectores entre comunidades)."""
        self.community_text.delete("1.0", "end")
        self.community_text.insert("1.0", "🌉 Bridging Ties (Top 20 conectores)\n")
        self.community_text.insert("end", "=" * 50 + "\n\n")
        self.community_text.insert("end", f"{'Nó':<25} {'Comunidades Conectadas':>22}\n")
        self.community_text.insert("end", "-" * 50 + "\n")
        sorted_nodes = sorted(bridging_values.items(), key=lambda x: x[1], reverse=True)
        for node, comms_count in sorted_nodes[:20]:
            label = labels.get(node, str(node))
            self.community_text.insert("end", f"{label:<25} {comms_count:>22d}\n")

    # ==========================================
    # LIMPEZA
    # ==========================================

    def clear_all(self):
        """Limpa todos os painéis."""
        for textbox in (self.centrality_text, self.structure_text, self.community_text):
            textbox.delete("1.0", "end")

    def show_loading(self, metric_name: str):
        """Exibe mensagem de carregamento."""
        msg = f"⏳ Calculando {metric_name}...\n"
        for textbox in (self.centrality_text, self.structure_text, self.community_text):
            textbox.delete("1.0", "end")
            textbox.insert("1.0", msg)

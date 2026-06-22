"""Renderizador de grafos com suporte a múltiplos backends."""
import math
from typing import Dict, Tuple, Optional, List
from grafo.networkx_pure.adapter import GraphAdapter


class GraphRenderer:
    """Renderiza grafos em diferentes superfícies (Canvas CTk, Matplotlib, etc.)."""
    
    def __init__(self, adapter: GraphAdapter, positions: Dict[int, Tuple[float, float]]):
        self.adapter = adapter
        self.positions = positions
        self.node_colors: Dict[int, str] = {}
        self.edge_colors: Dict[Tuple[int, int], str] = {}
        self.node_sizes: Dict[int, float] = {}
        self.edge_widths: Dict[Tuple[int, int], float] = {}
        self.show_labels = True
        self.show_arrows = True
    
    def set_node_colors_by_metric(self, metric_values: Dict[int, float], 
                                   colormap: str = "blue_red"):
        """Define cores dos nós baseado em valores de métrica."""
        if not metric_values:
            return
        
        min_val = min(metric_values.values())
        max_val = max(metric_values.values())
        val_range = max_val - min_val if max_val > min_val else 1.0
        
        for node, val in metric_values.items():
            normalized = (val - min_val) / val_range
            
            if colormap == "blue_red":
                # Azul (baixo) → Vermelho (alto)
                r = int(255 * normalized)
                b = int(255 * (1 - normalized))
                color = f"#{r:02x}40{b:02x}"
            elif colormap == "viridis":
                # Verde-azulado → Amarelo
                r = int(255 * normalized)
                g = int(200 * (1 - abs(normalized - 0.5) * 2))
                b = int(255 * (1 - normalized))
                color = f"#{r:02x}{g:02x}{b:02x}"
            else:
                color = "#4A90E2"
            
            self.node_colors[node] = color
    
    def set_node_colors_by_community(self, communities: List[List[int]]):
        """Define cores dos nós baseado em comunidades."""
        palette = [
            "#4A90E2", "#E74C3C", "#2ECC71", "#F39C12", "#9B59B6",
            "#1ABC9C", "#E67E22", "#3498DB", "#E91E63", "#00BCD4"
        ]
        
        for c_idx, comm in enumerate(communities):
            color = palette[c_idx % len(palette)]
            for node in comm:
                self.node_colors[node] = color
    
    def set_edge_widths_by_weight(self):
        """Define espessura das arestas baseado no peso."""
        for u in self.adapter.nodes():
            for v in self.adapter.successors(u):
                try:
                    weight = self.adapter._g.get_edge_weight(u, v)
                    # Normaliza para espessura entre 0.5 e 4.0
                    width = max(0.5, min(4.0, weight * 0.8))
                    self.edge_widths[(u, v)] = width
                except:
                    self.edge_widths[(u, v)] = 1.0
    
    def set_node_sizes_by_degree(self):
        """Define tamanho dos nós baseado no grau total."""
        degrees = {}
        for node in self.adapter.nodes():
            degrees[node] = self.adapter.in_degree(node) + self.adapter.out_degree(node)
        
        if not degrees:
            return
        
        max_deg = max(degrees.values())
        min_deg = min(degrees.values())
        deg_range = max_deg - min_deg if max_deg > min_deg else 1.0
        
        for node, deg in degrees.items():
            normalized = (deg - min_deg) / deg_range
            # Tamanho entre 8 e 20 pixels
            size = 8 + normalized * 12
            self.node_sizes[node] = size
    
    def render_to_svg(self, filepath: str, width: int = 800, height: int = 600):
        """Exporta grafo como SVG."""
        svg_lines = [
            f'<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
            f'<rect width="{width}" height="{height}" fill="white"/>'
        ]
        
        # Calcula bounds e escala
        xs = [p[0] for p in self.positions.values()]
        ys = [p[1] for p in self.positions.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        graph_w = max_x - min_x if max_x > min_x else 1
        graph_h = max_y - min_y if max_y > min_y else 1
        
        scale = min((width - 100) / graph_w, (height - 100) / graph_h)
        offset_x = (width - graph_w * scale) / 2 - min_x * scale
        offset_y = (height - graph_h * scale) / 2 - min_y * scale
        
        def to_svg(x, y):
            return (x * scale + offset_x, y * scale + offset_y)
        
        # Desenha arestas
        for u in self.adapter.nodes():
            for v in self.adapter.successors(u):
                if u in self.positions and v in self.positions:
                    x1, y1 = to_svg(*self.positions[u])
                    x2, y2 = to_svg(*self.positions[v])
                    width_edge = self.edge_widths.get((u, v), 1.0)
                    color = self.edge_colors.get((u, v), "#666")
                    
                    if self.show_arrows:
                        # Calcula ponto final ajustado (para não sobrepor o nó)
                        dx = x2 - x1
                        dy = y2 - y1
                        dist = math.hypot(dx, dy)
                        if dist > 0:
                            node_size = self.node_sizes.get(v, 10)
                            x2_adj = x2 - (dx / dist) * node_size
                            y2_adj = y2 - (dy / dist) * node_size
                        else:
                            x2_adj, y2_adj = x2, y2
                        
                        svg_lines.append(
                            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2_adj:.2f}" y2="{y2_adj:.2f}" '
                            f'stroke="{color}" stroke-width="{width_edge:.2f}" marker-end="url(#arrow)"/>'
                        )
                    else:
                        svg_lines.append(
                            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
                            f'stroke="{color}" stroke-width="{width_edge:.2f}"/>'
                        )
        
        # Desenha nós
        for node, (x, y) in self.positions.items():
            sx, sy = to_svg(x, y)
            size = self.node_sizes.get(node, 10)
            color = self.node_colors.get(node, "#4A90E2")
            
            svg_lines.append(
                f'<circle cx="{sx:.2f}" cy="{sy:.2f}" r="{size:.2f}" '
                f'fill="{color}" stroke="#333" stroke-width="1"/>'
            )
            
            if self.show_labels:
                label = self.adapter._g.vertex_labels.get(node, str(node))
                if len(label) > 10:
                    label = label[:9] + "…"
                svg_lines.append(
                    f'<text x="{sx:.2f}" y="{sy + size + 12:.2f}" '
                    f'text-anchor="middle" font-size="8" font-family="Arial">{label}</text>'
                )
        
        # Define marker de seta
        svg_lines.insert(2, '''
<defs>
  <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
    <path d="M0,0 L0,6 L9,3 z" fill="#666"/>
  </marker>
</defs>
''')
        
        svg_lines.append('</svg>')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(svg_lines))
    
    def render_to_matplotlib(self, ax, title: str = "Grafo"):
        """Renderiza grafo em eixo do matplotlib."""
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        
        # Desenha arestas
        for u in self.adapter.nodes():
            for v in self.adapter.successors(u):
                if u in self.positions and v in self.positions:
                    x1, y1 = self.positions[u]
                    x2, y2 = self.positions[v]
                    width = self.edge_widths.get((u, v), 1.0)
                    color = self.edge_colors.get((u, v), "#666")
                    
                    if self.show_arrows:
                        dx = x2 - x1
                        dy = y2 - y1
                        dist = math.hypot(dx, dy)
                        if dist > 0:
                            node_size = self.node_sizes.get(v, 10) / 50
                            x2_adj = x2 - (dx / dist) * node_size
                            y2_adj = y2 - (dy / dist) * node_size
                        else:
                            x2_adj, y2_adj = x2, y2
                        
                        ax.annotate("", xy=(x2_adj, y2_adj), xytext=(x1, y1),
                                   arrowprops=dict(arrowstyle="->", color=color, lw=width))
                    else:
                        ax.plot([x1, x2], [y1, y2], color=color, linewidth=width)
        
        # Desenha nós
        for node, (x, y) in self.positions.items():
            size = self.node_sizes.get(node, 10)
            color = self.node_colors.get(node, "#4A90E2")
            
            circle = plt.Circle((x, y), size / 50, color=color, ec='black', linewidth=1)
            ax.add_patch(circle)
            
            if self.show_labels:
                label = self.adapter._g.vertex_labels.get(node, str(node))
                if len(label) > 8:
                    label = label[:7] + "…"
                ax.text(x, y - size / 30, label, ha='center', va='top', fontsize=6)
        
        ax.set_title(title)
        ax.set_aspect('equal')
        ax.axis('off')
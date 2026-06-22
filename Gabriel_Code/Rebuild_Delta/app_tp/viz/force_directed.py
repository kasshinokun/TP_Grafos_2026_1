"""Layout force-directed (Fruchterman-Reingold)."""
import random
import math
from typing import Dict, Tuple


class ForceDirectedLayout:
    """Calcula posições usando forças atrativas/repulsivas."""
    
    def __init__(self, adapter, width: float = 800, height: float = 600):
        self.adapter = adapter
        self.width = width
        self.height = height
        self.area = width * height
        self.k = math.sqrt(self.area / max(1, adapter.number_of_nodes()))
    
    def compute(self, iterations: int = 100) -> Dict[int, Tuple[float, float]]:
        """Executa o algoritmo e retorna {node: (x, y)}."""
        nodes = self.adapter.nodes()
        n = len(nodes)
        if n == 0:
            return {}
        
        # Inicialização aleatória
        pos = {v: (random.uniform(0, self.width), random.uniform(0, self.height)) for v in nodes}
        
        temp = self.width / 10  # Temperatura inicial
        
        for iteration in range(iterations):
            # Forças repulsivas (todos contra todos)
            disp = {v: [0.0, 0.0] for v in nodes}
            
            for i, u in enumerate(nodes):
                for v in nodes[i + 1:]:
                    dx = pos[u][0] - pos[v][0]
                    dy = pos[u][1] - pos[v][1]
                    dist = max(0.01, math.hypot(dx, dy))
                    # Força repulsiva: k² / dist
                    force = (self.k * self.k) / dist
                    fx = (dx / dist) * force
                    fy = (dy / dist) * force
                    disp[u][0] += fx
                    disp[u][1] += fy
                    disp[v][0] -= fx
                    disp[v][1] -= fy
            
            # Forças atrativas (arestas)
            for u in nodes:
                for v in self.adapter.neighbors(u):
                    if u < v:  # Evita duplicação
                        dx = pos[u][0] - pos[v][0]
                        dy = pos[u][1] - pos[v][1]
                        dist = max(0.01, math.hypot(dx, dy))
                        # Força atrativa: dist² / k
                        force = (dist * dist) / self.k
                        fx = (dx / dist) * force
                        fy = (dy / dist) * force
                        disp[u][0] -= fx
                        disp[u][1] -= fy
                        disp[v][0] += fx
                        disp[v][1] += fy
            
            # Aplica deslocamentos limitados pela temperatura
            for v in nodes:
                dx, dy = disp[v]
                dist = max(0.01, math.hypot(dx, dy))
                limited_dx = (dx / dist) * min(dist, temp)
                limited_dy = (dy / dist) * min(dist, temp)
                
                new_x = pos[v][0] + limited_dx
                new_y = pos[v][1] + limited_dy
                # Mantém dentro dos limites
                new_x = max(0, min(self.width, new_x))
                new_y = max(0, min(self.height, new_y))
                pos[v] = (new_x, new_y)
            
            # Resfriamento
            temp *= 0.95
        
        return pos
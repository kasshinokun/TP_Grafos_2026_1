from abc import ABC, abstractmethod
import json
import os # Default lib to manage files 
import os.path as manager          # Alias for os.path to shorten repeated calls
from os.path import join as concat_path # Alias specifically for os.path.join
from os.path import abspath as absoluto # Alias specifically for os.path.abspath

# ============================
# FUNÇÕES AUXILIARES
# ============================
def get_absoluto(file:str):
    return manager.dirname(absoluto(file))

def get_diretory(name_diretory:str, condition:int = 2)->str:
    APP_DIR = get_absoluto(__file__)
    if condition == 1:
        return concat_path(APP_DIR, name_diretory)
    else:
        DATA_DIR = concat_path(APP_DIR, name_diretory)
        os.makedirs(DATA_DIR, exist_ok=True)
        return DATA_DIR
    
class AbstractGraph(ABC):
    def __init__(self, num_vertices):
        if num_vertices < 0:
            raise ValueError("O número de vértices não pode ser negativo.")
        self.num_vertices = num_vertices
        self.num_edges = 0
        self.vertex_weights = [0.0] * num_vertices
        self.vertex_labels = [None] * num_vertices
        self.app_dir = get_absoluto(__file__)

    def _validate_index(self, *indices):
        for i in indices:
            if not (0 <= i < self.num_vertices):
                raise IndexError(f"Índice de vértice inválido: {i}")

    def getVertexCount(self):
        return self.num_vertices

    def getEdgeCount(self):
        return self.num_edges

    @abstractmethod
    def hasEdge(self, u, v):
        pass

    @abstractmethod
    def addEdge(self, u, v):
        pass

    @abstractmethod
    def removeEdge(self, u, v):
        pass

    def isSucessor(self, u, v):
        return self.hasEdge(u, v)

    def isPredessor(self, u, v):
        return self.hasEdge(v, u)

    def isDivergent(self, u1, v1, u2, v2):
        # Dois arcos são divergentes se possuem a mesma origem mas destinos diferentes
        self._validate_index(u1, v1, u2, v2)
        return u1 == u2 and v1 != v2 and self.hasEdge(u1, v1) and self.hasEdge(u2, v2)

    def isConvergent(self, u1, v1, u2, v2):
        # Dois arcos são convergentes se possuem destinos iguais mas origens diferentes
        self._validate_index(u1, v1, u2, v2)
        return v1 == v2 and u1 != u2 and self.hasEdge(u1, v1) and self.hasEdge(u2, v2)

    def isIncident(self, u, v, x):
        # Uma aresta (u, v) é incidente a um vértice x se x é u ou v
        self._validate_index(u, v, x)
        return (x == u or x == v) and self.hasEdge(u, v)

    @abstractmethod
    def getVertexInDegree(self, u):
        pass

    @abstractmethod
    def getVertexOutDegree(self, u):
        pass

    def setVertexWeight(self, v, w):
        self._validate_index(v)
        self.vertex_weights[v] = w

    def getVertexWeight(self, v):
        self._validate_index(v)
        return self.vertex_weights[v]

    @abstractmethod
    def setEdgeWeight(self, u, v, w):
        pass

    @abstractmethod
    def getEdgeWeight(self, u, v):
        pass

    def isConnected(self):
        # Para um grafo direcionado, verificamos a conectividade fraca (tratando como não direcionado)
        if self.num_vertices == 0:
            return True
        
        visited = [False] * self.num_vertices
        queue = [0]
        visited[0] = True
        count = 1
        
        while queue:
            curr = queue.pop(0)
            for neighbor in range(self.num_vertices):
                if not visited[neighbor]:
                    if self.hasEdge(curr, neighbor) or self.hasEdge(neighbor, curr):
                        visited[neighbor] = True
                        count += 1
                        queue.append(neighbor)
        
        return count == self.num_vertices

    def isEmptyGraph(self):
        return self.num_edges == 0

    def isCompleteGraph(self):
        # Um grafo direcionado simples é completo se para todo par (u, v) com u != v, existe u->v E v->u
        if self.num_vertices <= 1:
            return True
        expected_edges = self.num_vertices * (self.num_vertices - 1)
        return self.num_edges == expected_edges

    def exportToGEPHI(self, path):
        # Exporta no formato GEXF (um dos formatos aceitos pelo Gephi)
        with open(concat_path(self.app_dir,path), 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<gexf xmlns="http://www.gexf.net/1.2draft" version="1.2">\n')
            f.write('  <graph mode="static" defaultedgetype="directed">\n')
            
            f.write('    <nodes>\n')
            for i in range(self.num_vertices):
                label = self.vertex_labels[i] if self.vertex_labels[i] else f"V{i}"
                f.write(f'      <node id="{i}" label="{label}" />\n')
            f.write('    </nodes>\n')
            
            f.write('    <edges>\n')
            edge_id = 0
            for u in range(self.num_vertices):
                for v in range(self.num_vertices):
                    if self.hasEdge(u, v):
                        weight = self.getEdgeWeight(u, v)
                        f.write(f'      <edge id="{edge_id}" source="{u}" target="{v}" weight="{weight}" />\n')
                        edge_id += 1
            f.write('    </edges>\n')
            
            f.write('  </graph>\n')
            f.write('</gexf>\n')

class AdjacencyMatrixGraph(AbstractGraph):
    def __init__(self, num_vertices):
        super().__init__(num_vertices)
        self.matrix = [[0.0 for _ in range(num_vertices)] for _ in range(num_vertices)]

    def hasEdge(self, u, v):
        self._validate_index(u, v)
        return self.matrix[u][v] > 0

    def addEdge(self, u, v):
        self._validate_index(u, v)
        if u == v:
            raise ValueError("Não são permitidos laços.")
        if not self.hasEdge(u, v):
            self.matrix[u][v] = 1.0
            self.num_edges += 1

    def removeEdge(self, u, v):
        self._validate_index(u, v)
        if self.hasEdge(u, v):
            self.matrix[u][v] = 0.0
            self.num_edges -= 1

    def getVertexInDegree(self, u):
        self._validate_index(u)
        degree = 0
        for row in range(self.num_vertices):
            if self.matrix[row][u] > 0:
                degree += 1
        return degree

    def getVertexOutDegree(self, u):
        self._validate_index(u)
        degree = 0
        for col in range(self.num_vertices):
            if self.matrix[u][col] > 0:
                degree += 1
        return degree

    def setEdgeWeight(self, u, v, w):
        self._validate_index(u, v)
        if not self.hasEdge(u, v):
            raise ValueError("Aresta não existe.")
        self.matrix[u][v] = float(w)

    def getEdgeWeight(self, u, v):
        self._validate_index(u, v)
        return self.matrix[u][v]

class AdjacencyListGraph(AbstractGraph):
    def __init__(self, num_vertices):
        super().__init__(num_vertices)
        self.adj = [{} for _ in range(num_vertices)]

    def hasEdge(self, u, v):
        self._validate_index(u, v)
        return v in self.adj[u]

    def addEdge(self, u, v):
        self._validate_index(u, v)
        if u == v:
            raise ValueError("Não são permitidos laços.")
        if not self.hasEdge(u, v):
            self.adj[u][v] = 1.0
            self.num_edges += 1

    def removeEdge(self, u, v):
        self._validate_index(u, v)
        if self.hasEdge(u, v):
            del self.adj[u][v]
            self.num_edges -= 1

    def getVertexInDegree(self, u):
        self._validate_index(u)
        degree = 0
        for i in range(self.num_vertices):
            if u in self.adj[i]:
                degree += 1
        return degree

    def getVertexOutDegree(self, u):
        self._validate_index(u)
        return len(self.adj[u])

    def setEdgeWeight(self, u, v, w):
        self._validate_index(u, v)
        if not self.hasEdge(u, v):
            raise ValueError("Aresta não existe.")
        self.adj[u][v] = float(w)

    def getEdgeWeight(self, u, v):
        self._validate_index(u, v)
        return self.adj[u].get(v, 0.0)

"""Classe base abstrata para mineradores de repositórios GitHub."""
from abc import ABC, abstractmethod
from typing import Optional, Callable, List, Dict, Any
from grafo.graph.adjacency_list_graph import AdjacencyListGraph


class BaseMiner(ABC):
    """Interface comum para todos os mineradores."""
    
    def __init__(self, repo_owner: str, repo_name: str, 
                 on_progress: Optional[Callable[[float, str], None]] = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.on_progress = on_progress
        
        self.graph: Optional[AdjacencyListGraph] = None
        self.is_running = False
        self.is_cancelled = False
        
        # Pesos das interações (conforme PDF)
        self.weights = {
            'comment': 2,
            'issue_commented': 3,
            'review': 4,
            'merge': 5
        }
        
        # Estatísticas
        self.stats = {
            'issues_fetched': 0,
            'prs_fetched': 0,
            'comments_fetched': 0,
            'reviews_fetched': 0,
            'users_discovered': 0,
            'edges_created': 0
        }
    
    @abstractmethod
    def run(self) -> AdjacencyListGraph:
        """Executa a mineração completa."""
        pass
    
    @abstractmethod
    def _fetch_issues(self) -> List[Dict[str, Any]]:
        """Busca issues do repositório."""
        pass
    
    @abstractmethod
    def _fetch_pull_requests(self) -> List[Dict[str, Any]]:
        """Busca pull requests do repositório."""
        pass
    
    @abstractmethod
    def _fetch_comments(self, issue_number: int) -> List[Dict[str, Any]]:
        """Busca comentários de uma issue/PR."""
        pass
    
    @abstractmethod
    def _fetch_reviews(self, pr_number: int) -> List[Dict[str, Any]]:
        """Busca revisões de um pull request."""
        pass
    
    def cancel(self):
        """Cancela a mineração em andamento."""
        self.is_cancelled = True
    
    def _report_progress(self, progress: float, message: str):
        """Reporta progresso para o callback."""
        if self.on_progress:
            self.on_progress(progress, message)
    
    def _build_graph_from_interactions(self, interactions: List[Dict[str, Any]]) -> AdjacencyListGraph:
        """Constrói grafo a partir de lista de interações."""
        # Coleta usuários únicos
        users = set()
        for interaction in interactions:
            users.add(interaction['author'])
            if 'mentions' in interaction:
                users.update(interaction['mentions'])
            if 'assignees' in interaction:
                users.update(interaction['assignees'])
        
        user_list = sorted(users)
        user_to_idx = {u: i for i, u in enumerate(user_list)}
        
        G = AdjacencyListGraph(len(user_list))
        for i, u in enumerate(user_list):
            G.vertex_labels[i] = u
        
        self.stats['users_discovered'] = len(user_list)
        
        # Adiciona arestas com pesos
        for interaction in interactions:
            if self.is_cancelled:
                break
            
            src = user_to_idx[interaction['author']]
            weight = self.weights.get(interaction['type'], 1)
            
            targets = set()
            if 'mentions' in interaction:
                targets.update(interaction['mentions'])
            if 'assignees' in interaction:
                targets.update(interaction['assignees'])
            
            for target_user in targets:
                tgt = user_to_idx[target_user]
                if src != tgt:
                    if G.has_edge(src, tgt):
                        current = G.get_edge_weight(src, tgt)
                        G.set_edge_weight(src, tgt, current + weight)
                    else:
                        G.add_edge(src, tgt)
                        G.set_edge_weight(src, tgt, weight)
                    self.stats['edges_created'] += 1
        
        return G
    
    def get_stats(self) -> Dict[str, int]:
        """Retorna estatísticas da mineração."""
        return self.stats.copy()
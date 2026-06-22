"""Minerador híbrido com checkpointing."""
import threading
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from grafo.graph.adjacency_list_graph import AdjacencyListGraph
from miner.checkpoint import CheckpointManager
from miner.rate_limiter import GitHubRateLimiter


class HybridMiner:
    """Minerador que usa threads para I/O e processos para CPU."""
    
    def __init__(self, repo_owner: str, repo_name: str, tokens: list,
                 on_progress: Optional[Callable] = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.rate_limiter = GitHubRateLimiter(tokens)
        self.on_progress = on_progress
        
        self.graph: Optional[AdjacencyListGraph] = None
        self.checkpoint = CheckpointManager(interval_seconds=60)
        
        # Pesos das interações (conforme PDF)
        self.weights = {
            'comment': 2,
            'issue_commented': 3,
            'review': 4,
            'merge': 5
        }
    
    def run_with_checkpoint(self, checkpoint_interval: int = 60) -> AdjacencyListGraph:
        """Executa mineração com checkpoint periódico."""
        self.checkpoint.interval = checkpoint_interval
        
        # Tenta retomar de checkpoint
        state = self.checkpoint.load_latest(f"{self.repo_owner}_{self.repo_name}")
        if state:
            self.graph = state['graph']
            processed_issues = state.get('processed_issues', set())
            if self.on_progress:
                self.on_progress(0.3, "Retomando de checkpoint...")
        else:
            self.graph = None
            processed_issues = set()
        
        # Fase 1: Coleta de issues/PRs (I/O bound → threads)
        interactions = self._fetch_interactions(processed_issues)
        
        # Fase 2: Construção do grafo (CPU bound → processos)
        self.graph = self._build_graph(interactions)
        
        # Checkpoint final
        self.checkpoint.save({
            'graph': self.graph,
            'processed_issues': set()  # Tudo processado
        }, f"{self.repo_owner}_{self.repo_name}")
        
        return self.graph
    
    def _fetch_interactions(self, already_processed: set) -> list:
        """Fase 1: Busca dados da API (multithread)."""
        interactions = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Busca issues
            futures = []
            for page in range(1, 11):  # Exemplo: 10 páginas
                token = self.rate_limiter.get_token()
                futures.append(executor.submit(
                    self._fetch_issues_page, page, token
                ))
            
            for f in futures:
                result = f.result()
                if result:
                    interactions.extend(result)
        
        return interactions
    
    def _fetch_issues_page(self, page: int, token: str) -> list:
        """Busca uma página de issues (simulado)."""
        # Implementação real usaria requests + API do GitHub
        return []
    
    def _build_graph(self, interactions: list) -> AdjacencyListGraph:
        """Fase 2: Constrói grafo ponderado."""
        # Coleta nós únicos
        users = set()
        for interaction in interactions:
            users.add(interaction['author'])
            if 'mentions' in interaction:
                users.update(interaction['mentions'])
        
        user_list = sorted(users)
        user_to_idx = {u: i for i, u in enumerate(user_list)}
        
        G = AdjacencyListGraph(len(user_list))
        for i, u in enumerate(user_list):
            G.vertex_labels[i] = u
        
        # Adiciona arestas com pesos
        for interaction in interactions:
            src = user_to_idx[interaction['author']]
            weight = self.weights.get(interaction['type'], 1)
            
            for mention in interaction.get('mentions', []):
                tgt = user_to_idx[mention]
                if src != tgt:
                    if G.has_edge(src, tgt):
                        # Soma peso (acumula interações)
                        current = G.get_edge_weight(src, tgt)
                        G.set_edge_weight(src, tgt, current + weight)
                    else:
                        G.add_edge(src, tgt)
                        G.set_edge_weight(src, tgt, weight)
        
        return G
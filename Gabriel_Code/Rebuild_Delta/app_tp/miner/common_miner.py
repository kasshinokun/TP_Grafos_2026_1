"""Minerador multithread otimizado com suporte a múltiplos tokens e paralelismo escalonado."""
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import requests

from miner.base_miner import BaseMiner
from miner.rate_limiter import GitHubRateLimiter
from grafo.graph.adjacency_list_graph import AdjacencyListGraph


class CommonMiner(BaseMiner):
    """Minerador que usa ThreadPoolExecutor com escalonamento de tokens."""

    # Regra de nome de usuário do GitHub: alfanumérico, hífens permitidos
    # (não em sequência, nem nas pontas) — usado para extrair @mentions.
    _MENTION_RE = re.compile(r'@([A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)')
    
    def __init__(self, repo_owner: str, repo_name: str, tokens: List[str],
                 on_progress: Optional[callable] = None, max_workers: Optional[int] = None):
        super().__init__(repo_owner, repo_name, on_progress)
        self.tokens = tokens
        self.rate_limiter = GitHubRateLimiter(tokens)
        
        # Lógica solicitada: 3 a 8 threads paralelas que são triplicadas
        # Se não especificado, calculamos com base no número de tokens
        num_tokens = len(tokens)
        base_threads = max(3, min(8, num_tokens))
        self.max_workers = max_workers or (base_threads * 3)
        
        self.session = requests.Session()
        self.interactions: List[Dict[str, Any]] = []
    
    def run(self) -> AdjacencyListGraph:
        """Executa mineração completa."""
        self.is_running = True
        self.is_cancelled = False
        
        try:
            self._report_progress(0.0, f"Iniciando mineração com {len(self.tokens)} tokens e {self.max_workers} threads...")
            
            # Fase 1: Busca issues e PRs
            self._report_progress(0.1, "Buscando issues e pull requests...")
            issues = self._fetch_issues()
            prs = self._fetch_pull_requests()
            
            if self.is_cancelled:
                return self._build_empty_graph()
            
            # Fase 2: Busca comentários e revisões
            self._report_progress(0.3, "Buscando detalhes das interações...")
            interactions = []
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                # Submete busca de comentários de issues
                for issue in issues:
                    if self.is_cancelled:
                        break
                    futures.append(executor.submit(self._process_issue, issue))
                
                # Submete busca de revisões de PRs
                for pr in prs:
                    if self.is_cancelled:
                        break
                    futures.append(executor.submit(self._process_pr, pr))
                
                # Coleta resultados
                total = len(futures)
                completed = 0
                for future in as_completed(futures):
                    if self.is_cancelled:
                        break
                    
                    try:
                        result = future.result()
                        if result:
                            interactions.extend(result)
                    except Exception as e:
                        print(f"Erro em thread: {e}")
                    
                    completed += 1
                    progress = 0.3 + (completed / total) * 0.6
                    if completed % 5 == 0: # Reduz verbosidade do log
                        self._report_progress(progress, f"Processando detalhes: {completed}/{total}...")
            
            if self.is_cancelled:
                return self._build_empty_graph()
            
            # Fase 3: Constrói grafo
            self._report_progress(0.9, "Construindo grafo de interações...")
            self.interactions = interactions
            self.graph = self._build_graph_from_interactions(interactions)
            
            self._report_progress(1.0, "Mineração concluída!")
            return self.graph
        
        finally:
            self.is_running = False
    
    def _fetch_issues(self) -> List[Dict[str, Any]]:
        """Busca issues do repositório com rotação de tokens."""
        issues = []
        page = 1
        per_page = 100
        
        while True:
            if self.is_cancelled:
                break
            
            token = self.rate_limiter.get_token()
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues"
            params = {'state': 'all', 'per_page': per_page, 'page': page}
            headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
            
            try:
                response = self.session.get(url, params=params, headers=headers, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if not data: break
                    for item in data:
                        if 'pull_request' not in item:
                            issues.append(item)
                            self.stats['issues_fetched'] += 1
                    if len(data) < per_page: break  # última página
                    page += 1
                    if page > 5: break # Limite para protótipo
                elif response.status_code == 403:
                    time.sleep(2) # Pequena espera antes de tentar outro token
                else:
                    break
            except Exception:
                break
        return issues
    
    def _fetch_pull_requests(self) -> List[Dict[str, Any]]:
        """Busca pull requests com rotação de tokens."""
        prs = []
        page = 1
        per_page = 100
        
        while True:
            if self.is_cancelled:
                break
            
            token = self.rate_limiter.get_token()
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls"
            params = {'state': 'all', 'per_page': per_page, 'page': page}
            headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
            
            try:
                response = self.session.get(url, params=params, headers=headers, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    if not data: break
                    prs.extend(data)
                    self.stats['prs_fetched'] += len(data)
                    if len(data) < per_page: break  # última página
                    page += 1
                    if page > 5: break
                else:
                    break
            except Exception:
                break
        return prs

    def _fetch_comments(self, issue_number: int) -> List[Dict[str, Any]]:
        token = self.rate_limiter.get_token()
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{issue_number}/comments"
        headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.stats['comments_fetched'] += len(data)
                return data
        except Exception: pass
        return []

    def _fetch_reviews(self, pr_number: int) -> List[Dict[str, Any]]:
        token = self.rate_limiter.get_token()
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}/reviews"
        headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
        try:
            response = self.session.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.stats['reviews_fetched'] += len(data)
                return data
        except Exception: pass
        return []

    def _extract_mentions(self, text: str) -> List[str]:
        """Extrai menções @usuario de um texto (corpo de comentário), em
        ordem de aparição e sem duplicatas."""
        if not text:
            return []
        seen = []
        for m in self._MENTION_RE.finditer(text):
            user = m.group(1)
            if user not in seen:
                seen.append(user)
        return seen

    def _process_issue(self, issue: Dict[str, Any]) -> List[Dict[str, Any]]:
        interactions = []
        author = issue['user']['login']

        # Grafo 1 — comentários em issues/PRs
        comments = self._fetch_comments(issue['number'])
        for c in comments:
            commenter = c['user']['login']
            if commenter != author:
                interactions.append({'type': 'comment', 'author': commenter, 'mentions': [author]})
            # Menções @usuario dentro do corpo do comentário também contam
            for mentioned in self._extract_mentions(c.get('body', '')):
                if mentioned != commenter:
                    interactions.append({'type': 'comment', 'author': commenter, 'mentions': [mentioned]})

        # Grafo 2 — fechamento de issue por outro usuário
        closed_by = (issue.get('closed_by') or {}).get('login')
        if issue.get('state') == 'closed' and closed_by and closed_by != author:
            interactions.append({'type': 'issue_commented', 'author': closed_by, 'mentions': [author]})

        return interactions

    def _process_pr(self, pr: Dict[str, Any]) -> List[Dict[str, Any]]:
        interactions = []
        author = pr['user']['login']

        # Grafo 1 — comentários em PRs (issue comments do PR)
        comments = self._fetch_comments(pr['number'])
        for c in comments:
            commenter = c['user']['login']
            if commenter != author:
                interactions.append({'type': 'comment', 'author': commenter, 'mentions': [author]})
            for mentioned in self._extract_mentions(c.get('body', '')):
                if mentioned != commenter:
                    interactions.append({'type': 'comment', 'author': commenter, 'mentions': [mentioned]})

        # Grafo 3 — revisões/aprovações de PR
        reviews = self._fetch_reviews(pr['number'])
        for r in reviews:
            if r['user']['login'] != author:
                interactions.append({'type': 'review', 'author': r['user']['login'], 'mentions': [author]})

        # Grafo 3 — merge de PR
        merged_by = (pr.get('merged_by') or {}).get('login')
        if pr.get('merged') and merged_by and merged_by != author:
            interactions.append({'type': 'merge', 'author': merged_by, 'mentions': [author]})

        return interactions

    def _build_empty_graph(self) -> AdjacencyListGraph:
        return AdjacencyListGraph(0)

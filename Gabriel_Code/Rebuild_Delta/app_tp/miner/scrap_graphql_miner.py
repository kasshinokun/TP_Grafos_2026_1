import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


class ScrapGraphQL:
    """
    Consulta a API GraphQL do GitHub para obter estatísticas do repositório,
    como total de issues, PRs e idade do projeto.
    Utiliza rotação simples de tokens para evitar estouro de limite.
    """

    def __init__(self, tokens: List[str], owner: str, repo: str,
                 on_progress: Optional[callable] = None):
        self.tokens = tokens
        self.owner = owner
        self.repo = repo
        self.on_progress = on_progress
        self._token_index = 0
        # Status de pré-voo, populado por fetch_metadata()
        self.last_viewer_login: Optional[str] = None
        self.last_rate_limit: Optional[Dict[str, Any]] = None

    def _next_token(self) -> str:
        """Retorna o próximo token em round-robin."""
        if not self.tokens:
            raise IndexError("Nenhum token disponível em ScrapGraphQL.")
        token = self.tokens[self._token_index % len(self.tokens)]
        self._token_index += 1
        return token

    def _graphql_request(self, query: str, variables: Dict = None) -> Dict[str, Any]:
        """Executa uma requisição GraphQL autenticada com rotação de tokens."""
        token = self._next_token()
        url = "https://api.github.com/graphql"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"GraphQL error {response.status_code}: {response.text}")

    def fetch_metadata(self) -> Dict[str, Any]:
        """
        Obtém a data de criação e as contagens totais de issues e pull requests.
        Também consulta, na mesma chamada, o status da API (rateLimit) e o
        usuário autenticado pelo token em uso — usado para apurar o status
        de acesso ANTES de iniciar a mineração REST.
        """
        query = """
        query($owner: String!, $repo: String!) {
            viewer { login }
            rateLimit { limit cost remaining resetAt }
            repository(owner: $owner, name: $repo) {
                createdAt
                issues(states: [OPEN, CLOSED]) {
                    totalCount
                }
                pullRequests(states: [OPEN, CLOSED, MERGED]) {
                    totalCount
                }
            }
        }
        """
        variables = {"owner": self.owner, "repo": self.repo}
        result = self._graphql_request(query, variables)
        payload = result.get("data") or {}

        # Status de pré-voo (token/quota), guardado para consulta posterior
        self.last_viewer_login = (payload.get("viewer") or {}).get("login")
        self.last_rate_limit = payload.get("rateLimit")

        data = payload.get("repository")
        if not data:
            errors = result.get("errors")
            msg = errors[0]["message"] if errors else "dados indisponíveis"
            raise Exception(f"Repositório não encontrado ou {msg}")
        return data

    def compute_limits(self) -> Dict[str, Any]:
        """
        Calcula os limites a serem usados na interface:
        - total_items: soma de issues + PRs
        - max_years: idade do repositório em anos (inteiro, mínimo 1, máximo 5)
        - created_at, age_years (float) etc.
        """
        meta = self.fetch_metadata()
        created_at = meta.get("createdAt")
        total_issues = meta.get("issues", {}).get("totalCount", 0)
        total_prs = meta.get("pullRequests", {}).get("totalCount", 0)
        total_items = total_issues + total_prs

        # Calcular idade em anos
        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        age_years = (now - created).days / 365.25

        # Limitar a 5 anos e arredondar para cima (mínimo 1)
        max_years = min(5, int(age_years) + 1 if age_years > int(age_years) else int(age_years))
        if max_years < 1:
            max_years = 1

        return {
            "total_issues": total_issues,
            "total_prs": total_prs,
            "total_items": total_items,
            "created_at": created_at,
            "age_years": age_years,
            "max_years": max_years,
            "max_items": total_items,      # limite superior para o campo de registros
            "viewer_login": self.last_viewer_login,
            "rate_limit": self.last_rate_limit,
        }

    def check_status(self) -> Dict[str, Any]:
        """Apuração de status ANTES da mineração: valida o token (via
        `viewer.login`), consulta a quota atual da API (`rateLimit`) e
        confirma a existência do repositório — tudo em uma única
        requisição GraphQL. Use isto como pré-voo antes de chamar
        CommonMiner.run() (que consome a API REST)."""
        repo_meta = self.fetch_metadata()
        rl = self.last_rate_limit or {}
        return {
            "ok": True,
            "viewer_login": self.last_viewer_login,
            "repo_exists": True,
            "remaining": rl.get("remaining"),
            "limit": rl.get("limit"),
            "reset_at": rl.get("resetAt"),
            "repo_created_at": repo_meta.get("createdAt"),
            "total_issues": repo_meta.get("issues", {}).get("totalCount"),
            "total_prs": repo_meta.get("pullRequests", {}).get("totalCount"),
        }

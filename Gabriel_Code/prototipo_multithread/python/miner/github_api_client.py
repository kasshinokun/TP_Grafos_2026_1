import requests
import time
import random
from collections import deque

class GitHubApiClient:
    def __init__(self, tokens):
        if not tokens:
            raise ValueError("A lista de tokens não pode ser vazia.")
        self.tokens = deque(tokens)
        self.current_token = self.tokens[0]
        self.token_status = {token: {'remaining': 5000, 'reset': 0} for token in tokens} # Default for authenticated users
        self.base_url_rest = "https://api.github.com"
        self.base_url_graphql = "https://api.github.com/graphql"

    def _get_headers(self):
        return {
            "Authorization": f"token {self.current_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _rotate_token(self):
        self.tokens.rotate(-1) # Move current token to the end
        self.current_token = self.tokens[0]
        print(f"Token rotacionado. Novo token atual: {self.current_token[:5]}...")

    def _handle_rate_limit(self, response):
        remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
        reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
        
        self.token_status[self.current_token]["remaining"] = remaining
        self.token_status[self.current_token]["reset"] = reset_time

        if remaining == 0:
            sleep_time = max(0, reset_time - time.time()) + 1 # Add 1 second buffer
            print(f"Limite de taxa atingido para o token {self.current_token[:5]}... Aguardando {sleep_time:.2f} segundos.")
            time.sleep(sleep_time)
            self._rotate_token()
            return True
        return False

    def _make_request(self, method, url, params=None, json=None, is_graphql=False, retries=3):
        for attempt in range(retries + 1):
            headers = self._get_headers()
            try:
                if is_graphql:
                    response = requests.post(url, headers=headers, json=json, timeout=30)
                else:
                    response = requests.request(method, url, headers=headers, params=params, json=json, timeout=30)
                
                if response and self._handle_rate_limit(response):
                    continue # Retry with new token after waiting

                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
                return response
            except requests.exceptions.HTTPError as e:
                if response.status_code in [403, 429]:
                    print(f"Erro de Rate Limit/Forbidden ({response.status_code}) para o token {self.current_token[:5]}... na tentativa {attempt+1}.")
                    if self._handle_rate_limit(response): # This will also rotate token
                        continue
                print(f"Erro HTTP na requisição ({response.status_code}): {e} na tentativa {attempt+1}.")
            except requests.exceptions.ConnectionError as e:
                print(f"Erro de conexão: {e} na tentativa {attempt+1}.")
            except requests.exceptions.Timeout:
                print(f"Timeout na requisição na tentativa {attempt+1}.")
            except requests.exceptions.RequestException as e:
                print(f"Erro inesperado na requisição: {e} na tentativa {attempt+1}.")
            
            if attempt < retries:
                sleep_time = 2 ** attempt + random.uniform(0, 1) # Exponential backoff with jitter
                print(f"Aguardando {sleep_time:.2f} segundos antes de retentar.")
                time.sleep(sleep_time)
            else:
                print(f"Todas as {retries+1} tentativas falharam para a requisição {url}. Retornando resposta vazia para demonstração.")
                # Para fins de demonstração com tokens dummy, retornamos um objeto de resposta mock
                class MockResponse:
                    def json(self): return []
                    @property
                    def status_code(self): return 200
                    @property
                    def headers(self): return {"X-RateLimit-Remaining": "5000", "X-RateLimit-Reset": str(int(time.time()) + 3600)}
                    def raise_for_status(self): pass
                return MockResponse()

    def get_rest(self, endpoint, params=None):
        url = f"{self.base_url_rest}{endpoint}"
        return self._make_request("GET", url, params=params)

    def post_graphql(self, query, variables=None):
        json_data = {"query": query}
        if variables:
            json_data["variables"] = variables
        return self._make_request("POST", self.base_url_graphql, json=json_data, is_graphql=True)

# Exemplo de uso (para testes)
if __name__ == '__main__':
    from config_loader import ConfigLoader
    try:
        loader = ConfigLoader()
        tokens = loader.get_tokens()
        client = GitHubApiClient(tokens)

        owner = loader.get_user_target()
        repo = loader.get_repo_target()

        # Exemplo de requisição REST: Listar issues
        print("\nTestando API REST: Listar issues")
        try:
            response = client.get_rest(f"/repos/{owner}/{repo}/issues", params={"state": "all", "per_page": 5})
            issues = response.json()
            for issue in issues:
                print(f"Issue #{issue["number"]}: {issue["title"]}")
        except Exception as e:
            print(f"Falha ao listar issues: {e}")

        # Exemplo de requisição GraphQL: Obter informações do repositório
        print("\nTestando API GraphQL: Obter informações do repositório")
        graphql_query = """
        query($owner: String!, $repo: String!) {
            repository(owner: $owner, name: $repo) {
                name
                description
                stargazerCount
            }
        }
        """
        graphql_variables = {"owner": owner, "repo": repo}
        try:
            response = client.post_graphql(graphql_query, graphql_variables)
            repo_info = response.json()
            print(f"Nome do Repositório: {repo_info["data"]["repository"]["name"]}")
            print(f"Descrição: {repo_info["data"]["repository"]["description"]}")
            print(f"Estrelas: {repo_info["data"]["repository"]["stargazerCount"]}")
        except Exception as e:
            print(f"Falha ao obter informações do repositório via GraphQL: {e}")

    except (FileNotFoundError, ValueError) as e:
        print(f"Erro de configuração: {e}")
    except Exception as e:
        print(f"Erro geral: {e}")

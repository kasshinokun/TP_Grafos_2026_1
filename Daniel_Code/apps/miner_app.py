import urllib.request
import urllib.error
import json
import getpass
from core.event_bus import EventBus

class MinerApp:
    def __init__(self):
        self.bus = EventBus()
        self.bus.subscribe("START_MINING", self.mine_github_data)

    def mine_github_data(self, event_type, payload):
        repo = payload.get("repo", "TheAlgorithms/Java")
        
        print("\n--- Autenticação do GitHub ---")
        print("Para evitar bloqueios da API, insira seu Personal Access Token (PAT).")
        print("A digitação ficará invisível por segurança.")
        token = getpass.getpass("Token: ")

        print(f"\n[MinerApp] Iniciando mineração das issues fechadas de: {repo}...")
        
        # Pega a primeira página de issues fechadas (100 resultados)
        url = f"https://api.github.com/repos/{repo}/issues?state=closed&per_page=100&page=1"
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Python-Native-Miner"
        }
        
        if token:
            headers["Authorization"] = f"token {token}"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
            
            issue_closings = []
            
            for item in data:
                # O GitHub retorna Pull Requests no endpoint de issues.
                # Se tiver a chave 'pull_request', ignoramos, pois queremos apenas Issues.
                if 'pull_request' not in item:
                    issue_number = item.get('number')
                    user_opened = item.get('user', {}).get('login')
                    
                    # Para saber quem fechou, olhamos para 'closed_by' (nem sempre presente dependendo da query, mas tentaremos pegar)
                    user_closed = item.get('closed_by', {}).get('login') if item.get('closed_by') else "Desconhecido"
                    
                    if user_opened and user_closed:
                        issue_closings.append({
                            "issue_number": issue_number,
                            "opened_by": user_opened,
                            "closed_by": user_closed
                        })

            print(f"[MinerApp] Encontradas {len(issue_closings)} issues fechadas nesta página.")
            
            # Envia os dados coletados para quem estiver escutando (o GraphApp)
            self.bus.publish("MINING_COMPLETE", {"interactions": issue_closings})

        except urllib.error.HTTPError as e:
            print(f"[MinerApp] Erro HTTP: {e.code} - {e.reason}")
            if e.code == 401:
                print("Dica: Verifique se o seu Token é válido.")
            elif e.code == 403:
                print("Dica: Você pode ter atingido o limite de requisições da API do GitHub.")
        except Exception as e:
            print(f"[MinerApp] Erro inesperado: {e}")
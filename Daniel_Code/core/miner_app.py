import urllib.request
import urllib.error
import json
import os
import threading
from queue import Queue
from core.event_bus import EventBus
from core.cypher_token import QRCodeJSONHandler

class MinerApp:
    def __init__(self):
        self.bus = EventBus()
        self.bus.subscribe("START_MINING", self.mine_github_data)
        
        # Variáveis compartilhadas entre as threads
        self.resultados_grafos = []
        self.resultados_brutos = []
        self.lock = threading.Lock() # Trava de segurança para evitar colisão entre threads

    def obter_credenciais(self, caminho_qr_code):
        print(f"[MinerApp] Tentando ler credenciais do QR Code: {caminho_qr_code}...")
        
        if not os.path.exists(caminho_qr_code):
            print(f"[Erro] O arquivo '{caminho_qr_code}' não foi encontrado.")
            return None

        qr_handler = QRCodeJSONHandler(json_data={}) 
        dados_recuperados = qr_handler.ler_qr_code(caminho_qr_code)
        
        if not dados_recuperados:
            return None
            
        print("[MinerApp] ✅ Credenciais recuperadas em memória com sucesso!")
        return dados_recuperados

    def worker_minerador(self, token, fila_urls, thread_id):
        """
        Função executada em paralelo por cada thread. Consome URLs da fila e baixa os dados.
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"Python-Native-Miner-Thread-{thread_id}",
            "Authorization": f"token {token}"
        }

        while not fila_urls.empty():
            try:
                # Pega a próxima página da fila de forma segura
                url = fila_urls.get_nowait()
            except:
                break
            
            pagina_atual = url.split('&page=')[1]
            print(f"[Thread-{thread_id}] 📡 Baixando página {pagina_atual}...")
            
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
                    
                    # Aciona a trava ao modificar variáveis globais no Python
                    with self.lock:
                        for item in data:
                            if 'pull_request' not in item:
                                # 1. Salva o objeto JSON bruto (Igual ao do seu colega)
                                self.resultados_brutos.append(item)
                                
                                # 2. Extrai apenas o necessário para criar o Grafo
                                issue_number = item.get('number')
                                user_opened = item.get('user', {}).get('login')
                                user_closed = item.get('closed_by', {}).get('login') if item.get('closed_by') else "N/A"
                                
                                if user_opened and user_closed and user_closed != "N/A":
                                    self.resultados_grafos.append({
                                        "issue_number": issue_number,
                                        "opened_by": user_opened,
                                        "closed_by": user_closed
                                    })
            except urllib.error.HTTPError as e:
                print(f"[Thread-{thread_id}] ⚠️ Erro HTTP {e.code} na página {pagina_atual}")
            except Exception as e:
                print(f"[Thread-{thread_id}] ⚠️ Erro inesperado: {e}")
            finally:
                # Avisa a fila que o trabalho desta URL acabou
                fila_urls.task_done()

    def mine_github_data(self, event_type, payload):
        repo = payload.get("repo", "microsoft/TypeScript")
        caminho_qr = payload.get("qr_path", "token_qr.png")
        
        dados_config = self.obter_credenciais(caminho_qr)
        if not dados_config:
            return
            
        tokens = dados_config.get("token", [])
        if not tokens:
            print("[Erro] Nenhum token encontrado no QR Code.")
            return

        num_threads = len(tokens)
        print(f"\n[MinerApp] 🚀 Iniciando mineração MULTITHREADING com {num_threads} token(s) em paralelo...")
        
        self.resultados_grafos = []
        self.resultados_brutos = []

        # 1. Cria a Fila de páginas a serem mineradas
        fila_urls = Queue()
        
        # Mude este número para baixar mais páginas. Ex: 40 páginas = 4000 issues avaliadas.
        limite_paginas = 100
        
        base_url = f"https://api.github.com/repos/{repo}/issues?state=closed&per_page=100"
        for page in range(1, limite_paginas + 1):
            fila_urls.put(f"{base_url}&page={page}")

        # 2. Cria e inicia as Threads (Uma para cada token do QR Code)
        threads = []
        for i, token in enumerate(tokens):
            t = threading.Thread(target=self.worker_minerador, args=(token, fila_urls, i+1))
            t.start()
            threads.append(t)

        # 3. Aguarda todas as threads terminarem
        for t in threads:
            t.join()

        print(f"\n[MinerApp] 📥 Download concluído!")
        print(f"   -> Issues brutas obtidas: {len(self.resultados_brutos)}")
        print(f"   -> Interações válidas extraídas: {len(self.resultados_grafos)}")

        # 4. Exportação dos Dados para JSON (Exigência do projeto)
        # Garante que a pasta 'data' existe na raiz do projeto
        os.makedirs("data", exist_ok=True) 
        
        # Cria o caminho completo: data/github_dados_minerados.json
        nome_arquivo_json = os.path.join("data", "github_dados_minerados.json")
        
        with open(nome_arquivo_json, "w", encoding="utf-8") as f:
            json.dump(self.resultados_brutos, f, indent=4, ensure_ascii=False)
        print(f"[MinerApp] 💾 Dados exportados com sucesso para: '{nome_arquivo_json}'")

        # 5. Envia apenas a versão limpa para a micro-aplicação de Grafos
        print("[MinerApp] Repassando dados para o Módulo de Grafos...")
        self.bus.publish("MINING_COMPLETE", {"interactions": self.resultados_grafos})
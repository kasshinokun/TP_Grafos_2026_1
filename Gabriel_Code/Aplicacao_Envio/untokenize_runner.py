# Adicione este código ao final do arquivo orchestrator_hibrido_alpha0b.py,
# antes do if __name__ == "__main__", ou em um arquivo separado importando as classes necessárias.

def untokenized_runner(target_user: str, target_repo: str, years_back: int = 5):
    """
    Executa o minerador sem utilizar tokens de autenticação do GitHub.
    Respeita o limite de 60 requisições por hora para clientes não autenticados.
    
    Args:
        target_user (str): Dono do repositório
        target_repo (str): Nome do repositório
        years_back (int): Quantos anos de histórico minerar (padrão 5)
    """
    import threading
    import queue
    import time
    import asyncio
    import aiohttp
    import logging
    from datetime import datetime, timedelta
    from typing import Optional, Dict, Any
    
    # Configuração de logging (já existe no escopo global, mas reforçamos)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
    
    # ========== Rate Limiter para requisições não autenticadas ==========
    class UnauthenticatedRateLimiter:
        """
        Gerencia o limite de 60 req/hora para chamadas sem token.
        Utiliza um lock e controle de tempo para bloquear todas as threads quando o limite é atingido.
        """
        def __init__(self):
            self.lock = threading.Lock()
            self.request_timestamps = []  # lista de timestamps das últimas requisições
            self.limit = 60
            self.window = 3600  # 1 hora em segundos
            self.global_cooldown_until = 0  # timestamp até quando todas as threads devem esperar
        
        def acquire(self):
            """
            Bloqueia até que seja permitido fazer uma nova requisição.
            Retorna o tempo de espera (útil para logging).
            """
            with self.lock:
                now = time.time()
                # Se estamos em cooldown global (após 403), espera até o reset
                if now < self.global_cooldown_until:
                    wait_time = self.global_cooldown_until - now
                    logging.warning(f"⏳ Rate limit global: aguardando {wait_time:.0f}s até reset...")
                    time.sleep(wait_time)
                    now = time.time()
                    # Limpa timestamps antigos após a espera
                    self.request_timestamps = [ts for ts in self.request_timestamps if ts > now - self.window]
                
                # Remove timestamps fora da janela
                self.request_timestamps = [ts for ts in self.request_timestamps if ts > now - self.window]
                
                # Se ainda atingiu o limite, espera até o mais antigo sair da janela
                if len(self.request_timestamps) >= self.limit:
                    oldest = min(self.request_timestamps)
                    wait_time = (oldest + self.window) - now
                    logging.warning(f"⏳ Limite de 60 req/h atingido. Aguardando {wait_time:.0f}s...")
                    time.sleep(wait_time)
                    now = time.time()
                    # Recalcula timestamps
                    self.request_timestamps = [ts for ts in self.request_timestamps if ts > now - self.window]
                
                # Registra esta requisição
                self.request_timestamps.append(now)
        
        def set_global_cooldown(self, reset_timestamp: int):
            """Chamado quando o GitHub responde com 403/429 e fornece X-RateLimit-Reset."""
            with self.lock:
                self.global_cooldown_until = reset_timestamp + 60  # margem de 1 minuto
                logging.warning(f"🚫 Cooldown global ativado até {datetime.fromtimestamp(self.global_cooldown_until).strftime('%H:%M:%S')}")
    
    # ========== EventBus modificado para manter filas separadas (igual ao tokenizado) ==========
    class UntokenizedEventBus:
        def __init__(self):
            self.task_queue = queue.Queue(maxsize=50000)
            self.data_queue = queue.Queue(maxsize=50000)
            self.notification_queue = queue.Queue(maxsize=50000)
        
        def publish_task(self, task: Dict[str, Any]):
            self.task_queue.put(task)
        
        def consume_task(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
            try:
                return self.task_queue.get(timeout=timeout)
            except queue.Empty:
                return None
        
        def publish_data(self, event: Dict[str, Any]):
            self.data_queue.put(event)
        
        def consume_data(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
            try:
                return self.data_queue.get(timeout=timeout)
            except queue.Empty:
                return None
        
        def publish_notification(self, event: Dict[str, Any]):
            self.notification_queue.put(event)
        
        def consume_notification(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
            try:
                return self.notification_queue.get(timeout=timeout)
            except queue.Empty:
                return None
        
        def task_done(self):
            self.task_queue.task_done()
    
    # ========== AsyncRequester sem autenticação ==========
    class UntokenizedAsyncRequester:
        def __init__(self, max_concurrent: int = 5):
            self.semaphore = asyncio.Semaphore(max_concurrent)
            self.session = None
            self.rate_limiter = UnauthenticatedRateLimiter()
        
        async def __aenter__(self):
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=20, ttl_dns_cache=300)
            self.session = aiohttp.ClientSession(connector=connector)
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if self.session:
                await self.session.close()
        
        async def fetch(self, url: str, params: Dict) -> tuple:
            # Aplica o rate limiter (bloqueia se necessário)
            # Como o rate_limiter usa time.sleep (bloqueante), precisamos rodar em thread separada
            # para não travar o event loop. Vamos usar loop.run_in_executor.
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.rate_limiter.acquire)
            
            headers = {"Accept": "application/vnd.github.v3+json"}
            try:
                async with self.session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    data = await response.json() if response.status == 200 else None
                    return response, data
            except Exception as e:
                logging.error(f"Erro de rede no UntokenizedAsyncRequester: {e}")
                return None, None
    
    # ========== Hybrid Worker sem token (usa o requester acima) ==========
    async def untokenized_hybrid_worker_async(worker_id: int, task_type: str, event_bus: UntokenizedEventBus,
                                              requester: UntokenizedAsyncRequester, shutdown_event: threading.Event):
        requests_processed = 0
        while not shutdown_event.is_set():
            task = event_bus.consume_task(timeout=1.0)
            if task is None:
                continue
            
            try:
                if task.get("type") != task_type:
                    event_bus.publish_task(task)
                    await asyncio.sleep(0.05)
                    continue
                
                owner = task["owner"]
                repo = task["repo"]
                p_type = task["type"]
                page = task.get("page", 1)
                since = task.get("since", "")
                
                base_url = "https://api.github.com"
                data_prs = None
                
                if p_type == "issue_comments":
                    url = f"{base_url}/repos/{owner}/{repo}/issues/comments"
                    params = {"since": since, "page": page, "per_page": 100}
                    resp, data = await requester.fetch(url, params)
                
                elif p_type == "pr_comments":
                    url = f"{base_url}/repos/{owner}/{repo}/pulls/comments"
                    params = {"since": since, "page": page, "per_page": 100}
                    resp, data = await requester.fetch(url, params)
                
                elif p_type == "closed_issues":
                    url = f"{base_url}/repos/{owner}/{repo}/issues"
                    params = {"state": "closed", "since": since, "page": page, "per_page": 100}
                    resp, data = await requester.fetch(url, params)
                
                elif p_type == "pr_reviews":
                    url_prs = f"{base_url}/repos/{owner}/{repo}/pulls"
                    resp_prs, data_prs = await requester.fetch(
                        url_prs, {"state": "closed", "page": page, "per_page": 30}
                    )
                    if resp_prs and resp_prs.status in [403, 429]:
                        raise Exception(f"Rate Limit nos PRs: {resp_prs.status}")
                    
                    reviews_data = []
                    if data_prs:
                        for pr in data_prs:
                            if pr.get("merged_at"):
                                pr_author = pr.get("user", {}).get("login")
                                pr_url = f"{base_url}/repos/{owner}/{repo}/pulls/{pr['number']}"
                                url_rev = f"{base_url}/repos/{owner}/{repo}/pulls/{pr['number']}/reviews"
                                _, data_rev = await requester.fetch(url_rev, {"per_page": 100})
                                if data_rev:
                                    for review in data_rev:
                                        review["_pr_author"] = pr_author
                                        review["_pr_url"] = pr_url
                                    reviews_data.extend(data_rev)
                    resp, data = resp_prs, reviews_data
                else:
                    logging.warning(f"Worker-{worker_id}: tipo desconhecido '{p_type}'")
                    continue
                
                requests_processed += 1
                if requests_processed % 500 == 0:
                    logging.info(f"Worker-{worker_id} processou {requests_processed} requests (sem token).")
                
                if resp and resp.status in [403, 429]:
                    reset_time = int(resp.headers.get("X-RateLimit-Reset", time.time()))
                    requester.rate_limiter.set_global_cooldown(reset_time)
                    event_bus.publish_notification({"type": "TOKEN_COOLDOWN", "token": "unauthenticated"})
                    # Recoloca a tarefa na fila para tentar depois
                    event_bus.publish_task(task)
                
                elif resp and resp.status == 200 and data:
                    event_bus.publish_data({
                        "type": "DATA_EXTRACTED",
                        "data_type": p_type,
                        "payload": data
                    })
                    # Paginação
                    if p_type == "pr_reviews":
                        has_more = data_prs is not None and len(data_prs) >= 30
                    else:
                        has_more = len(data) >= 90
                    if has_more:
                        next_task = task.copy()
                        next_task["page"] = page + 1
                        event_bus.publish_task(next_task)
            
            except Exception as e:
                logging.error(f"Erro no Worker-{worker_id} ({task_type} pág.{task.get('page',1)}): {e}")
            finally:
                event_bus.task_done()
    
    def untokenized_hybrid_worker_thread(worker_id: int, task_type: str, event_bus: UntokenizedEventBus,
                                          requester: UntokenizedAsyncRequester, shutdown_event: threading.Event):
        logging.info(f"Worker-{worker_id} (sem token, tipo {task_type}) iniciado.")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(untokenized_hybrid_worker_async(worker_id, task_type, event_bus, requester, shutdown_event))
        finally:
            loop.close()
    
    # ========== Storage Worker (idêntico ao original, consome data_queue) ==========
    class UntokenizedStorageWorker(threading.Thread):
        def __init__(self, event_bus: UntokenizedEventBus, shutdown_event: threading.Event):
            super().__init__(name="Storage-Worker-NoToken", daemon=True)
            self.event_bus = event_bus
            self.shutdown_event = shutdown_event
            self.file_lock = threading.Lock()
            self.max_size_bytes = 200 * 1024 * 1024
            self.data_json_dir = get_diretory("json")  # reusa função auxiliar existente
            
            self.base_files = {
                "issue_comments": "issue_comments",
                "pr_comments": "pr_comments",
                "closed_issues": "closed_issues",
                "pr_reviews": "pr_reviews_merges"
            }
            self.current_parts = {key: 1 for key in self.base_files}
            self.memory_buffer = {key: [] for key in self.base_files}
            self.buffer_limit = 2000
        
        def _get_current_filename(self, data_type: str) -> str:
            base = self.base_files[data_type]
            part = self.current_parts[data_type]
            return concat_path(self.data_json_dir, f"{base}_part_{part:02d}.json")
        
        def _check_and_rotate_file(self, filename: str, data_type: str):
            if manager.exists(filename):
                if manager.getsize(filename) >= (self.max_size_bytes - 5 * 1024 * 1024):
                    self.current_parts[data_type] += 1
                    logging.info(f"🔄 Arquivo {filename} atingiu limite. Rotacionando para parte {self.current_parts[data_type]}")
        
        def _flush_buffer(self, data_type: str):
            if not self.memory_buffer[data_type]:
                return
            filename = self._get_current_filename(data_type)
            with self.file_lock:
                self._check_and_rotate_file(filename, data_type)
                filename = self._get_current_filename(data_type)
                try:
                    try:
                        with open(filename, "r", encoding="utf-8") as f:
                            existing_data = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        existing_data = []
                    existing_data.extend(self.memory_buffer[data_type])
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(existing_data, f, indent=2, ensure_ascii=False)
                    size_mb = manager.getsize(filename) / (1024*1024)
                    logging.info(f"💾 [Storage] Salvo {len(self.memory_buffer[data_type])} registros em {filename} ({size_mb:.2f} MB)")
                    self.memory_buffer[data_type] = []
                except Exception as e:
                    logging.error(f"Erro ao salvar {filename}: {e}")
        
        def run(self):
            logging.info("Storage-Worker (sem token) iniciado.")
            while not self.shutdown_event.is_set() or not self.event_bus.data_queue.empty():
                event = self.event_bus.consume_data(timeout=1.0)
                if not event:
                    for dtype in self.base_files:
                        if len(self.memory_buffer[dtype]) >= self.buffer_limit:
                            self._flush_buffer(dtype)
                    continue
                if event["type"] == "DATA_EXTRACTED":
                    data_type = event["data_type"]
                    payload = event["payload"]
                    self.memory_buffer[data_type].extend(payload)
                    if len(self.memory_buffer[data_type]) >= self.buffer_limit:
                        self._flush_buffer(data_type)
            for dtype in self.base_files:
                if self.memory_buffer[dtype]:
                    self._flush_buffer(dtype)
            logging.info("Storage-Worker (sem token) encerrado.")
    
    # ========== Função principal untokenized_runner ==========
    logging.info("🚀 Iniciando minerador SEM TOKEN (limite: 60 requisições/hora).")
    shutdown_event = threading.Event()
    event_bus = UntokenizedEventBus()
    
    # Cria o requester compartilhado (será usado por todas as threads)
    requester = UntokenizedAsyncRequester(max_concurrent=MAX_ASYNC_CONCURRENCY_PER_THREAD)
    # Inicializa o loop asyncio para o requester (ele precisa de um loop para usar run_in_executor)
    # Na verdade, o requester será usado dentro de cada thread, cada uma com seu próprio loop.
    # O rate_limiter dentro do requester é thread-safe, então podemos instanciar um requester por thread? Não, porque o rate_limiter deve ser global.
    # Melhor criar um único rate_limiter global e passar para cada thread. Vamos ajustar: o rate_limiter será uma instância separada e cada requester o usará.
    global_rate_limiter = UnauthenticatedRateLimiter()
    
    # Precisamos modificar o UntokenizedAsyncRequester para aceitar um rate_limiter externo.
    # Vamos redefinir a classe dentro da função para usar o global_rate_limiter.
    class FixedUntokenizedAsyncRequester:
        def __init__(self, rate_limiter, max_concurrent=5):
            self.semaphore = asyncio.Semaphore(max_concurrent)
            self.session = None
            self.rate_limiter = rate_limiter
        
        async def __aenter__(self):
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=20, ttl_dns_cache=300)
            self.session = aiohttp.ClientSession(connector=connector)
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if self.session:
                await self.session.close()
        
        async def fetch(self, url: str, params: Dict) -> tuple:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.rate_limiter.acquire)
            headers = {"Accept": "application/vnd.github.v3+json"}
            try:
                async with self.session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    data = await response.json() if response.status == 200 else None
                    return response, data
            except Exception as e:
                logging.error(f"Erro de rede: {e}")
                return None, None
    
    # Agora redefinimos a função worker_async para usar essa nova classe
    async def worker_async_fixed(worker_id, task_type, event_bus, rate_limiter, shutdown_event):
        async with FixedUntokenizedAsyncRequester(rate_limiter, max_concurrent=MAX_ASYNC_CONCURRENCY_PER_THREAD) as requester:
            requests_processed = 0
            while not shutdown_event.is_set():
                task = event_bus.consume_task(timeout=1.0)
                if task is None:
                    continue
                try:
                    if task.get("type") != task_type:
                        event_bus.publish_task(task)
                        await asyncio.sleep(0.05)
                        continue
                    # ... (mesma lógica de antes, usando requester.fetch)
                    owner = task["owner"]
                    repo = task["repo"]
                    p_type = task["type"]
                    page = task.get("page", 1)
                    since = task.get("since", "")
                    base_url = "https://api.github.com"
                    data_prs = None
                    
                    if p_type == "issue_comments":
                        url = f"{base_url}/repos/{owner}/{repo}/issues/comments"
                        params = {"since": since, "page": page, "per_page": 100}
                        resp, data = await requester.fetch(url, params)
                    elif p_type == "pr_comments":
                        url = f"{base_url}/repos/{owner}/{repo}/pulls/comments"
                        params = {"since": since, "page": page, "per_page": 100}
                        resp, data = await requester.fetch(url, params)
                    elif p_type == "closed_issues":
                        url = f"{base_url}/repos/{owner}/{repo}/issues"
                        params = {"state": "closed", "since": since, "page": page, "per_page": 100}
                        resp, data = await requester.fetch(url, params)
                    elif p_type == "pr_reviews":
                        url_prs = f"{base_url}/repos/{owner}/{repo}/pulls"
                        resp_prs, data_prs = await requester.fetch(url_prs, {"state": "closed", "page": page, "per_page": 30})
                        if resp_prs and resp_prs.status in [403, 429]:
                            raise Exception(f"Rate Limit: {resp_prs.status}")
                        reviews_data = []
                        if data_prs:
                            for pr in data_prs:
                                if pr.get("merged_at"):
                                    pr_author = pr.get("user", {}).get("login")
                                    pr_url = f"{base_url}/repos/{owner}/{repo}/pulls/{pr['number']}"
                                    _, data_rev = await requester.fetch(f"{base_url}/repos/{owner}/{repo}/pulls/{pr['number']}/reviews", {"per_page": 100})
                                    if data_rev:
                                        for rev in data_rev:
                                            rev["_pr_author"] = pr_author
                                            rev["_pr_url"] = pr_url
                                        reviews_data.extend(data_rev)
                        resp, data = resp_prs, reviews_data
                    else:
                        continue
                    
                    requests_processed += 1
                    if requests_processed % 500 == 0:
                        logging.info(f"Worker-{worker_id} processou {requests_processed} (sem token).")
                    
                    if resp and resp.status in [403, 429]:
                        reset = int(resp.headers.get("X-RateLimit-Reset", time.time()))
                        rate_limiter.set_global_cooldown(reset)
                        event_bus.publish_notification({"type": "TOKEN_COOLDOWN", "token": "unauthenticated"})
                        event_bus.publish_task(task)  # recoloca
                    elif resp and resp.status == 200 and data:
                        event_bus.publish_data({"type": "DATA_EXTRACTED", "data_type": p_type, "payload": data})
                        if p_type == "pr_reviews":
                            has_more = data_prs and len(data_prs) >= 30
                        else:
                            has_more = len(data) >= 90
                        if has_more:
                            next_task = task.copy()
                            next_task["page"] = page + 1
                            event_bus.publish_task(next_task)
                except Exception as e:
                    logging.error(f"Erro no worker {worker_id}: {e}")
                finally:
                    event_bus.task_done()
    
    def worker_thread_wrapper(worker_id, task_type, event_bus, rate_limiter, shutdown_event):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(worker_async_fixed(worker_id, task_type, event_bus, rate_limiter, shutdown_event))
        finally:
            loop.close()
    
    # Cria e inicia storage worker
    storage = UntokenizedStorageWorker(event_bus, shutdown_event)
    storage.start()
    
    # Cria workers híbridos (um por tipo e multiplicador)
    task_types = ["issue_comments", "pr_comments", "closed_issues", "pr_reviews"]
    threads = []
    for task_type in task_types:
        for i in range(THREADS_PER_TYPE):
            t = threading.Thread(target=worker_thread_wrapper,
                                 args=(i, task_type, event_bus, global_rate_limiter, shutdown_event),
                                 name=f"NoToken-{task_type}-{i}")
            t.start()
            threads.append(t)
    
    # Semeia tarefas iniciais
    since_date = (datetime.now() - timedelta(days=years_back * 365)).strftime("%Y-%m-%dT00:00:00Z")
    for task_type in task_types:
        event_bus.publish_task({
            "owner": target_user,
            "repo": target_repo,
            "type": task_type,
            "page": 1,
            "since": since_date
        })
    
    # Aguarda término das tarefas
    mining_completed = threading.Event()
    def wait_tasks():
        event_bus.task_queue.join()
        mining_completed.set()
    threading.Thread(target=wait_tasks, daemon=True).start()
    
    # Loop principal com monitor de cooldown
    try:
        while not shutdown_event.is_set():
            if mining_completed.is_set():
                logging.info("✅ Mineração sem token concluída.")
                break
            # Consome notificações (cooldown global)
            note = event_bus.consume_notification(timeout=0.5)
            if note and note["type"] == "TOKEN_COOLDOWN":
                logging.info("📢 Cooldown global ativo (limite de 60 req/h excedido). Aguardando reset...")
            time.sleep(0.1)
    except KeyboardInterrupt:
        logging.info("Interrupção manual. Finalizando...")
    finally:
        shutdown_event.set()
        for t in threads:
            t.join(timeout=3)
        storage.join(timeout=5)
        logging.info("Minerador sem token finalizado.")

# Exemplo de uso no main (adicione uma opção de escolha):
"""
if __name__ == "__main__":
    # ... carregar configurações ...
    use_tokens = input("Usar tokens? (s/N): ").lower() == 's'
    if use_tokens:
        main()   # função original com tokens
    else:
        untokenized_runner(target_user, target_repo, years_back)
"""
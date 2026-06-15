# Release Alpha 0e — 2026-06-14
# Baseado em orchestrator_hibrido_alpha0d.py + integração revisada de untokenize_runner.py
#
# === CORREÇÕES v0e ===
# [BUG CRÍTICO] Removida chamada dupla de requester.fetch() que dobrava consumo de rate-limit
#               em todos os tipos exceto pr_reviews (linha "if p_type != 'pr_reviews': resp, data = ...")
# [BUG]        Adicionada injeção de _pr_author e _pr_url no worker TOKENIZADO de pr_reviews
#               (a omissão fazia Lapidador descartar 100% das reviews do modo COM token)
# [REFACTOR]   untokenized_runner agora usa ShutdownManager nativo em vez de objeto anônimo
# [UX]         Notificações de cooldown no modo sem token exibem tempo restante em minutos
# [UX]         Evento MINING_COMPLETE publicado na notification_queue ao fim da mineração

import threading
import queue
import time
import asyncio
import aiohttp
import requests
import json
import qrcode
from PIL import Image
from pyzbar.pyzbar import decode
import logging
import os
import os.path as manager
from os.path import join as concat_path
from os.path import abspath as absoluto
from main_rebuild import main as init_lapidador
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# ==============================================================================
# CONFIGURAÇÃO DE LOGGING E CONSTANTES
# ==============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')

THREADS_PER_TYPE = 2          # 2 threads x 4 tipos = 8 threads totais no pool
MAX_ASYNC_CONCURRENCY_PER_THREAD = 5   # 1–5 coroutines paralelas por thread
BATCH_LOG_INTERVAL = 500      # Loga a cada 500 requisições processadas pelo worker

# ==============================================================================
# 0A. FUNÇÕES AUXILIARES
# ==============================================================================
def get_absoluto(file: str) -> str:
    return manager.dirname(absoluto(file))

def get_diretory(name_diretory: str, condition: int = 2) -> str:
    APP_DIR = get_absoluto(__file__)
    if condition == 1:
        return concat_path(APP_DIR, name_diretory)
    DATA_DIR = concat_path(APP_DIR, name_diretory)
    os.makedirs(DATA_DIR, exist_ok=True)
    return DATA_DIR

# ==============================================================================
# 0B. GERADOR / LEITOR DE QR CODE COM TOKENS DO GITHUB
# ==============================================================================
class QRCodeJSONHandler:
    def __init__(self, json_file_path=None, json_data=None):
        if json_file_path:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        elif json_data is not None:
            self.data = json_data
        else:
            raise ValueError("É necessário fornecer 'json_file_path' ou 'json_data'.")

    def gerar_qr_code(self, caminho_saida="qrcode_saida.png") -> str:
        json_string = json.dumps(self.data, ensure_ascii=False, separators=(',', ':'))
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(json_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(caminho_saida)
        logging.info(f"✅ QR Code gerado e salvo em: {caminho_saida}")
        return caminho_saida

    @staticmethod
    def ler_qr_code(caminho_imagem) -> Optional[dict]:
        try:
            img = Image.open(caminho_imagem)
            dados_decodificados = decode(img)
            if not dados_decodificados:
                raise ValueError("Nenhum QR Code foi encontrado na imagem fornecida.")
            string_json = dados_decodificados[0].data.decode('utf-8')
            json_recuperado = json.loads(string_json)
            logging.info("✅ JSON recuperado com sucesso!")
            return json_recuperado
        except Exception as e:
            logging.error(f"❌ Erro ao ler o QR Code: {e}")
            return None

    @staticmethod
    def write_json(data_dict, path_file: str):
        with open(path_file, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=4, ensure_ascii=False)

    @staticmethod
    def excluir_arquivo(caminho_arquivo):
        try:
            if manager.isfile(caminho_arquivo):
                os.remove(caminho_arquivo)
                logging.info(f"Arquivo '{caminho_arquivo}' excluído.")
        except Exception as e:
            logging.error(f"Erro ao excluir '{caminho_arquivo}': {e}")

# ==============================================================================
# 1. GERENCIADOR DE DESLIGAMENTO (Graceful Shutdown)
# ==============================================================================
class ShutdownManager:
    def __init__(self):
        self._event = threading.Event()

    def request_shutdown(self):
        logging.info("Sinal de desligamento recebido. Finalizando tarefas ordenadamente...")
        self._event.set()

    def is_shutdown_requested(self) -> bool:
        return self._event.is_set()

# ==============================================================================
# 2. CERTIFICADOR DE TOKENS (Síncrono, roda apenas na inicialização)
# ==============================================================================
class TokenCertifier:
    @staticmethod
    def validate_tokens(tokens: List[str]) -> List[str]:
        valid_tokens = []
        logging.info("Certificando tokens com a API do GitHub...")
        session = requests.Session()
        session.headers.update({"Accept": "application/vnd.github.v3+json"})
        for token in tokens:
            headers = {"Authorization": f"token {token}"}
            try:
                response = session.get(
                    "https://api.github.com/rate_limit",
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    scopes_header = response.headers.get("X-OAuth-Scopes", "")
                    scopes = [s.strip() for s in scopes_header.split(",")]
                    if "repo" in scopes or "public_repo" in scopes:
                        valid_tokens.append(token)
                        logging.info(f"✅ Token ...{token[-4:]} válido. Escopos: {scopes_header}")
                    else:
                        logging.warning(f"⚠️ Token ...{token[-4:]} rejeitado: escopos insuficientes ({scopes_header}).")
                else:
                    logging.warning(f"❌ Token ...{token[-4:]} inválido ou expirado (HTTP {response.status_code}).")
            except requests.exceptions.RequestException as e:
                logging.error(f"❌ Erro de rede ao certificar token ...{token[-4:]}: {e}")

        logging.info(f"Certificação concluída. {len(valid_tokens)}/{len(tokens)} tokens aptos.")
        return valid_tokens

# ==============================================================================
# 3. GERENCIADOR DE TOKENS (Thread-Safe)
# ==============================================================================
class TokenManager:
    def __init__(self, tokens: List[str]):
        self.tokens = {
            token: {"available": True, "cooldown_until": 0}
            for token in tokens
        }
        self.lock = threading.Lock()

    def get_available_token(self) -> Optional[str]:
        with self.lock:
            now = time.time()
            for token, status in self.tokens.items():
                if status["available"] and now >= status["cooldown_until"]:
                    status["available"] = False
                    return token
            return None

    def release_token(self, token: str):
        """Marca token como disponível (não cancela cooldown ativo — apenas libera o bloqueio de uso)."""
        with self.lock:
            if token in self.tokens:
                self.tokens[token]["available"] = True

    def set_cooldown(self, token: str, github_reset_timestamp: int):
        """Coloca o token em cooldown até o timestamp do GitHub + 1 min de margem."""
        with self.lock:
            cooldown_time = int(github_reset_timestamp) + 60
            if token in self.tokens:
                self.tokens[token]["available"] = False
                self.tokens[token]["cooldown_until"] = cooldown_time
        logging.warning(
            f"⏳ Token ...{token[-4:]} em cooldown até "
            f"{datetime.fromtimestamp(cooldown_time).strftime('%H:%M:%S')}"
        )

    def all_in_cooldown(self) -> bool:
        """Retorna True se nenhum token está disponível agora."""
        with self.lock:
            now = time.time()
            return all(
                not status["available"] or now < status["cooldown_until"]
                for status in self.tokens.values()
            )

    def get_next_reset_time(self) -> float:
        """Retorna o timestamp unix do próximo token a sair do cooldown."""
        with self.lock:
            resets = [
                status["cooldown_until"]
                for status in self.tokens.values()
                if status["cooldown_until"] > 0
            ]
            return min(resets) if resets else 0.0

# ==============================================================================
# 4. BARRAMENTO DE EVENTOS (EDA Thread-Safe) — três filas dedicadas
# ==============================================================================
class EventBus:
    """
    Três filas completamente separadas:
      task_queue         → tarefas de mineração (workers consomem)
      data_queue         → dados extraídos (StorageWorker consome)
      notification_queue → eventos de sistema / cooldown (Orchestrator consome)
    """
    def __init__(self):
        self.task_queue         = queue.Queue(maxsize=50000)
        self.data_queue         = queue.Queue(maxsize=50000)
        self.notification_queue = queue.Queue(maxsize=1000)

    # --- task ---
    def publish_task(self, task: Dict[str, Any]):
        self.task_queue.put(task)

    def consume_task(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        try:
            return self.task_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def task_done(self):
        self.task_queue.task_done()

    # --- data ---
    def publish_data(self, data: Dict[str, Any]):
        self.data_queue.put(data)

    def consume_data(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        try:
            return self.data_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    # --- notification ---
    def publish_notification(self, notification: Dict[str, Any]):
        self.notification_queue.put(notification)

    def consume_notification(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        try:
            return self.notification_queue.get(timeout=timeout)
        except queue.Empty:
            return None

# ==============================================================================
# 5. MOTOR DE REQUISIÇÃO ASSÍNCRONO (COM TOKEN)
# ==============================================================================
class AsyncRequester:
    def __init__(self, max_concurrent: int = 5):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, *_):
        if self.session:
            await self.session.close()

    async def fetch(self, url: str, token: str, params: Dict) -> tuple:
        async with self.semaphore:
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            try:
                async with self.session.get(
                    url, headers=headers, params=params,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    data = await response.json() if response.status == 200 else None
                    return response, data
            except Exception as e:
                logging.error(f"Erro de rede no AsyncRequester: {e}")
                return None, None

# ==============================================================================
# 5B. RATE LIMITER PARA MODO SEM TOKEN (60 req/hora)
# ==============================================================================
class UnauthenticatedRateLimiter:
    def __init__(self):
        self.lock = threading.Lock()
        self.request_timestamps: List[float] = []
        self.limit = 60
        self.window = 3600          # 1 hora em segundos
        self.global_cooldown_until = 0.0

    def acquire(self):
        """Bloqueia a thread até que uma requisição possa ser enviada com segurança."""
        with self.lock:
            now = time.time()
            # Aguarda cooldown global se ativo
            if now < self.global_cooldown_until:
                wait_time = self.global_cooldown_until - now
                logging.warning(f"⏳ Rate limit global: aguardando {wait_time:.0f}s até reset...")
                time.sleep(wait_time)
                now = time.time()

            # Remove timestamps fora da janela
            self.request_timestamps = [ts for ts in self.request_timestamps if ts > now - self.window]

            # Aguarda se atingiu o limite
            if len(self.request_timestamps) >= self.limit:
                oldest = min(self.request_timestamps)
                wait_time = (oldest + self.window) - now
                logging.warning(f"⏳ Limite de {self.limit} req/h atingido. Aguardando {wait_time:.0f}s...")
                time.sleep(wait_time)
                now = time.time()
                self.request_timestamps = [ts for ts in self.request_timestamps if ts > now - self.window]

            self.request_timestamps.append(now)

    def set_global_cooldown(self, reset_timestamp: int):
        with self.lock:
            self.global_cooldown_until = reset_timestamp + 60
            logging.warning(
                f"🚫 Cooldown global ativado até "
                f"{datetime.fromtimestamp(self.global_cooldown_until).strftime('%H:%M:%S')}"
            )

# ==============================================================================
# 5C. MOTOR DE REQUISIÇÃO ASSÍNCRONO (SEM TOKEN)
# ==============================================================================
class UntokenizedAsyncRequester:
    def __init__(self, rate_limiter: UnauthenticatedRateLimiter, max_concurrent: int = 5):
        self.semaphore    = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = rate_limiter

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=20, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, *_):
        if self.session:
            await self.session.close()

    async def fetch(self, url: str, params: Dict) -> tuple:
        # Executa rate-limit check em executor para não bloquear o event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.rate_limiter.acquire)
        headers = {"Accept": "application/vnd.github.v3+json"}
        try:
            async with self.session.get(
                url, headers=headers, params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                data = await response.json() if response.status == 200 else None
                return response, data
        except Exception as e:
            logging.error(f"Erro de rede no UntokenizedAsyncRequester: {e}")
            return None, None

# ==============================================================================
# 6. HYBRID WORKER (COM TOKEN)
#    CORREÇÃO: removida chamada dupla a requester.fetch() que dobrava o consumo
#              de rate-limit em todos os tipos exceto pr_reviews.
#    CORREÇÃO: _pr_author e _pr_url agora são injetados em cada review, assim
#              como já ocorre no modo sem token, para que o Lapidador os consuma.
# ==============================================================================
def hybrid_miner_worker(
    worker_id: int,
    task_type: str,
    event_bus: EventBus,
    token_manager: TokenManager,
    shutdown_mgr: ShutdownManager
):
    logging.info(
        f"Worker-{worker_id} ({task_type}) iniciado. "
        f"Motor: Híbrido (Thread + Asyncio Semáforo {MAX_ASYNC_CONCURRENCY_PER_THREAD})"
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    requests_processed = 0

    async def run_async_engine():
        nonlocal requests_processed
        async with AsyncRequester(max_concurrent=MAX_ASYNC_CONCURRENCY_PER_THREAD) as requester:
            while not shutdown_mgr.is_shutdown_requested():
                try:
                    task = event_bus.consume_task(timeout=1.0)
                    if not task:
                        continue

                    if task.get("type") != task_type:
                        event_bus.publish_task(task)
                        await asyncio.sleep(0.05)
                        continue

                    # Obtém token
                    token = task.get("token")
                    if token is None:
                        token = token_manager.get_available_token()
                        if not token:
                            event_bus.publish_task(task)
                            await asyncio.sleep(0.5)
                            continue
                        task["token"] = token

                    owner  = task["owner"]
                    repo   = task["repo"]
                    p_type = task["type"]
                    page   = task.get("page", 1)
                    since  = task.get("since", "")
                    base_url = "https://api.github.com"

                    try:
                        resp      = None
                        data      = None
                        data_prs  = None

                        if p_type == "issue_comments":
                            url    = f"{base_url}/repos/{owner}/{repo}/issues/comments"
                            params = {"since": since, "page": page, "per_page": 100}
                            resp, data = await requester.fetch(url, token, params)

                        elif p_type == "pr_comments":
                            url    = f"{base_url}/repos/{owner}/{repo}/pulls/comments"
                            params = {"since": since, "page": page, "per_page": 100}
                            resp, data = await requester.fetch(url, token, params)

                        elif p_type == "closed_issues":
                            url    = f"{base_url}/repos/{owner}/{repo}/issues"
                            params = {"state": "closed", "since": since, "page": page, "per_page": 100}
                            resp, data = await requester.fetch(url, token, params)

                        elif p_type == "pr_reviews":
                            # 1. Busca lista de PRs fechados
                            url_prs   = f"{base_url}/repos/{owner}/{repo}/pulls"
                            resp_prs, data_prs = await requester.fetch(
                                url_prs, token,
                                {"state": "closed", "page": page, "per_page": 30}
                            )
                            if resp_prs and resp_prs.status in [403, 429]:
                                raise Exception(f"Rate Limit nos PRs: {resp_prs.status}")

                            # 2. Para cada PR mergeado, busca reviews e injeta metadados
                            reviews_data: List[dict] = []
                            if data_prs:
                                for pr in data_prs:
                                    if pr.get("merged_at"):
                                        pr_author = pr.get("user", {}).get("login")
                                        pr_url    = (
                                            f"{base_url}/repos/{owner}/{repo}"
                                            f"/pulls/{pr['number']}"
                                        )
                                        url_rev = f"{pr_url}/reviews"
                                        _, data_rev = await requester.fetch(
                                            url_rev, token, {"per_page": 100}
                                        )
                                        if data_rev:
                                            for review in data_rev:
                                                review["_pr_author"] = pr_author
                                                review["_pr_url"]    = pr_url
                                            reviews_data.extend(data_rev)
                            resp, data = resp_prs, reviews_data

                        else:
                            logging.warning(f"Worker-{worker_id}: tipo desconhecido '{p_type}'")
                            event_bus.task_done()
                            continue

                        # NOTA: fetch chamado UMA ÚNICA VEZ acima por tipo.
                        # A versão anterior chamava uma segunda vez aqui para
                        # tipos != pr_reviews, dobrando o consumo de rate-limit.

                        requests_processed += 1
                        if requests_processed % BATCH_LOG_INTERVAL == 0:
                            logging.info(f"Worker-{worker_id} processou {requests_processed} requests.")

                        # Trata rate-limit
                        if resp and resp.status in [403, 429]:
                            reset_time = int(resp.headers.get("X-RateLimit-Reset", time.time()))
                            token_manager.set_cooldown(token, reset_time)
                            event_bus.publish_notification({
                                "type": "TOKEN_COOLDOWN",
                                "token": token,
                                "reset_time": reset_time
                            })
                            task.pop("token", None)
                            event_bus.publish_task(task)
                            continue

                        # Publica dados e agenda próxima página
                        if resp and resp.status == 200 and data:
                            event_bus.publish_data({
                                "type": "DATA_EXTRACTED",
                                "data_type": p_type,
                                "payload": data
                            })
                            has_more = (
                                (data_prs is not None and len(data_prs) >= 30)
                                if p_type == "pr_reviews"
                                else len(data) >= 90
                            )
                            if has_more:
                                next_task = {**task, "page": page + 1}
                                next_task.pop("token", None)
                                event_bus.publish_task(next_task)

                    except Exception as e:
                        logging.error(f"Erro no Worker-{worker_id} (Página {page}): {e}")
                    finally:
                        if token:
                            token_manager.release_token(token)
                        event_bus.task_done()

                except Exception as e:
                    logging.error(f"Erro crítico no loop do Worker-{worker_id}: {e}")

    try:
        loop.run_until_complete(run_async_engine())
    finally:
        loop.close()
        logging.info(f"Worker-{worker_id} ({task_type}) encerrado. Total: {requests_processed}")

# ==============================================================================
# 6B. HYBRID WORKER (SEM TOKEN)
# ==============================================================================
async def untokenized_hybrid_worker_async(
    worker_id: int,
    task_type: str,
    event_bus: EventBus,
    rate_limiter: UnauthenticatedRateLimiter,
    shutdown_event: threading.Event
):
    requests_processed = 0
    async with UntokenizedAsyncRequester(
        rate_limiter, max_concurrent=MAX_ASYNC_CONCURRENCY_PER_THREAD
    ) as requester:
        while not shutdown_event.is_set():
            task = event_bus.consume_task(timeout=1.0)
            if task is None:
                continue

            try:
                if task.get("type") != task_type:
                    event_bus.publish_task(task)
                    await asyncio.sleep(0.05)
                    continue

                owner  = task["owner"]
                repo   = task["repo"]
                p_type = task["type"]
                page   = task.get("page", 1)
                since  = task.get("since", "")
                base_url = "https://api.github.com"
                data_prs = None

                if p_type == "issue_comments":
                    url    = f"{base_url}/repos/{owner}/{repo}/issues/comments"
                    params = {"since": since, "page": page, "per_page": 100}
                    resp, data = await requester.fetch(url, params)

                elif p_type == "pr_comments":
                    url    = f"{base_url}/repos/{owner}/{repo}/pulls/comments"
                    params = {"since": since, "page": page, "per_page": 100}
                    resp, data = await requester.fetch(url, params)

                elif p_type == "closed_issues":
                    url    = f"{base_url}/repos/{owner}/{repo}/issues"
                    params = {"state": "closed", "since": since, "page": page, "per_page": 100}
                    resp, data = await requester.fetch(url, params)

                elif p_type == "pr_reviews":
                    url_prs   = f"{base_url}/repos/{owner}/{repo}/pulls"
                    resp_prs, data_prs = await requester.fetch(
                        url_prs, {"state": "closed", "page": page, "per_page": 30}
                    )
                    if resp_prs and resp_prs.status in [403, 429]:
                        raise Exception(f"Rate Limit nos PRs: {resp_prs.status}")

                    reviews_data: List[dict] = []
                    if data_prs:
                        for pr in data_prs:
                            if pr.get("merged_at"):
                                pr_author = pr.get("user", {}).get("login")
                                pr_url    = (
                                    f"{base_url}/repos/{owner}/{repo}"
                                    f"/pulls/{pr['number']}"
                                )
                                url_rev = f"{pr_url}/reviews"
                                _, data_rev = await requester.fetch(url_rev, {"per_page": 100})
                                if data_rev:
                                    for review in data_rev:
                                        review["_pr_author"] = pr_author
                                        review["_pr_url"]    = pr_url
                                    reviews_data.extend(data_rev)
                    resp, data = resp_prs, reviews_data

                else:
                    logging.warning(f"Worker-{worker_id} (sem token): tipo desconhecido '{p_type}'")
                    continue

                requests_processed += 1
                if requests_processed % 500 == 0:
                    logging.info(f"Worker-{worker_id} (sem token) processou {requests_processed} requests.")

                if resp and resp.status in [403, 429]:
                    reset_time = int(resp.headers.get("X-RateLimit-Reset", time.time() + 3600))
                    rate_limiter.set_global_cooldown(reset_time)
                    wait_min = max(0, int((reset_time - time.time()) / 60))
                    event_bus.publish_notification({
                        "type":       "TOKEN_COOLDOWN",
                        "token":      "unauthenticated",
                        "reset_time": reset_time,
                        "wait_min":   wait_min
                    })
                    event_bus.publish_task(task)

                elif resp and resp.status == 200 and data:
                    event_bus.publish_data({
                        "type":      "DATA_EXTRACTED",
                        "data_type": p_type,
                        "payload":   data
                    })
                    has_more = (
                        (data_prs is not None and len(data_prs) >= 30)
                        if p_type == "pr_reviews"
                        else len(data) >= 90
                    )
                    if has_more:
                        next_task = {**task, "page": page + 1}
                        event_bus.publish_task(next_task)

            except Exception as e:
                logging.error(
                    f"Erro no Worker-{worker_id} sem token "
                    f"({task_type} pág.{task.get('page', 1)}): {e}"
                )
            finally:
                event_bus.task_done()


def untokenized_hybrid_worker_thread(
    worker_id: int,
    task_type: str,
    event_bus: EventBus,
    rate_limiter: UnauthenticatedRateLimiter,
    shutdown_event: threading.Event
):
    logging.info(f"Worker-{worker_id} (sem token, tipo {task_type}) iniciado.")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            untokenized_hybrid_worker_async(
                worker_id, task_type, event_bus, rate_limiter, shutdown_event
            )
        )
    finally:
        loop.close()
        logging.info(f"Worker-{worker_id} (sem token, tipo {task_type}) encerrado.")

# ==============================================================================
# 7. STORAGE WORKER OTIMIZADO (REUTILIZADO PARA AMBOS OS MODOS)
# ==============================================================================
class BufferedStorageWorker(threading.Thread):
    def __init__(self, event_bus: EventBus, shutdown_mgr: ShutdownManager):
        super().__init__(name="Storage-Worker", daemon=True)
        self.event_bus    = event_bus
        self.shutdown_mgr = shutdown_mgr
        self.file_lock    = threading.Lock()
        self.max_size_bytes = 200 * 1024 * 1024   # 200 MB por arquivo
        self.data_json_dir  = get_diretory("json")
        self.base_files = {
            "issue_comments": "issue_comments",
            "pr_comments":    "pr_comments",
            "closed_issues":  "closed_issues",
            "pr_reviews":     "pr_reviews_merges"
        }
        self.current_parts  = {key: 1 for key in self.base_files}
        self.memory_buffer  = {key: [] for key in self.base_files}
        self.buffer_limit   = 2000

    def _get_current_filename(self, data_type: str) -> str:
        base = self.base_files[data_type]
        part = self.current_parts[data_type]
        return concat_path(self.data_json_dir, f"{base}_part_{part:02d}.json")

    def _check_and_rotate_file(self, filename: str, data_type: str):
        if manager.exists(filename):
            if manager.getsize(filename) >= (self.max_size_bytes - 5 * 1024 * 1024):
                self.current_parts[data_type] += 1
                logging.info(
                    f"🔄 Arquivo {filename} atingiu o limite. "
                    f"Rotacionando para parte {self.current_parts[data_type]}"
                )

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
                size_mb = manager.getsize(filename) / (1024 * 1024)
                logging.info(
                    f"💾 [Storage] Salvo {len(self.memory_buffer[data_type])} registros "
                    f"em {filename} ({size_mb:.2f} MB)"
                )
                self.memory_buffer[data_type] = []
            except Exception as e:
                logging.error(f"Erro ao salvar em {filename}: {e}")

    def run(self):
        logging.info("Storage-Worker iniciado (Modo Bufferizado de Alta Performance).")
        while not self.shutdown_mgr.is_shutdown_requested() or not self.event_bus.data_queue.empty():
            event = self.event_bus.consume_data(timeout=1.0)
            if not event:
                for dtype in self.base_files:
                    if len(self.memory_buffer[dtype]) >= self.buffer_limit:
                        self._flush_buffer(dtype)
                continue
            if event["type"] == "DATA_EXTRACTED":
                data_type = event["data_type"]
                payload   = event["payload"]
                self.memory_buffer[data_type].extend(payload)
                if len(self.memory_buffer[data_type]) >= self.buffer_limit:
                    self._flush_buffer(data_type)
        # Flush final
        logging.info("Storage-Worker realizando flush final de dados...")
        for dtype in self.base_files:
            if self.memory_buffer[dtype]:
                self._flush_buffer(dtype)
        logging.info("Storage-Worker encerrado com sucesso.")

# ==============================================================================
# 8. ORCHESTRATOR (MODO COM TOKEN)
# ==============================================================================
class Orchestrator:
    def __init__(
        self,
        tokens: List[str],
        target_user: str,
        target_repo: str,
        years_back: int = 5
    ):
        self.shutdown_mgr = ShutdownManager()
        valid_tokens = TokenCertifier.validate_tokens(tokens)
        if not valid_tokens:
            raise ValueError("Nenhum token válido foi fornecido. Encerrando.")

        self.token_manager = TokenManager(valid_tokens)
        self.event_bus     = EventBus()
        self.target_user   = target_user
        self.target_repo   = target_repo
        self.task_types    = ["issue_comments", "pr_comments", "closed_issues", "pr_reviews"]

        since_date = (
            datetime.now() - timedelta(days=years_back * 365)
        ).strftime("%Y-%m-%dT00:00:00Z")
        self.since_date = since_date
        logging.info(f"Janela de mineração desde: {since_date}")

        total_threads = len(self.task_types) * THREADS_PER_TYPE
        logging.info(
            f"Configurando {total_threads} Threads Híbridas "
            f"({THREADS_PER_TYPE}/tipo × {MAX_ASYNC_CONCURRENCY_PER_THREAD} async req/thread)."
        )
        self.storage        = BufferedStorageWorker(self.event_bus, self.shutdown_mgr)
        self.worker_threads: List[threading.Thread] = []

    def start(self):
        logging.info("🚀 Orchestrator Híbrido iniciando (MODO COM TOKEN)...")
        self.storage.start()

        thread_id = 1
        for task_type in self.task_types:
            for i in range(THREADS_PER_TYPE):
                t = threading.Thread(
                    target=hybrid_miner_worker,
                    args=(thread_id, task_type, self.event_bus, self.token_manager, self.shutdown_mgr),
                    name=f"Miner-{task_type}-{i + 1}"
                )
                t.start()
                self.worker_threads.append(t)
                thread_id += 1

        for task_type in self.task_types:
            self.event_bus.publish_task({
                "owner": self.target_user,
                "repo":  self.target_repo,
                "type":  task_type,
                "page":  1,
                "since": self.since_date
            })

        mining_completed = threading.Event()

        def wait_for_completion():
            self.event_bus.task_queue.join()
            mining_completed.set()
            self.event_bus.publish_notification({"type": "MINING_COMPLETE"})

        threading.Thread(target=wait_for_completion, daemon=True, name="Completion-Watcher").start()

        last_cooldown_notify = 0.0
        try:
            while not self.shutdown_mgr.is_shutdown_requested():
                if mining_completed.is_set():
                    logging.info("✅ Mineração concluída. Nenhuma tarefa pendente.")
                    break

                event = self.event_bus.consume_notification(timeout=0.5)
                if event:
                    if event["type"] == "TOKEN_COOLDOWN":
                        token = event["token"]
                        reset = event.get("reset_time", 0)
                        wait_min = max(0, int((reset - time.time()) / 60))
                        logging.warning(
                            f"⚠️ Cooldown: Token ...{token[-4:]} bloqueado "
                            f"(~{wait_min} min para reset)."
                        )
                    elif event["type"] == "MINING_COMPLETE":
                        break

                if self.token_manager.all_in_cooldown():
                    now = time.time()
                    if now - last_cooldown_notify > 30:
                        reset_at = self.token_manager.get_next_reset_time()
                        wait_min = max(0, int((reset_at - now) / 60))
                        logging.error(
                            f"🛑 CRÍTICO: TODOS os tokens em cooldown! "
                            f"Mineração suspensa por ~{wait_min} min."
                        )
                        last_cooldown_notify = now

                time.sleep(0.1)

        except KeyboardInterrupt:
            logging.info("\n⚠️ Interrupção manual (Ctrl+C).")
            self.shutdown_mgr.request_shutdown()

        self._cleanup()
        logging.info("Orchestrator finalizado.")

    def _cleanup(self):
        logging.info("Aguardando finalização das threads e storage...")
        self.shutdown_mgr.request_shutdown()
        for t in self.worker_threads:
            t.join(timeout=5.0)
        self.storage.join(timeout=5.0)
        logging.info("✅ Aplicação encerrada com sucesso.")

# ==============================================================================
# 8B. UNTOKENIZED RUNNER (MODO SEM TOKEN)
#     REFACTOR: usa ShutdownManager nativo em vez de objeto anônimo (hack removido)
# ==============================================================================
def untokenized_runner(target_user: str, target_repo: str, years_back: int = 5):
    logging.info("🚀 Iniciando minerador SEM TOKEN (limite: 60 requisições/hora).")
    shutdown_mgr      = ShutdownManager()
    event_bus         = EventBus()
    global_rate_limiter = UnauthenticatedRateLimiter()

    # BufferedStorageWorker usa ShutdownManager nativo (sem hack de objeto anônimo)
    storage = BufferedStorageWorker(event_bus, shutdown_mgr)
    storage.start()

    task_types = ["issue_comments", "pr_comments", "closed_issues", "pr_reviews"]
    shutdown_event = threading.Event()   # Event dedicado para os workers async
    threads: List[threading.Thread] = []

    for task_type in task_types:
        for i in range(THREADS_PER_TYPE):
            t = threading.Thread(
                target=untokenized_hybrid_worker_thread,
                args=(i + 1, task_type, event_bus, global_rate_limiter, shutdown_event),
                name=f"NoToken-{task_type}-{i + 1}"
            )
            t.start()
            threads.append(t)

    since_date = (
        datetime.now() - timedelta(days=years_back * 365)
    ).strftime("%Y-%m-%dT00:00:00Z")

    for task_type in task_types:
        event_bus.publish_task({
            "owner": target_user,
            "repo":  target_repo,
            "type":  task_type,
            "page":  1,
            "since": since_date
        })

    mining_completed = threading.Event()

    def wait_tasks():
        event_bus.task_queue.join()
        mining_completed.set()
        event_bus.publish_notification({"type": "MINING_COMPLETE"})

    threading.Thread(target=wait_tasks, daemon=True, name="Completion-Watcher").start()

    try:
        while not shutdown_event.is_set():
            if mining_completed.is_set():
                logging.info("✅ Mineração sem token concluída.")
                break

            note = event_bus.consume_notification(timeout=0.5)
            if note:
                if note["type"] == "TOKEN_COOLDOWN":
                    wait_min = note.get("wait_min", 0)
                    logging.warning(
                        f"📢 Rate limit excedido (sem token). "
                        f"Aguardando ~{wait_min} min para reset..."
                    )
                elif note["type"] == "MINING_COMPLETE":
                    logging.info("✅ Mineração sem token concluída.")
                    break

            time.sleep(0.1)

    except KeyboardInterrupt:
        logging.info("⚠️ Interrupção manual. Finalizando...")
    finally:
        shutdown_event.set()
        shutdown_mgr.request_shutdown()   # Sinaliza também o StorageWorker
        for t in threads:
            t.join(timeout=3.0)
        storage.join(timeout=5.0)
        logging.info("Minerador sem token finalizado.")

# ==============================================================================
# 9. JSON WORKER
# ==============================================================================
class JsonWorker:
    @staticmethod
    def obter_config(tag: str, str_arquivo_json: str) -> Any:
        if not manager.exists(str_arquivo_json):
            raise FileNotFoundError(f"Arquivo {str_arquivo_json} não encontrado.")
        with open(str_arquivo_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        if tag in data:
            return data[tag]
        raise KeyError(f"Chave '{tag}' não encontrada no JSON.")

# ==============================================================================
# 10. EXECUÇÃO PRINCIPAL
# ==============================================================================
def main():
    APP_PATH    = get_absoluto(__file__)
    PATH_QRCODE = concat_path(APP_PATH, "meu_qrcode.png")
    PATH_JSON   = concat_path(APP_PATH, "data.json")
    dados_recuperados: dict = {}
    GITHUB_TOKENS: List[str] = []
    GITHUB_TARGET_USER       = ""
    GITHUB_TARGET_REPOSITORY = ""

    # --- Carrega configuração via QR Code ou JSON ---
    if manager.exists(PATH_QRCODE):
        dados_recuperados = QRCodeJSONHandler.ler_qr_code(PATH_QRCODE) or {}
        if dados_recuperados:
            print("\n📦 Dados Recuperados do QR Code:")
            for chave, valor in dados_recuperados.items():
                print(chave)
                if isinstance(valor, list):
                    for item in valor:
                        print(f"|----> Token ...{item[-4:]}" if chave == "token" else item)
                else:
                    print(f"|----> {valor}")

    try:
        if dados_recuperados:
            GITHUB_TOKENS            = dados_recuperados.get("token", [])
            GITHUB_TARGET_USER       = dados_recuperados.get("target_user", "")
            GITHUB_TARGET_REPOSITORY = dados_recuperados.get("target_repo", "")
        else:
            GITHUB_TOKENS            = JsonWorker.obter_config("token",       PATH_JSON)
            GITHUB_TARGET_USER       = JsonWorker.obter_config("target_user", PATH_JSON)
            GITHUB_TARGET_REPOSITORY = JsonWorker.obter_config("target_repo", PATH_JSON)

        if isinstance(GITHUB_TOKENS, str):
            GITHUB_TOKENS = [GITHUB_TOKENS]

        DEFAULT_YEARS = 5
        try:
            YEARS_OF_HISTORY = int(
                input(f"\nQuantos anos preciso voltar? (Padrão {DEFAULT_YEARS}): ")
                or DEFAULT_YEARS
            )
            if YEARS_OF_HISTORY < 1:
                raise ValueError
        except (ValueError, EOFError):
            print(f"Preconfigurando para DEFAULT {DEFAULT_YEARS} anos.")
            YEARS_OF_HISTORY = DEFAULT_YEARS

        print(f"\nAlvo: {GITHUB_TARGET_USER}/{GITHUB_TARGET_REPOSITORY}")
        print(f"Janela: {YEARS_OF_HISTORY} anos")

        use_tokens = (
            input("Deseja usar tokens para mineração rápida? (s/N): ").strip().lower() == "s"
        )

        if use_tokens:
            print(f"Tokens carregados: {len(GITHUB_TOKENS)}")
            print(
                f"Arquitetura: {len(GITHUB_TOKENS)} tokens × "
                f"{len(['issue_comments','pr_comments','closed_issues','pr_reviews']) * THREADS_PER_TYPE}"
                f" Threads Híbridas (Semáforo {MAX_ASYNC_CONCURRENCY_PER_THREAD})"
            )
            try:
                app = Orchestrator(
                    tokens=GITHUB_TOKENS,
                    target_user=GITHUB_TARGET_USER,
                    target_repo=GITHUB_TARGET_REPOSITORY,
                    years_back=YEARS_OF_HISTORY
                )
                app.start()
            except ValueError:
                print("⚠️ Nenhum token válido encontrado. Alternando para modo SEM TOKEN.")
                untokenized_runner(
                    target_user=GITHUB_TARGET_USER,
                    target_repo=GITHUB_TARGET_REPOSITORY,
                    years_back=YEARS_OF_HISTORY
                )
        else:
            print("⚠️ Modo SEM TOKEN. Limite: 60 req/hora. Mineração mais lenta.")
            untokenized_runner(
                target_user=GITHUB_TARGET_USER,
                target_repo=GITHUB_TARGET_REPOSITORY,
                years_back=YEARS_OF_HISTORY
            )

    except Exception as e:
        logging.error(f"Erro fatal: {e}", exc_info=True)


if __name__ == "__main__":
    import sys
    if "--gui" in sys.argv:
        from gui_ctk import main as gui_main
        gui_main()
    else:
        main()
        init_lapidador()

"""
Minerador de Interações do GitHub — Implementação Nativa (sem PyGithub)
=======================================================================

Substitui a dependência ``PyGithub`` por chamadas diretas à API REST v3 do
GitHub usando apenas a biblioteca ``requests`` (já comumente disponível no
host). Isto evita o "bug da lib do GitHub": instalações quebradas de
``pygithub``/``github`` no sistema host paralisavam toda a aplicação porque
``main_gui.py`` importa este módulo no topo.

Mantém a mesma interface pública do minerador original:

    - ``TOKENS_GRUPO``       : lista de tokens (compatível com main_gui)
    - ``REPO_NAME``          : repositório-alvo  (compatível com main_gui)
    - ``minerar_dados()``    : função principal de extração
    - ``ThreadSafeTokenManager`` / ``CSVThreadSafeWriter`` : utilitários
                                preservados para retrocompatibilidade.

Os três grafos do TCC continuam sendo gerados:
    G1: COMMENT_ON_ISSUE_OR_PR
    G2: ISSUE_CLOSED_BY_OTHER
    G3: PR_REVIEW_OR_APPROVAL  +  PR_MERGE
"""
from __future__ import annotations

import csv
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Any, Dict, Iterable, List, Optional

import requests

from filemanager import FileSet # Filemanager
    
# ──────────────────────────────────────────────────────────────────────────
# POOL DE CREDENCIAIS — ADICIONE OS TOKENS DOS INTEGRANTES DO GRUPO AQUI
# ──────────────────────────────────────────────────────────────────────────
TOKENS_GRUPO: List[str] = [
    "INSIRA_AQUI_SEU_TOKEN",
    "INSIRA_AQUI_SEU_TOKEN",
    "INSIRA_AQUI_SEU_TOKEN",
    "INSIRA_AQUI_SEU_TOKEN",
]

REPO_NAME = "vuejs/core"

GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 30

PATH_CSV = FileSet.set_path_f("csv","interacoes_reais.csv")

# ==========================================================================
# Cliente REST mínimo (substitui PyGithub)
# ==========================================================================
class GithubRestClient:
    """Cliente HTTP fino para a REST v3 do GitHub.

    Sem dependências externas além de ``requests``. Implementa apenas o
    subconjunto de endpoints usado pelo minerador.
    """

    def __init__(self, token: str, session: Optional[requests.Session] = None) -> None:
        self.token = token
        self.session = session or requests.Session()
        self.session.headers.update({
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "tcc-grafo-minerador/2.0",
        })

    # -- helpers HTTP ------------------------------------------------------
    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = path if path.startswith("http") else f"{GITHUB_API}{path}"
        return self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)

    def _get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        r = self._get(path, params=params)
        r.raise_for_status()
        return r.json()

    def _paginate(self, path: str, params: Optional[Dict[str, Any]] = None) -> Iterable[Dict[str, Any]]:
        """Itera por todas as páginas usando o cabeçalho ``Link``."""
        url: Optional[str] = f"{GITHUB_API}{path}"
        first_params = dict(params or {})
        first_params.setdefault("per_page", 100)
        while url:
            r = self.session.get(url, params=first_params, timeout=DEFAULT_TIMEOUT)
            r.raise_for_status()
            batch = r.json()
            if not isinstance(batch, list):
                return
            for item in batch:
                yield item
            url = r.links.get("next", {}).get("url")
            first_params = None  # parâmetros vão no próprio link "next"

    # -- endpoints utilizados pelo TCC ------------------------------------
    def get_issues_page(self, repo: str, page: int, state: str = "all") -> List[Dict[str, Any]]:
        return self._get_json(f"/repos/{repo}/issues",
                              params={"state": state, "per_page": 30, "page": page + 1})

    def get_pulls_page(self, repo: str, page: int, state: str = "all") -> List[Dict[str, Any]]:
        return self._get_json(f"/repos/{repo}/pulls",
                              params={"state": state, "per_page": 30, "page": page + 1})

    def get_issue(self, repo: str, number: int) -> Dict[str, Any]:
        return self._get_json(f"/repos/{repo}/issues/{number}")

    def get_pull(self, repo: str, number: int) -> Dict[str, Any]:
        return self._get_json(f"/repos/{repo}/pulls/{number}")

    def list_issue_comments(self, repo: str, number: int) -> List[Dict[str, Any]]:
        return list(self._paginate(f"/repos/{repo}/issues/{number}/comments"))

    def list_pr_reviews(self, repo: str, number: int) -> List[Dict[str, Any]]:
        return list(self._paginate(f"/repos/{repo}/pulls/{number}/reviews"))


# ==========================================================================
# Gerência thread-safe de pool de tokens (compatível com versão antiga)
# ==========================================================================
class ThreadSafeTokenManager:
    """Distribui clientes REST round-robin entre threads (compat-API)."""

    def __init__(self, tokens: Iterable[str]) -> None:
        self.tokens = [t for t in tokens
                       if t and "TOKEN_DO" not in t and t != "MEU_TOKEN"
                       and t != "INSIRA_AQUI_SEU_TOKEN"]
        if not self.tokens:
            print("❌ ERRO CRÍTICO: Forneça ao menos um Token válido em TOKENS_GRUPO!")
            sys.exit(1)
        self.index = 0
        self.lock = Lock()
        # Reutiliza Sessions por token (mantém keep-alive e baixa latência)
        self._clients = [GithubRestClient(tok) for tok in self.tokens]
        print(f"🔄 Pool ativo com {len(self.tokens)} token(s). Distribuição paralela ativada.")

    def get_client(self) -> GithubRestClient:
        with self.lock:
            client = self._clients[self.index]
            self.index = (self.index + 1) % len(self._clients)
            return client

    # Mantém o nome antigo para qualquer chamador legado
    def get_github_instance(self) -> GithubRestClient:  # noqa: D401
        return self.get_client()


# ==========================================================================
# Escritor CSV thread-safe (idêntico à versão anterior)
# ==========================================================================
class CSVThreadSafeWriter:
    def __init__(self, filename: str) -> None:
        self.file = open(filename, mode="w", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)
        self.lock = Lock()
        self.writer.writerow(["actor", "target", "type"])

    def write_row(self, row: List[str]) -> None:
        with self.lock:
            self.writer.writerow(row)

    def close(self) -> None:
        self.file.close()


# ==========================================================================
# Tratamento de rate-limit (substitui GithubException)
# ==========================================================================
def _handle_http_error(exc: requests.HTTPError) -> bool:
    """Retorna True se a operação deve ser repetida (rate-limit)."""
    status = exc.response.status_code if exc.response is not None else 0
    if status in (403, 429):
        print("\n⚠️ Rate Limit atingido em uma thread. Aguardando 60s para retomar...")
        time.sleep(60)
        return True
    return False


# ==========================================================================
# Workers que extraem os 3 grafos do TCC
# ==========================================================================
def processar_uma_issue(issue_number: int,
                        token_manager: ThreadSafeTokenManager,
                        csv_writer: CSVThreadSafeWriter) -> bool:
    while True:
        client = token_manager.get_client()
        try:
            issue = client.get_issue(REPO_NAME, issue_number)
            target = (issue.get("user") or {}).get("login")
            if not target:
                return False

            # Grafo 1 — Comentários em issues
            for comment in client.list_issue_comments(REPO_NAME, issue_number):
                actor = (comment.get("user") or {}).get("login")
                if actor and actor != target:
                    csv_writer.write_row([actor, target, "COMMENT_ON_ISSUE_OR_PR"])

            # Grafo 2 — Fechamento de issue por outro usuário
            closed_by = (issue.get("closed_by") or {}).get("login")
            if issue.get("state") == "closed" and closed_by and closed_by != target:
                csv_writer.write_row([closed_by, target, "ISSUE_CLOSED_BY_OTHER"])
            return True
        except requests.HTTPError as e:
            if _handle_http_error(e):
                continue
            return False
        except requests.RequestException:
            return False


def processar_um_pr(pr_number: int,
                    token_manager: ThreadSafeTokenManager,
                    csv_writer: CSVThreadSafeWriter) -> bool:
    while True:
        client = token_manager.get_client()
        try:
            pr = client.get_pull(REPO_NAME, pr_number)
            target = (pr.get("user") or {}).get("login")
            if not target:
                return False

            # Grafo 1 — Comentários no PR (issue comments)
            for comment in client.list_issue_comments(REPO_NAME, pr_number):
                actor = (comment.get("user") or {}).get("login")
                if actor and actor != target:
                    csv_writer.write_row([actor, target, "COMMENT_ON_ISSUE_OR_PR"])

            # Grafo 3 — Revisões / Aprovações
            for review in client.list_pr_reviews(REPO_NAME, pr_number):
                actor = (review.get("user") or {}).get("login")
                if actor and actor != target:
                    csv_writer.write_row([actor, target, "PR_REVIEW_OR_APPROVAL"])

            # Grafo 3 — Merge de PR
            if pr.get("merged") and pr.get("merged_by"):
                actor = pr["merged_by"].get("login")
                if actor and actor != target:
                    csv_writer.write_row([actor, target, "PR_MERGE"])
            return True
        except requests.HTTPError as e:
            if _handle_http_error(e):
                continue
            return False
        except requests.RequestException:
            return False


# ==========================================================================
# Orquestrador (substitui o ``minerar_dados`` antigo)
# ==========================================================================
def minerar_dados(LIMITE_REGISTROS:int = 200, NUMBER_PER_PAGE:int =100) -> None:
    print("═══════════════════════════════════════════════")
    print(" 🚀 Iniciando Mineração Multithread (REST nativa):", REPO_NAME)
    print("═══════════════════════════════════════════════")

    token_manager = ThreadSafeTokenManager(TOKENS_GRUPO)
    csv_writer = CSVThreadSafeWriter(PATH_CSV)
    tempo_inicial = time.time()

    max_workers = len(token_manager.tokens) * 3
    print(f"⚡ Disparando pool com {max_workers} threads simultâneas...")

    def worker_issues(page_num: int) -> int:
        client = token_manager.get_client()
        try:
            issues_page = client.get_issues_page(REPO_NAME, page_num)
        except requests.HTTPError as e:
            if _handle_http_error(e):
                return 0
            return 0
        except requests.RequestException:
            return 0

        count = 0
        for iss in issues_page:
            # Issues "puras" (não PR) — PRs aparecem em /issues com pull_request
            if iss.get("pull_request"):
                continue
            processar_uma_issue(iss["number"], token_manager, csv_writer)
            count += 1
        return count

    def worker_pulls(page_num: int) -> int:
        client = token_manager.get_client()
        try:
            pulls_page = client.get_pulls_page(REPO_NAME, page_num)
        except requests.HTTPError as e:
            if _handle_http_error(e):
                return 0
            return 0
        except requests.RequestException:
            return 0

        count = 0
        for pr in pulls_page:
            processar_um_pr(pr["number"], token_manager, csv_writer)
            count += 1
        return count

    SAFE_COUNTER_RANGE = 1 # ADICIONA X A MAIS NA CONTAGEM DE PÁGINAS
    paginas_necessarias = (LIMITE_REGISTROS // NUMBER_PER_PAGE) + SAFE_COUNTER_RANGE
    total_itens = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        print(f"📥 Agendando extração paralela de aproximada de {paginas_necessarias} páginas...")
        for i in range(paginas_necessarias):
            futures.append(executor.submit(worker_issues, i))
            futures.append(executor.submit(worker_pulls, i))
        EXPANDER_PROCESSED_PAGES = 2 # MULTIPLICA O VALOR BASE DE PÁGINAS POR X 
        print(f"📥 Expandindo para {paginas_necessarias * EXPANDER_PROCESSED_PAGES} páginas...")
        for idx, future in enumerate(as_completed(futures)):
            total_itens += future.result()
            sys.stdout.write(
                f"\rPáginas processadas: {idx + 1}/{paginas_necessarias * EXPANDER_PROCESSED_PAGES} "
                f"| Registros salvos: ~{total_itens}\n"
            )
            sys.stdout.flush()

    csv_writer.close()
    tempo_final = time.time()

    print("\n\n═══════════════════════════════════════════════")
    print(" 🎉 FIM: Extração finalizada com sucesso!")
    print(f" ⏱️  Tempo total: {tempo_final - tempo_inicial:.2f}s")
    print("═══════════════════════════════════════════════")


if __name__ == "__main__":
    minerar_dados()

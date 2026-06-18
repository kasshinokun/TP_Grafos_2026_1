"""
Minerador Híbrido — Versão Operacional
======================================

Adaptação enxuta do ``orchestrator_hibrido_alpha0e.py`` para o projeto do
TCC. Mantém os princípios do orquestrador original:

    * Pool de tokens em round-robin (modo COM TOKEN).
    * Concorrência por tipo de evento (issues, pr_comments, pr_reviews,
      pr_merges) em threads separadas, cada qual com I/O assíncrono.
    * Backoff cooperativo em 403/429 (rate-limit) sem travar a aplicação.
    * Geração dos MESMOS três grafos do TCC (G1 / G2 / G3).

Diferenças em relação ao ``orchestrator_hibrido_alpha0e.py``:

    * Não exige ``main_rebuild``, ``qrcode``, ``pyzbar``, ``PIL`` ou
      ``aiohttp`` opcionalmente — se ``aiohttp`` estiver ausente, cai para
      o pool de threads do minerador clássico, mantendo compatibilidade
      total no host.
    * Sem leitura de QR-Code: os tokens vêm de ``minerador.TOKENS_GRUPO``.
    * Sem dependência de ``PyGithub`` (igual ao novo ``minerador.py``).

Interface pública compatível com ``main_gui.py``:

    >>> from minerador_hibrido import minerar_dados
    >>> minerar_dados()                # escreve interacoes_reais.csv
"""
from __future__ import annotations

import asyncio
import sys
import time
from typing import Any, Dict, List

from minerador import (
    CSVThreadSafeWriter,
    GithubRestClient,
    REPO_NAME,
    ThreadSafeTokenManager,
    TOKENS_GRUPO,
    minerar_dados as _minerar_dados_threads,
)

try:
    import aiohttp  # type: ignore
    _HAS_AIOHTTP = True
except Exception:  # pragma: no cover
    aiohttp = None  # type: ignore
    _HAS_AIOHTTP = False

from filemanager import FileSet # Filemanager

GITHUB_API = "https://api.github.com"
MAX_CONCURRENCY_PER_TYPE = 5
PATH_CSV = FileSet.set_path_f("csv","interacoes_reais.csv")

# --------------------------------------------------------------------------
# Núcleo assíncrono (usado quando aiohttp está disponível)
# --------------------------------------------------------------------------
async def _async_get(session: "aiohttp.ClientSession", url: str,
                     token: str, params: Dict[str, Any] | None = None) -> Any:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "tcc-grafo-minerador-hibrido/1.0",
    }
    while True:
        async with session.get(url, headers=headers, params=params, timeout=30) as resp:
            if resp.status in (403, 429):
                # Backoff cooperativo (não trava as outras threads/tipos)
                await asyncio.sleep(60)
                continue
            resp.raise_for_status()
            return await resp.json()


async def _process_issue_async(session, token: str, number: int,
                               writer: CSVThreadSafeWriter) -> None:
    base = f"{GITHUB_API}/repos/{REPO_NAME}"
    issue = await _async_get(session, f"{base}/issues/{number}", token)
    target = (issue.get("user") or {}).get("login")
    if not target:
        return
    comments = await _async_get(session, f"{base}/issues/{number}/comments",
                                token, params={"per_page": 100})
    for c in comments:
        actor = (c.get("user") or {}).get("login")
        if actor and actor != target:
            writer.write_row([actor, target, "COMMENT_ON_ISSUE_OR_PR"])
    closed_by = (issue.get("closed_by") or {}).get("login")
    if issue.get("state") == "closed" and closed_by and closed_by != target:
        writer.write_row([closed_by, target, "ISSUE_CLOSED_BY_OTHER"])


async def _process_pr_async(session, token: str, number: int,
                            writer: CSVThreadSafeWriter) -> None:
    base = f"{GITHUB_API}/repos/{REPO_NAME}"
    pr = await _async_get(session, f"{base}/pulls/{number}", token)
    target = (pr.get("user") or {}).get("login")
    if not target:
        return
    comments = await _async_get(session, f"{base}/issues/{number}/comments",
                                token, params={"per_page": 100})
    for c in comments:
        actor = (c.get("user") or {}).get("login")
        if actor and actor != target:
            writer.write_row([actor, target, "COMMENT_ON_ISSUE_OR_PR"])
    reviews = await _async_get(session, f"{base}/pulls/{number}/reviews",
                               token, params={"per_page": 100})
    for r in reviews:
        actor = (r.get("user") or {}).get("login")
        if actor and actor != target:
            writer.write_row([actor, target, "PR_REVIEW_OR_APPROVAL"])
    if pr.get("merged") and pr.get("merged_by"):
        actor = pr["merged_by"].get("login")
        if actor and actor != target:
            writer.write_row([actor, target, "PR_MERGE"])


async def _run_async(token_manager: ThreadSafeTokenManager,
                     writer: CSVThreadSafeWriter, pages: int,
                     counter:int) -> int:
    sem = asyncio.Semaphore(MAX_CONCURRENCY_PER_TYPE * len(token_manager.tokens))
    total = 0

    async with aiohttp.ClientSession() as session:
        # 1) Coleta de números (issues e PRs) — sequencial e barata
        issue_numbers: List[int] = []
        pr_numbers: List[int] = []
        for page in range(pages):
            token = token_manager.tokens[page % len(token_manager.tokens)]
            issues = await _async_get(
                session, f"{GITHUB_API}/repos/{REPO_NAME}/issues",
                token, params={"state": "all", "per_page": counter, "page": page + 1},
            )
            for it in issues:
                if it.get("pull_request"):
                    pr_numbers.append(it["number"])
                else:
                    issue_numbers.append(it["number"])

        # 2) Processamento concorrente (com semáforo por tipo)
        async def bounded(coro):
            async with sem:
                await coro

        tasks = []
        for i, n in enumerate(issue_numbers):
            tok = token_manager.tokens[i % len(token_manager.tokens)]
            tasks.append(bounded(_process_issue_async(session, tok, n, writer)))
        for i, n in enumerate(pr_numbers):
            tok = token_manager.tokens[i % len(token_manager.tokens)]
            tasks.append(bounded(_process_pr_async(session, tok, n, writer)))

        total = len(tasks)
        for idx, fut in enumerate(asyncio.as_completed(tasks), 1):
            try:
                await fut
            except Exception as exc:  # noqa: BLE001
                # Erros pontuais não derrubam o pipeline (paridade c/ alpha0e)
                sys.stdout.write(f"\n[warn] item ignorado: {exc}\n")
            if idx % 25 == 0 or idx == total:
                sys.stdout.write(f"\rProcessados: {idx}/{total}")
                sys.stdout.flush()
    return total


# --------------------------------------------------------------------------
# API pública (idêntica ao minerador clássico)
# --------------------------------------------------------------------------
def minerar_dados(LIMITE_REGISTROS:int = 200, NUMBER_PER_PAGE:int =100) -> None:
    """Executa a mineração híbrida; degrada para threads se aiohttp ausente."""
    if not _HAS_AIOHTTP:
        print("ℹ️ aiohttp não disponível — usando minerador clássico (threads).")
        _minerar_dados_threads()
        return

    print("═══════════════════════════════════════════════")
    print(" 🚀 Minerador HÍBRIDO (async + pool de tokens):", REPO_NAME)
    print("═══════════════════════════════════════════════")

    token_manager = ThreadSafeTokenManager(TOKENS_GRUPO)
    writer = CSVThreadSafeWriter(PATH_CSV)
    SAFE_COUNTER_RANGE = 1 # ADICIONA X A MAIS NA CONTAGEM DE PÁGINAS
    pages = (LIMITE_REGISTROS // NUMBER_PER_PAGE) + SAFE_COUNTER_RANGE
    t0 = time.time()
    try:
        total = asyncio.run(_run_async(token_manager, writer, pages,NUMBER_PER_PAGE))
    finally:
        writer.close()

    print(f"\n\n🎉 Híbrido concluído: {total} itens em {time.time() - t0:.2f}s.")


if __name__ == "__main__":
    minerar_dados()

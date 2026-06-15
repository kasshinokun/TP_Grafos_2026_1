import json
import logging
import os
import os.path as manager
from os.path import join as concat_path
from os.path import abspath as absoluto
import glob

# ============================
# FUNÇÕES AUXILIARES
# ============================
def get_absoluto(file: str):
    return manager.dirname(absoluto(file))

def get_diretory(name_diretory: str, condition: int = 2) -> str:
    APP_DIR = get_absoluto(__file__)
    if condition == 1:
        return concat_path(APP_DIR, name_diretory)
    else:
        DATA_DIR = concat_path(APP_DIR, name_diretory)
        os.makedirs(DATA_DIR, exist_ok=True)
        return DATA_DIR


class Lapidador:
    def __init__(self, data_dir: str):
        self.data_dir      = get_diretory(data_dir)    # diretório de saída (ex: 'work')
        self.data_json_dir = get_diretory("json")       # onde os JSONs brutos estão
        self.users         = {}   # login -> id
        self.user_count    = 0
        self.interactions  = []   # lista de dicts: {"source", "target", "type"}

    # ------------------------------------------------------------------
    # Gerenciamento de usuários
    # ------------------------------------------------------------------
    def get_user_id(self, login: str) -> int:
        if login not in self.users:
            self.users[login] = self.user_count
            self.user_count += 1
        return self.users[login]

    def _add_interaction(self, source: str, target: str, itype: str):
        if source and target and source != target:
            self.get_user_id(source)
            self.get_user_id(target)
            self.interactions.append({"source": source, "target": target, "type": itype})

    # ------------------------------------------------------------------
    # Construção de mapas auxiliares (corrige lacunas da API do GitHub)
    # ------------------------------------------------------------------
    def _build_issue_author_map(self) -> dict:
        """
        Constrói {issue_url -> author_login} a partir dos closed_issues.

        A API de issue_comments retorna o campo 'issue_url' (ex:
        https://api.github.com/repos/owner/repo/issues/123) mas NÃO inclui
        o autor da issue. Como mineramos as closed_issues separadamente —
        e cada objeto de issue traz 'url' e 'user.login' — usamos esses
        dados para reconstruir a autoria.
        """
        mapping = {}
        pattern = concat_path(self.data_json_dir, "closed_issues_part_*.json")
        files   = sorted(glob.glob(pattern))
        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for issue in data:
                url    = issue.get("url")
                author = issue.get("user", {}).get("login")
                if url and author:
                    mapping[url] = author
        logging.info(f"[Lapidador] Mapa de autores de issues: {len(mapping)} registros.")
        return mapping

    def _build_pr_author_map(self) -> dict:
        """
        Constrói {pr_url -> author_login} a partir dos pr_reviews enriquecidos.

        O orchestrator injeta '_pr_author' e '_pr_url' em cada review
        durante a mineração. Usamos esses campos para recuperar o autor
        do PR sem precisar de uma requisição extra.
        """
        mapping = {}
        pattern = concat_path(self.data_json_dir, "pr_reviews_merges_part_*.json")
        files   = sorted(glob.glob(pattern))
        for filepath in files:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for review in data:
                pr_url    = review.get("_pr_url")
                pr_author = review.get("_pr_author")
                if pr_url and pr_author:
                    mapping[pr_url] = pr_author
        logging.info(f"[Lapidador] Mapa de autores de PRs: {len(mapping)} registros.")
        return mapping

    # ------------------------------------------------------------------
    # Processadores por tipo de dado
    # ------------------------------------------------------------------
    def process_issue_comments(self, part_pattern: str, issue_author_map: dict | None = None):
        """
        Interação: comentador → autor da issue.

        A API /repos/{owner}/{repo}/issues/comments não emite o objeto
        'issue' aninhado. Usamos 'issue_url' como chave no mapa construído
        a partir dos closed_issues. Issues abertas que não estejam no mapa
        são ignoradas (sem dados suficientes para determinar o autor).
        """
        pattern = concat_path(self.data_json_dir, part_pattern)
        skipped = 0
        for filepath in sorted(glob.glob(pattern)):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for comment in data:
                commenter = comment.get("user", {}).get("login")
                if not commenter:
                    continue

                # Tenta o campo enriquecido primeiro, depois o mapa
                issue  = comment.get("issue")
                author = issue.get("user", {}).get("login") if issue else None

                if not author and issue_author_map:
                    issue_url = comment.get("issue_url")
                    author    = issue_author_map.get(issue_url)

                if author:
                    self._add_interaction(commenter, author, "comment")
                else:
                    skipped += 1

        if skipped:
            logging.warning(
                f"[Lapidador] process_issue_comments: {skipped} comentário(s) ignorado(s) "
                "(issue não encontrada nos closed_issues — pode ser issue aberta)."
            )

    def process_pr_comments(self, part_pattern: str, pr_author_map: dict | None = None):
        """
        Interação: comentador → autor do PR.

        A API /repos/{owner}/{repo}/pulls/comments retorna 'pull_request_url'
        mas não o objeto do PR com o autor. Usamos o mapa construído a
        partir dos pr_reviews enriquecidos pelo orchestrator.
        """
        pattern = concat_path(self.data_json_dir, part_pattern)
        skipped = 0
        for filepath in sorted(glob.glob(pattern)):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for comment in data:
                commenter = comment.get("user", {}).get("login")
                if not commenter:
                    continue

                # Tenta o campo enriquecido '_pr_author' (se presente)
                author = comment.get("_pr_author")

                if not author and pr_author_map:
                    pr_url = comment.get("pull_request_url")
                    author = pr_author_map.get(pr_url)

                if author:
                    self._add_interaction(commenter, author, "comment")
                else:
                    skipped += 1

        if skipped:
            logging.warning(
                f"[Lapidador] process_pr_comments: {skipped} comentário(s) ignorado(s) "
                "(PR não encontrado no mapa de autores — pode ser PR não mergeado)."
            )

    def process_closed_issues(self, part_pattern: str):
        """Interação: quem fechou a issue → autor da issue."""
        pattern = concat_path(self.data_json_dir, part_pattern)
        for filepath in sorted(glob.glob(pattern)):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for issue in data:
                author    = issue.get("user", {}).get("login")
                closed_by = issue.get("closed_by")
                closer    = closed_by.get("login") if closed_by else None
                self._add_interaction(closer, author, "issue_close")

    def process_pr_reviews(self, part_pattern: str):
        """
        Interação: revisor → autor do PR.

        O orchestrator enriquece cada review com '_pr_author'.
        """
        pattern = concat_path(self.data_json_dir, part_pattern)
        skipped = 0
        for filepath in sorted(glob.glob(pattern)):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for review in data:
                reviewer = review.get("user", {}).get("login")
                if not reviewer:
                    continue
                # Campo enriquecido pelo orchestrator
                author = review.get("_pr_author")
                if author:
                    self._add_interaction(reviewer, author, "review")
                else:
                    skipped += 1

        if skipped:
            logging.warning(
                f"[Lapidador] process_pr_reviews: {skipped} review(s) ignorada(s) "
                "(campo '_pr_author' ausente — dados minerados antes da correção?)."
            )

    # ------------------------------------------------------------------
    # Ponto de entrada principal
    # ------------------------------------------------------------------
    def lapidar(self) -> str:
        logging.info("[Lapidador] Construindo mapas de autores...")
        issue_author_map = self._build_issue_author_map()
        pr_author_map    = self._build_pr_author_map()

        logging.info("[Lapidador] Processando arquivos brutos...")
        self.process_issue_comments("issue_comments_part_*.json",   issue_author_map)
        self.process_pr_comments   ("pr_comments_part_*.json",      pr_author_map)
        self.process_closed_issues ("closed_issues_part_*.json")
        self.process_pr_reviews    ("pr_reviews_merges_part_*.json")

        resultado = {
            "metadata": {
                "total_users":        self.user_count,
                "total_interactions": len(self.interactions),
            },
            "users":        self.users,
            "interactions": self.interactions,
        }

        output_path = concat_path(self.data_dir, "dados_lapidados.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=2, ensure_ascii=False)

        logging.info(
            f"[Lapidador] Concluído — {self.user_count} usuários, "
            f"{len(self.interactions)} interações → {output_path}"
        )
        return output_path

    @staticmethod
    def initialize_work():
        return Lapidador("work")

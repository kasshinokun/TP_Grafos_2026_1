import csv
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from github import Github, GithubException

# ──────────────────────────────────────────────────────────────────────────
# POOL DE CREDENCIAIS - ADICIONE OS TOKENS DOS INTEGRANTES DO GRUPO AQUI
# ──────────────────────────────────────────────────────────────────────────
TOKENS_GRUPO = [
    "INSIRA_AQUI_SEU_TOKEN",  
    "INSIRA_AQUI_SEU_TOKEN",
    "INSIRA_AQUI_SEU_TOKEN",
    "INSIRA_AQUI_SEU_TOKEN"
]

REPO_NAME = "vuejs/core"  
LIMITE_REGISTROS = 900

class ThreadSafeTokenManager:
    """Gerencia a distribuição de instâncias do GitHub de forma thread-safe."""
    def __init__(self, tokens):
        self.tokens = [t for t in tokens if t and "TOKEN_DO" not in t and t != "MEU_TOKEN"]
        if not self.tokens:
            print("❌ ERRO CRÍTICO: Forneça ao menos um Token válido em TOKENS_GRUPO!")
            sys.exit(1)
        self.index = 0
        self.lock = Lock()
        print(f"🔄 Pool ativo com {len(self.tokens)} token(s). Distribuição paralela ativada.")

    def get_github_instance(self):
        """Retorna uma instância utilizando o próximo token de forma segura entre threads."""
        with self.lock:
            token = self.tokens[self.index]
            self.index = (self.index + 1) % len(self.tokens)
            return Github(token)


class CSVThreadSafeWriter:
    """Garante que a escrita no arquivo CSV não sofra condição de corrida (Race Condition)."""
    def __init__(self, filename):
        self.file = open(filename, mode='w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        self.lock = Lock()
        self.writer.writerow(['actor', 'target', 'type'])

    def write_row(self, row):
        with self.lock:
            self.writer.writerow(row)

    def close(self):
        self.file.close()


def processar_uma_issue(issue_number, token_manager, csv_writer):
    """Processa uma única issue de forma isolada em sua própria thread."""
    while True:
        g_instance = token_manager.get_github_instance()
        try:
            repo = g_instance.get_repo(REPO_NAME)
            issue_obj = repo.get_issue(issue_number)
            
            # Grafo 1: Comentários na issue [cite: 25]
            for comment in issue_obj.get_comments():
                actor = comment.user.login
                target = issue_obj.user.login
                if actor != target:  
                    csv_writer.write_row([actor, target, 'COMMENT_ON_ISSUE_OR_PR'])

            # Grafo 2: Fechamento de issue por outro usuário [cite: 26]
            if issue_obj.state == 'closed' and issue_obj.closed_by:
                actor = issue_obj.closed_by.login
                target = issue_obj.user.login
                if actor != target:
                    csv_writer.write_row([actor, target, 'ISSUE_CLOSED_BY_OTHER'])
            return True
        except GithubException as e:
            if e.status == 403:
                print(f"\n⚠️ Rate Limit atingido em uma das threads. Aguardando 1 minuto para reatar...")
                time.sleep(60)
            else:
                return False # Ignora outros erros específicos (ex: dados corrompidos)


def processar_um_pr(pr_number, token_manager, csv_writer):
    """Processa um único Pull Request de forma isolada em sua própria thread."""
    while True:
        g_instance = token_manager.get_github_instance()
        try:
            repo = g_instance.get_repo(REPO_NAME)
            pr_obj = repo.get_pull(pr_number)
            target = pr_obj.user.login
            
            # Grafo 1: Comentários no PR [cite: 25]
            for comment in pr_obj.get_issue_comments():
                actor = comment.user.login
                if actor != target:
                    csv_writer.write_row([actor, target, 'COMMENT_ON_ISSUE_OR_PR'])

            # Grafo 3: Revisões/Aprovações [cite: 27]
            for review in pr_obj.get_reviews():
                actor = review.user.login
                if actor != target:
                    csv_writer.write_row([actor, target, 'PR_REVIEW_OR_APPROVAL'])

            # Grafo 3: Merge de Pull Request [cite: 27]
            if pr_obj.merged and pr_obj.merged_by:
                actor = pr_obj.merged_by.login
                if actor != target:
                    csv_writer.write_row([actor, target, 'PR_MERGE'])
            return True
        except GithubException as e:
            if e.status == 403:
                print(f"\n⚠️ Rate Limit atingido em uma das threads. Aguardando 1 minuto para reatar...")
                time.sleep(60)
            else:
                return False


def minerar_dados():
    print("═══════════════════════════════════════════════")
    print(" 🚀 Iniciando Mineração Multithread:", REPO_NAME)
    print("═══════════════════════════════════════════════")
    
    token_manager = ThreadSafeTokenManager(TOKENS_GRUPO)
    csv_writer = CSVThreadSafeWriter('interacoes_reais.csv')
    tempo_inicial = time.time()

    # Configura dinamicamente o número de threads
    max_workers = len(token_manager.tokens) * 3 
    print(f"⚡ Disparando pool com {max_workers} threads simultâneas...")

    # Função interna para gerenciar o consumo de páginas de Issues por thread
    def worker_issues(page_num):
        g_instance = token_manager.get_github_instance()
        try:
            repo = g_instance.get_repo(REPO_NAME)
            issues_page = repo.get_issues(state='all').get_page(page_num)
            if not issues_page:
                return 0
            
            count = 0
            for iss in issues_page:
                if not iss.pull_request:
                    processar_uma_issue(iss.number, token_manager, csv_writer)
                    count += 1
            return count
        except Exception as e:
            # Se der erro de rate limit (403), trata silenciosamente na thread
            if "403" in str(e):
                time.sleep(60)
            return 0

    # Função interna para gerenciar o consumo de páginas de PRs por thread
    def worker_pulls(page_num):
        g_instance = token_manager.get_github_instance()
        try:
            repo = g_instance.get_repo(REPO_NAME)
            pulls_page = repo.get_pulls(state='all').get_page(page_num)
            if not pulls_page:
                return 0
            
            count = 0
            for pr in pulls_page:
                processar_um_pr(pr.number, token_manager, csv_writer)
                count += 1
            return count
        except Exception as e:
            if "403" in str(e):
                time.sleep(60)
            return 0

    # Determina quantas páginas precisamos buscar para atingir o limite aproximado
    # Como cada página traz 30 itens por padrão no GitHub: 900 / 30 = 30 páginas
    paginas_necessarias = (LIMITE_REGISTROS // 30) + 1
    total_itens_processados = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        
        print(f"📥 Agendando a extração paralela de {paginas_necessarias} páginas de dados...")
        for i in range(paginas_necessarias):
            futures.append(executor.submit(worker_issues, i))
            futures.append(executor.submit(worker_pulls, i))

        # Mostra o progresso conforme as páginas vão sendo concluídas
        for idx, future in enumerate(as_completed(futures)):
            total_itens_processados += future.result()
            sys.stdout.write(f"\rPáginas processadas: {idx + 1}/{paginas_necessarias * 2} | Registros salvos: ~{total_itens_processados}\n")
            sys.stdout.flush()

    csv_writer.close()
    tempo_final = time.time()
    
    print("\n\n═══════════════════════════════════════════════")
    print(" 🎉 FIM: Extração finalizada com sucesso!")
    print(f" ⏱️  Tempo total de processamento: {tempo_final - tempo_inicial:.2f} segundos")
    print("═══════════════════════════════════════════════")

if __name__ == "__main__":
    minerar_dados()
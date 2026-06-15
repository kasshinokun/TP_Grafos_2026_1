import csv
import sys
import time
from github import Github, GithubException

# ──────────────────────────────────────────────────────────────────────────
# POOL DE CREDENCIAIS - ADICIONE OS TOKENS DOS INTEGRANTES DO GRUPO AQUI
# ──────────────────────────────────────────────────────────────────────────
TOKENS_GRUPO = [
    "TOKEN_DO_INTEGRANTE_1",  # Deixe o seu aqui para o teste massivo solo
    "TOKEN_DO_INTEGRANTE_2",
    "TOKEN_DO_INTEGRANTE_3",
    "TOKEN_DO_INTEGRANTE_4"
]

REPO_NAME = "vuejs/core"  
# 🎯 VOLUME MASSIVO: 900 registros consomem a cota de forma segura em um único token
LIMITE_REGISTROS = 900

class TokenManager:
    """Gerencia o revezamento de tokens para contornar o Rate Limit."""
    def __init__(self, tokens):
        # Filtra strings vazias ou padrões não preenchidos
        self.tokens = [t for t in tokens if t and "TOKEN_DO" not in t and t != "MEU_TOKEN"]
        if not self.tokens:
            print("❌ ERRO CRÍTICO: Você precisa fornecer ao menos um Token válido na lista TOKENS_GRUPO!")
            sys.exit(1)
        self.index = 0
        print(f"🔄 Pool de credenciais ativado com {len(self.tokens)} token(s) disponível(is).")

    def get_github_instance(self):
        """Retorna uma instância do GitHub usando o próximo token da fila."""
        token = self.tokens[self.index]
        self.index = (self.index + 1) % len(self.tokens)
        return Github(token)

def lidar_com_rate_limit(exception):
    """Trata o erro 403 (Rate Limit ou Abuse Limit) aplicando um recuo de tempo."""
    if exception.status == 403:
        print("\n⚠️ Alerta de Rate/Abuse Limit do GitHub!")
        print("⏱️  Pausando a execução por 5 minutos para restaurar as quotas de requisições...")
        time.sleep(300)  # Interrupção sutil de 5 minutos antes de reatar o pipeline
        return True
    return False

def minerar_dados():
    print("═══════════════════════════════════════════════")
    print(" 🚀 Iniciando Mineração Distribuída:", REPO_NAME)
    print("═══════════════════════════════════════════════")
    
    token_manager = TokenManager(TOKENS_GRUPO)
    tempo_inicial = time.time()

    try:
        g = token_manager.get_github_instance()
        repo = g.get_repo(REPO_NAME)
    except Exception as e:
        print(f"❌ Erro ao conectar ao repositório: {e}")
        return

    try:
        with open('interacoes_reais.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['actor', 'target', 'type'])

            # ── 1. MINERANDO ISSUES ──
            print("\n📥 Coletando comentários e fechamentos de Issues...")
            issues = repo.get_issues(state='all')
            count_issues = 0
            
            for issue in issues:
                if count_issues >= LIMITE_REGISTROS:
                    break
                if issue.pull_request:
                    continue
                
                count_issues += 1
                sys.stdout.write(f"\rProcessando Issue #{issue.number} ({count_issues}/{LIMITE_REGISTROS})...")
                sys.stdout.flush()

                # 🛡️ THROTTLING ADAPTATIVO: 2 segundos de atraso para camuflar o tráfego contra Abuse Limits
                time.sleep(2.0)

                while True:
                    g_instance = token_manager.get_github_instance()
                    try:
                        issue_obj = g_instance.get_repo(REPO_NAME).get_issue(issue.number)
                        for comment in issue_obj.get_comments():
                            actor = comment.user.login
                            target = issue.user.login
                            if actor != target:  
                                writer.writerow([actor, target, 'COMMENT_ON_ISSUE_OR_PR'])
                        break  # Sai do loop infinito de tentativa se a requisição deu certo
                    except GithubException as e:
                        if not lidar_com_rate_limit(e):
                            break  # Se for outro tipo de erro que não o 403, ignora e pula a linha

                # Fechamento de Issue por outro usuário (Grafo 2)
                if issue.state == 'closed' and issue.closed_by:
                    actor = issue.closed_by.login
                    target = issue.user.login
                    if actor != target:
                        writer.writerow([actor, target, 'ISSUE_CLOSED_BY_OTHER'])

            # ── 2. MINERANDO PULL REQUESTS ──
            print("\n\n📥 Coletando revisões e merges de Pull Requests...")
            pulls = repo.get_pulls(state='all')
            count_prs = 0

            for pr in pulls:
                if count_prs >= LIMITE_REGISTROS:
                    break
                
                count_prs += 1
                sys.stdout.write(f"\rProcessando PR #{pr.number} ({count_prs}/{LIMITE_REGISTROS})...")
                sys.stdout.flush()

                # 🛡️ THROTTLING ADAPTATIVO: 2 segundos de atraso para proteção de IP
                time.sleep(2.0)

                while True:
                    g_instance = token_manager.get_github_instance()
                    try:
                        pr_obj = g_instance.get_repo(REPO_NAME).get_pull(pr.number)
                        
                        # Comentários no PR (Grafo 1)
                        for comment in pr_obj.get_issue_comments():
                            actor = comment.user.login
                            target = pr_obj.user.login
                            if actor != target:
                                writer.writerow([actor, target, 'COMMENT_ON_ISSUE_OR_PR'])

                        # Revisões/Aprovações (Grafo 3)
                        for review in pr_obj.get_reviews():
                            actor = review.user.login
                            target = pr_obj.user.login
                            if actor != target:
                                writer.writerow([actor, target, 'PR_REVIEW_OR_APPROVAL'])

                        # Merge de Pull Request (Grafo 3)
                        if pr_obj.merged and pr_obj.merged_by:
                            actor = pr_obj.merged_by.login
                            target = pr_obj.user.login
                            if actor != target:
                                writer.writerow([actor, target, 'PR_MERGE'])
                        break
                    except GithubException as e:
                        if not lidar_com_rate_limit(e):
                            break

        tempo_final = time.time()
        print("\n\n═══════════════════════════════════════════════")
        print(" 🎉 FIM: Arquivo 'interacoes_reais.csv' gerado de forma segura!")
        print(f" ⏱️  Tempo total de processamento: {tempo_final - tempo_inicial:.2f} segundos")
        print("═══════════════════════════════════════════════")

    except IOError as e:
        print(f"\n❌ Erro ao salvar o arquivo CSV: {e}")

if __name__ == "__main__":
    minerar_dados()
import os
import sys
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Adiciona o diretório atual ao PATH para que os módulos possam ser importados
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_loader import ConfigLoader
from github_api_client import GitHubApiClient
from data_processor import DataProcessor
from data_saver import DataSaver

class GitHubMiner:
    def __init__(self, config_path=os.path.join(os.path.dirname(__file__), '..', 'tokens.json'), output_dir=os.path.join(os.path.dirname(__file__), '..', 'output')):
        self.config_loader = ConfigLoader(config_path)
        self.tokens = self.config_loader.get_tokens()
        self.owner = self.config_loader.get_user_target()
        self.repo = self.config_loader.get_repo_target()
        self.api_client = GitHubApiClient(self.tokens)
        self.data_processor = DataProcessor()
        self.data_saver = DataSaver(output_dir)
        self.output_dir = output_dir

    def _get_all_pages(self, endpoint, params=None, since_date=None):
        all_data = []
        page = 1
        per_page = 100 # Max per page for GitHub API
        
        while True:
            current_params = {"per_page": per_page, "page": page}
            if params:
                current_params.update(params)
            
            print(f"Coletando {endpoint} - Página {page} com params: {current_params}")
            response = self.api_client.get_rest(endpoint, params=current_params)
            data = response.json()

            if not data:
                break

            # Filtrar por data se since_date for fornecido
            if since_date:
                filtered_data = []
                for item in data:
                    item_date_str = item.get("created_at") or item.get("submitted_at") or item.get("updated_at")
                    if item_date_str:
                        item_date = datetime.datetime.strptime(item_date_str, "%Y-%m-%dT%H:%M:%SZ")
                        if item_date >= since_date:
                            filtered_data.append(item)
                all_data.extend(filtered_data)
                # Se a última data na página for anterior à since_date, podemos parar
                if data and datetime.datetime.strptime(data[-1].get("created_at") or data[-1].get("submitted_at") or data[-1].get("updated_at"), "%Y-%m-%dT%H:%M:%SZ") < since_date:
                    break
            else:
                all_data.extend(data)

            if len(data) < per_page:
                break
            page += 1
        return all_data

    def _get_all_issues(self, since_date=None):
        print(f"Iniciando coleta de issues para {self.owner}/{self.repo}")
        issues = self._get_all_pages(f"/repos/{self.owner}/{self.repo}/issues", params={"state": "all"}, since_date=since_date)
        processed_issues = []
        for issue in issues:
            # PRs são issues com pull_request key
            if "pull_request" not in issue:
                processed_issues.append(issue)
        print(f"Total de issues coletadas: {len(processed_issues)}")
        return processed_issues

    def _get_all_pull_requests(self, since_date=None):
        print(f"Iniciando coleta de pull requests para {self.owner}/{self.repo}")
        prs = self._get_all_pages(f"/repos/{self.owner}/{self.repo}/pulls", params={"state": "all"}, since_date=since_date)
        print(f"Total de pull requests coletados: {len(prs)}")
        return prs

    def mine_issue_comments(self, issue, since_date=None):
        print(f"Coletando comentários para Issue #{issue["number"]}")
        comments = self._get_all_pages(f"/repos/{self.owner}/{self.repo}/issues/{issue["number"]}/comments", since_date=since_date)
        return [self.data_processor.process_issue_comment(c) for c in comments]

    def mine_issue_closures(self, issue, since_date=None):
        print(f"Coletando eventos de fechamento para Issue #{issue["number"]}")
        # GitHub API REST para eventos de issue não filtra por tipo de evento diretamente na URL
        # Precisamos coletar todos os eventos e filtrar localmente
        events = self._get_all_pages(f"/repos/{self.owner}/{self.repo}/issues/{issue["number"]}/events", since_date=since_date)
        closure_events = [e for e in events if e.get("event") == "closed"]
        return [self.data_processor.process_issue_closure(e) for e in closure_events]

    def mine_pull_request_comments(self, pr, since_date=None):
        print(f"Coletando comentários para Pull Request #{pr["number"]}")
        comments = self._get_all_pages(f"/repos/{self.owner}/{self.repo}/pulls/{pr["number"]}/comments", since_date=since_date)
        return [self.data_processor.process_pull_request_comment(c) for c in comments]

    def mine_pull_request_reviews(self, pr, since_date=None):
        print(f"Coletando revisões para Pull Request #{pr["number"]}")
        reviews = self._get_all_pages(f"/repos/{self.owner}/{self.repo}/pulls/{pr["number"]}/reviews", since_date=since_date)
        return [self.data_processor.process_pull_request_review(r) for r in reviews]

    def mine_pull_request_openings(self, pr, since_date=None):
        # Aberturas de PRs são os próprios objetos de PR
        # O filtro de data já é feito em _get_all_pull_requests
        return self.data_processor.process_pull_request_opening(pr)

    def mine_pull_request_merges(self, pr, since_date=None):
        # Merges de PRs são PRs que possuem merged_at
        # O filtro de data já é feito em _get_all_pull_requests
        return self.data_processor.process_pull_request_merge(pr)

    def mine_pull_request_approvals(self, review, since_date=None):
        # Aprovações são revisões com estado 'APPROVED'
        # O filtro de data já é feito em mine_pull_request_reviews
        return self.data_processor.process_pull_request_approval(review)

    def start_mining(self, time_window="all", num_threads=4):
        if not (1 <= num_threads <= 4):
            print("Número de threads deve ser entre 1 e 4. Usando 4 threads.")
            num_threads = 4
        
        # Limita o número de threads ao número de tokens disponíveis, se for menor que num_threads
        num_threads = min(num_threads, len(self.tokens))
        print(f"Iniciando mineração com {num_threads} threads.")

        since_date = None
        if time_window == "3-5_years":
            # Define a data de 3 anos atrás como padrão, pode ser ajustado para 5
            since_date = datetime.datetime.now() - datetime.timedelta(days=3*365)
            print(f"Coletando dados desde: {since_date.strftime('%Y-%m-%d')}")
        elif time_window == "all":
            print("Coletando todos os dados disponíveis.")
        else:
            print("Janela de tempo inválida. Usando 'all'.")

        all_issues = self._get_all_issues(since_date=since_date)
        all_prs = self._get_all_pull_requests(since_date=since_date)

        all_issue_comments = []
        all_issue_closures = []
        all_pr_comments = []
        all_pr_reviews = []
        all_pr_openings = []
        all_pr_merges = []
        all_pr_approvals = []

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []

            # Tarefas para issues
            for issue in all_issues:
                futures.append(executor.submit(self.mine_issue_comments, issue, since_date))
                futures.append(executor.submit(self.mine_issue_closures, issue, since_date))
            
            # Tarefas para PRs
            for pr in all_prs:
                futures.append(executor.submit(self.mine_pull_request_comments, pr, since_date))
                futures.append(executor.submit(self.mine_pull_request_reviews, pr, since_date))
                # Aberturas e merges são processados a partir do objeto PR completo
                futures.append(executor.submit(self.mine_pull_request_openings, pr, since_date))
                futures.append(executor.submit(self.mine_pull_request_merges, pr, since_date))

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if isinstance(result, list):
                        # Determinar o tipo de lista pelo conteúdo ou pelo nome da função
                        if result and "issue_url" in result[0] and "pull_request_url" not in result[0]:
                            all_issue_comments.extend(result)
                        elif result and "pull_request_url" in result[0]:
                            all_pr_comments.extend(result)
                        elif result and "state" in result[0] and "pull_request_url" in result[0]:
                            all_pr_reviews.extend(result)
                            for review in result:
                                approval = self.data_processor.process_pull_request_approval(review)
                                if approval:
                                    all_pr_approvals.append(approval)
                        elif result and "event" in result[0] and result[0].get("event") == "closed":
                            all_issue_closures.extend(result)
                    elif isinstance(result, dict):
                        if "merged_at" in result and result["merged_at"] is not None:
                            all_pr_merges.append(result)
                        elif "number" in result and "pull_request_url" in result.get("html_url", ""):
                            all_pr_openings.append(result)

                except Exception as exc:
                    print(f"Tarefa gerou uma exceção: {exc}")

        # Salvar os dados coletados
        self.data_saver.save_to_json(all_issue_comments, "issue_comments.json")
        self.data_saver.save_to_json(all_issue_closures, "issue_closures.json")
        self.data_saver.save_to_json(all_pr_comments, "pull_request_comments.json")
        self.data_saver.save_to_json(all_pr_reviews, "pull_request_reviews.json")
        self.data_saver.save_to_json(all_pr_approvals, "pull_request_approvals.json")
        self.data_saver.save_to_json(all_pr_merges, "pull_request_merges.json")
        self.data_saver.save_to_json(all_pr_openings, "pull_request_openings.json")

        print("Mineração concluída. Dados salvos em arquivos JSON.")

if __name__ == "__main__":
    miner = GitHubMiner()
    # Exemplo de uso: mineração de todos os dados com 4 threads
    miner.start_mining(time_window="all", num_threads=4)
    # Exemplo de uso: mineração dos últimos 3-5 anos com 2 threads
    # miner.start_mining(time_window="3-5_years", num_threads=2)

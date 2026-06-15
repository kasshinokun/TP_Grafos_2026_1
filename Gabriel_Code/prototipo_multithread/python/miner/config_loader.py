import json
import os

class ConfigLoader:
    def __init__(self, config_path='../tokens.json'):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        self._validate_config(config)
        return config

    def _validate_config(self, config):
        required_keys = ["GITHUB_TOKENS", "GITHUB_USER_TARGET", "GITHUB_REPO_TARGET"]
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Chave '{key}' ausente no arquivo de configuração.")

        if not isinstance(config["GITHUB_TOKENS"], list) or not config["GITHUB_TOKENS"]:
            raise ValueError("GITHUB_TOKENS deve ser uma lista não vazia de strings.")
        if not all(isinstance(token, str) for token in config["GITHUB_TOKENS"]):
            raise ValueError("Todos os tokens em GITHUB_TOKENS devem ser strings.")

        if not isinstance(config["GITHUB_USER_TARGET"], str) or not config["GITHUB_USER_TARGET"].strip():
            raise ValueError("GITHUB_USER_TARGET deve ser uma string não vazia.")
        if not isinstance(config["GITHUB_REPO_TARGET"], str) or not config["GITHUB_REPO_TARGET"].strip():
            raise ValueError("GITHUB_REPO_TARGET deve ser uma string não vazia.")

    def get_tokens(self):
        return self.config["GITHUB_TOKENS"]

    def get_user_target(self):
        return self.config["GITHUB_USER_TARGET"]

    def get_repo_target(self):
        return self.config["GITHUB_REPO_TARGET"]

if __name__ == '__main__':
    try:
        loader = ConfigLoader()
        print("Configuração carregada com sucesso:")
        print(f"Tokens: {loader.get_tokens()}")
        print(f"Usuário Alvo: {loader.get_user_target()}")
        print(f"Repositório Alvo: {loader.get_repo_target()}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Erro ao carregar configuração: {e}")

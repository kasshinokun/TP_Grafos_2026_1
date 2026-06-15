import json
import os

class Lapidador:
    @classmethod
    def initialize_work(cls):
        return cls()

    def lapidar(self):
        # 1. Procura o ficheiro gerado pelo nosso minerador
        input_file = os.path.join("data", "github_dados_minerados.json")
        output_file = os.path.join("data", "dados_lapidados.json")

        # Fallback: Caso tenhas renomeado o ficheiro antes
        if not os.path.exists(input_file):
            input_file = os.path.join("data", "closed_issues_part_01.json")
            if not os.path.exists(input_file):
                # Se não achar na pasta data, procura na raiz do projeto
                input_file = "github_dados_minerados.json"
                if not os.path.exists(input_file):
                    raise FileNotFoundError("Ficheiro JSON minerado não foi encontrado. Corre o main_miner.py primeiro.")

        # 2. Lê os dados brutos
        with open(input_file, 'r', encoding='utf-8') as f:
            dados_brutos = json.load(f)

        users_map = {}
        id_to_user = {}
        next_id = 0
        interacoes_dict = {}

        def get_or_create_user(username):
            nonlocal next_id
            if username not in users_map:
                users_map[username] = next_id
                id_to_user[next_id] = username
                next_id += 1
            return users_map[username]

        # 3. Processa as interações e soma os pesos
        for item in dados_brutos:
            # Proteção extra: garante que o item é de facto um dicionário (JSON object)
            if not isinstance(item, dict):
                continue

            # A CORREÇÃO ESTÁ AQUI:
            # Se o get devolver None (utilizador apagado), o "or {}" transforma num dicionário vazio.
            # Assim, o próximo .get('login') irá simplesmente devolver None sem rebentar o programa.
            user_data = item.get('user') or {}
            closed_by_data = item.get('closed_by') or {}

            opener = user_data.get('login')
            closer = closed_by_data.get('login')

            # Só cria aresta se quem fechou for diferente de quem abriu e se ambos existirem
            if opener and closer and opener != closer:
                u_id = get_or_create_user(closer) # Quem fecha
                v_id = get_or_create_user(opener) # De quem é a issue

                # Peso 3 para fecho de issue (conforme guião do professor)
                aresta = (closer, opener)
                if aresta in interacoes_dict:
                    interacoes_dict[aresta] += 3
                else:
                    interacoes_dict[aresta] = 3

        # 4. Formata a saída no padrão que a interface espera
        interactions_list = []
        for (fr, to), weight in interacoes_dict.items():
            interactions_list.append({"from": fr, "to": to, "weight": weight})

        dados_finais = {
            "metadata": {"total_users": next_id},
            "users": users_map,
            "interactions": interactions_list
        }

        # 5. Guarda o ficheiro lapidado final
        os.makedirs("data", exist_ok=True) 
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)

        return output_file
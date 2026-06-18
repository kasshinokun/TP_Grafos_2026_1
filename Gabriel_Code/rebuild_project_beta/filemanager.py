import json
import os
from os.path import join as concat      # junção de caminhos
from os.path import abspath as absf     # caminho absoluto
from os.path import dirname as dir_base # diretório pai
from os.path import isfile as eh_arquivo # encontra arquivo  

class FileSet:
    """
    Classe utilitária para manipulação de caminhos de arquivos e diretórios.
    Fornece métodos estáticos para obter diretórios, criar pastas e montar
    caminhos completos relativos ao arquivo atual.
    """

    @staticmethod
    def absoluto(file_name: str) -> str:
        """
        Retorna o diretório onde o arquivo informado está localizado.

        Parâmetros:
            file_name (str): Caminho para um arquivo (pode ser relativo).

        Retorna:
            str: Diretório contendo o arquivo, com caminho absoluto.
        """
        return dir_base(absf(file_name))

    @staticmethod
    def set_dir(name_diretorio: str, condicao: int = 1) -> str:
        """
        Constrói um caminho absoluto para um diretório dentro da pasta do
        arquivo atual (__file__) e, opcionalmente, cria o diretório.

        Parâmetros:
            name_diretorio (str): Nome do subdiretório a ser criado/retornado.
            condicao (int): Se igual a 1, o diretório é criado (com exist_ok=True).
                            Qualquer outro valor evita a criação.

        Retorna:
            str: Caminho absoluto completo do diretório.
        """
        if not name_diretorio: # Se for None
            print("configurando para a raiz (__file__)")
            FILE_DIR = FileSet.absoluto(__file__)
        else:
            # Obtém o diretório onde este arquivo está e concatena com o nome desejado
            FILE_DIR = concat(FileSet.absoluto(__file__), name_diretorio)
        
        # Cria o diretório se a condição for 1
        if condicao == 1:
            os.makedirs(FILE_DIR, exist_ok=True)

        return FILE_DIR

    @staticmethod
    def set_path_f(name_diretorio: str , file_name: str, condicao: int = 1) -> str:
        """
        Constrói o caminho completo de um arquivo dentro de um subdiretório
        da pasta do arquivo atual.

        Parâmetros:
            name_diretorio (str): Nome do subdiretório.
            file_name (str): Nome do arquivo.
            condicao (int): Repassado a set_dir; se igual a 1, cria o diretório.

        Retorna:
            str: Caminho absoluto completo para o arquivo.
        """
        if not name_diretorio:
            print("configurando para a raiz (__file__)")
            name_diretorio = FileSet.absoluto(__file__)

        # Obtém o caminho do diretório (criando‑o se condicao == 1) e junta com o nome do arquivo
        return concat(FileSet.set_dir(name_diretorio, condicao), file_name)

class JsonSet:
    @staticmethod
    def j_write(dirname: str = "json", data: dict = None, name_file: str = None):
        """
        Grava um dicionário em um arquivo JSON.
        :param dirname: Nome do diretório onde o arquivo será salvo (padrão: "json").
        :param data: Dicionário a ser serializado.
        :param name_file: Nome do arquivo (sem extensão ou com .json).
        """
        if data is None:
            data = {}
        if name_file is None:
            raise ValueError("O parâmetro 'name_file' é obrigatório.")

        # Garante que o nome do arquivo termine com .json
        if not name_file.endswith('.json'):
            name_file += '.json'

        # Constrói o caminho absoluto usando pathlib (mais moderno)
        file_path = FileSet.set_path_f(dirname,name_file)

        # Escreve o JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)  # indent para legibilidade

        return str(file_path)  # Retorna o caminho para referência

    @staticmethod
    def j_read(path_f: str):
        """
        Lê um arquivo JSON e retorna o dicionário.
        :param path_f: Caminho completo do arquivo JSON.
        :return: Dicionário com os dados lidos.
        """
        if not eh_arquivo(path_f):
            raise FileNotFoundError(f"Arquivo não encontrado: {path_f}")

        with open(path_f, 'r', encoding='utf-8') as f:
            data = json.load(f, ensure_ascii=False, indent=4)
        return data
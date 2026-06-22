"""Gerenciamento centralizado de caminhos de arquivos/diretórios do projeto.

Define o root_path do projeto (pasta onde este arquivo está localizado) e os
subdiretórios padronizados usados pela aplicação:

    root_path/gexf            -> arquivos .gexf (salvos e localizados aqui)
    root_path/qr_tokens       -> tokens em QR Code (.png)
    root_path/csv-provisorio  -> resultados (provisórios) da mineração em .csv

Baseado no utilitário equivalente do estágio beta (FileSet), adaptado para o
estágio v2b.
"""
import os
from os.path import join as concat
from os.path import abspath as absf
from os.path import dirname as dir_base


class FileSet:
    """Utilitário estático para resolver caminhos relativos ao root_path."""

    @staticmethod
    def absoluto(file_name: str) -> str:
        """Diretório onde o arquivo informado está localizado (caminho absoluto)."""
        return dir_base(absf(file_name))

    @staticmethod
    def set_dir(name_diretorio: str, condicao: int = 1) -> str:
        """Constrói (e opcionalmente cria) um caminho absoluto para um
        subdiretório dentro da pasta raiz do projeto (root_path)."""
        if not name_diretorio:
            FILE_DIR = FileSet.absoluto(__file__)
        else:
            FILE_DIR = concat(FileSet.absoluto(__file__), name_diretorio)

        if condicao == 1:
            os.makedirs(FILE_DIR, exist_ok=True)

        return FILE_DIR

    @staticmethod
    def set_path_f(name_diretorio: str, file_name: str, condicao: int = 1) -> str:
        """Caminho completo de um arquivo dentro de um subdiretório do root_path."""
        if not name_diretorio:
            name_diretorio = FileSet.absoluto(__file__)
        return concat(FileSet.set_dir(name_diretorio, condicao), file_name)


# Raiz do projeto (pasta onde este arquivo está localizado)
ROOT_PATH = FileSet.absoluto(__file__)

# Diretórios padronizados (criados automaticamente se não existirem)
PATH_D_GEXF = FileSet.set_dir("gexf")
PATH_D_QR = FileSet.set_dir("qr_tokens")
PATH_D_CSV = FileSet.set_dir("csv")

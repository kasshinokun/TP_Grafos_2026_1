# ./cli/cli_interpreter.py
"""Interpretador do CLI textual: converte uma linha de texto digitada
pelo usuário em uma intenção de comando "crua" — um par
`(token_de_comando: str, kwargs: dict)`, ainda sem validação contra o
`EventType` (isso é responsabilidade de `cli_cmd_validator.py`).

Gramática suportada (deliberadamente simples — isto não é um shell
completo, é um campo de comando para acionar a EDA via texto):

    comando [chave=valor ...]

Exemplos:
    bfs source=0 target=12
    load filename=graph1.gexf
    test category=algorithms run="Todos da categoria"

Regras de parsing:
- O primeiro token (até o primeiro espaço) é o nome do comando.
- Os tokens seguintes no formato `chave=valor` se tornam entradas do
  dict de argumentos.
- Valores entre aspas (simples ou duplas) podem conter espaços:
  `run="Todos da categoria"`.
- Valores puramente numéricos são convertidos para `int`/`float`
  automaticamente (conveniência para `source=0`, sem o usuário
  precisar saber que o payload "deveria" ser int) — texto que não
  parsear como número permanece string.
- Tokens sem `=` são ignorados silenciosamente por este módulo (a
  validação de "argumentos faltando ou em formato errado" é
  responsabilidade do validador, não do interpretador — este módulo só
  faz parsing sintático, nunca decide se o resultado "faz sentido").
"""
import re
import shlex
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ParsedCommand:
    """Resultado bruto do parsing — ainda não é um Event válido, só a
    intenção tal como o texto a descreve."""
    raw_text: str
    command_token: str
    kwargs: Dict[str, Any] = field(default_factory=dict)


class ParseError(Exception):
    """Texto de entrada mal formado a ponto de não ser possível nem
    tokenizar (ex.: aspas não fechadas) — diferente de um comando
    desconhecido ou argumento inválido, que são responsabilidade do
    validador."""


_NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")


class CliInterpreter:
    """Sem estado — pode ser reutilizada livremente, inclusive de
    múltiplas threads (não guarda nada entre chamadas)."""

    def parse(self, raw_text: str) -> ParsedCommand:
        text = raw_text.strip()
        if not text:
            raise ParseError("Linha de comando vazia.")

        try:
            tokens = shlex.split(text)
        except ValueError as ex:
            # shlex levanta ValueError para aspas não fechadas etc.
            raise ParseError(f"Comando mal formado: {ex}") from ex

        if not tokens:
            raise ParseError("Linha de comando vazia.")

        command_token = tokens[0]
        kwargs: Dict[str, Any] = {}
        for token in tokens[1:]:
            if "=" not in token:
                # Ignorado deliberadamente — ver docstring do módulo.
                continue
            key, _, raw_value = token.partition("=")
            kwargs[key] = self._coerce(raw_value)

        return ParsedCommand(raw_text=raw_text, command_token=command_token, kwargs=kwargs)

    @staticmethod
    def _coerce(raw_value: str) -> Any:
        """Converte o valor textual para int/float quando possível;
        caso contrário devolve a string como está (já sem as aspas,
        que o `shlex.split` já removeu)."""
        if _NUMBER_RE.match(raw_value):
            return int(raw_value) if "." not in raw_value else float(raw_value)
        return raw_value

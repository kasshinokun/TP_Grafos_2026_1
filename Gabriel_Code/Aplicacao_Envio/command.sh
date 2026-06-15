#!/bin/bash


# Configurações iniciais (sem espaços!)
PYTHON_LINUX="python3"
PYTHON_WINDOWS="python"
VENV_DIR="./venv"

# Detecta o sistema operacional via uname -s
OS=$(uname -s)

if [[ "$OS" == "Linux" ]]; then
    echo "Sistema Linux detectado"
    PYTHON_SET="$PYTHON_LINUX"
    OS_RUNTIME="LINUX"
    ACTIVATE_SCRIPT="$VENV_DIR/bin/activate"
elif [[ "$OS" == MINGW* ]] || [[ "$OS" == CYGWIN* ]] || [[ "$OS" == MSYS* ]]; then
    echo "Sistema Windows (Git Bash/Cygwin/MSYS2) detectado"
    PYTHON_SET="$PYTHON_WINDOWS"
    OS_RUNTIME="WINDOWS"
    ACTIVATE_SCRIPT="$VENV_DIR/Scripts/activate"
else
    echo "Sistema operacional não suportado: $OS"
    exit 1
fi

echo "$OS_RUNTIME"

# Cria o ambiente virtual se necessário
if [ -f "$ACTIVATE_SCRIPT" ]; then
    echo "Ambiente virtual já existe em $VENV_DIR. Prosseguindo..."
else
    echo "Criando ambiente virtual em $VENV_DIR usando $PYTHON_SET..."
    "$PYTHON_SET" -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "Falha ao criar o ambiente virtual. Verifique se $PYTHON_SET está instalado e o módulo venv disponível."
        exit 1
    fi
fi


# ======================== PROCESSO DEFAULT EM AMBOS OS SISTEMAS ========================
# Ativa o ambiente (necessário que o script seja executado com 'source')
source "$ACTIVATE_SCRIPT"

# Atualiza o pip
pip install --upgrade pip

# adiciona pacotes
pip install -r requirements.txt

# roda o cifrador de tokens para qr code
"$PYTHON_SET" cypher_token_rebuild.py

# Configura o texto do prompt do menu
PS3="Escolha uma opção (1-4): "

# Definição das variáveis (sem espaços ao redor do '=')
MODO_CONSOLE="Console TP"
EXECUTE_CONSOLE="$PYTHON_SET orchestrator_hibrido_alpha0f.py"

MODO_CTK="CTK GUI TP"
EXECUTE_CTK="$PYTHON_SET gui_ctk.py"

MODO_PYQT6="CTK PYQT6 TP"
EXECUTE_PYQT6="$PYTHON_SET gui_pyqt6.py"

# Lista de opções e ações
select opcao in "$MODO_CONSOLE" "$MODO_CTK" "$MODO_PYQT6" "Sair"; do
    case $REPLY in
        1)
            echo "Iniciando: $MODO_CONSOLE..."
            $EXECUTE_CONSOLE
            ;;
        2)
            echo "Iniciando: $MODO_CTK..."
            $EXECUTE_CTK
            ;;
        3)
            echo "Iniciando: $MODO_PYQT6..."
            $EXECUTE_PYQT6
            ;;
        4)
            echo "Saindo do programa. Até logo!"
            break
            ;;
        *)
            echo "Opção inválida! Escolha um número de 1 a 4."
            ;;
    esac
done


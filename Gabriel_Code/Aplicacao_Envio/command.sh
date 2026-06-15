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
python3 cypher_token_rebuild.py

# inicia a aplicação do trabalho prático
python3 orchestrator_hibrido_alpha0b.py

#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# build.sh — compila e executa a ferramenta de análise de grafos
# Uso:
#   ./build.sh          → compila + testes
#   ./build.sh run      → compila + CLI interativo
#   ./build.sh tests    → compila + apenas testes
# ─────────────────────────────────────────────────────────────
set -e

SRC_DIR="src/main/java"
OUT_DIR="out"
MAIN_CLASS="br.pucminas.grafo.Main"
TEST_CLASS="br.pucminas.grafo.TestSuite"

echo "═══════════════════════════════════════════════"
echo "  Compilando fontes Java..."
echo "═══════════════════════════════════════════════"
mkdir -p "$OUT_DIR"
find "$SRC_DIR" -name "*.java" | xargs javac -d "$OUT_DIR" -source 17 -target 17

echo "Compilação concluída com sucesso!"

MODE="${1:-tests}"

if [[ "$MODE" == "run" ]]; then
    echo ""
    echo "═══════════════════════════════════════════════"
    echo "  Iniciando CLI interativo..."
    echo "═══════════════════════════════════════════════"
    java -cp "$OUT_DIR" "$MAIN_CLASS"
elif [[ "$MODE" == "tests" || "$MODE" == "" ]]; then
    echo ""
    echo "═══════════════════════════════════════════════"
    echo "  Executando suite de testes..."
    echo "═══════════════════════════════════════════════"
    java -cp "$OUT_DIR" "$TEST_CLASS"
fi

"""Tela Sobre o projeto."""
import customtkinter as ctk
from typing import Optional, Callable
from gui.screen_base import BaseScreen
import qrcode
from customtkinter import CTkImage
from PIL import Image

REPO_URL = "https://github.com/kasshinokun/TP_Grafos_2026_1"

class AboutScreen(BaseScreen):
    """Informações sobre o projeto, tecnologias e autores."""

    def __init__(self, master,
                 on_back: Optional[Callable] = None,
                 **kwargs):
        super().__init__(
            master,
            title="ℹ️ Sobre o Projeto",
            subtitle="Teoria de Grafos e Computabilidade — PUC-MG 2026/1",
            on_back=on_back,
            **kwargs
        )

    def _build_content(self):
        # Scrollable frame principal
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=40, pady=20)

        # Tabview com 2 abas
        tabview = ctk.CTkTabview(scroll)
        tabview.pack(fill="both", expand=True)

        # Aba 1: Autores
        tab_autores = tabview.add("👥 Autores")
        # Aba 2: Sobre o projeto (com sections)
        tab_sobre = tabview.add("📋 Sobre o Projeto")

        # ========== ABA AUTORES ==========
        autores_frame = ctk.CTkFrame(tab_autores, fg_color="transparent")
        autores_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Coluna esquerda: informações
        left_col = ctk.CTkFrame(autores_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 20))

        info_texts = [
            "🏫 Projeto Trabalho Prático de Teoria de Grafos",
            "e Computabilidade",
            "🏛️ Faculdade: Pontifícia Universidade Católica de Minas Gerais - PUC MINAS",
            "📍 Campus: Coração Eucarístico",
            "👥 Alunos:",
            "   • Daniel Lucas Soares Madureira",
            "   • Gabriel da Silva Cassino",
            "   • Paulo Henrique Rodrigues Neves",
            "   • Vinicius Cezar Pereira Menezes",
            "👨‍🏫 Professor: Prof. Leonardo Vilela Cardoso",
            "📚 Turma: 31.32.101",
            "🎓 Graduação: Engenharia de Computação",
            "📅 Semestre: 2026/1",
        ]
        for linha in info_texts:
            ctk.CTkLabel(left_col, text=linha, font=("Arial", 12),
                         justify="left", anchor="w").pack(anchor="w", pady=1)

        # Coluna direita: QR Code + URL
        right_col = ctk.CTkFrame(autores_frame, fg_color="transparent", width=200)
        right_col.pack(side="right", fill="y", padx=(20, 0))
        right_col.pack_propagate(False)

        try:
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(REPO_URL)
            qr.make(fit=True)
            img_pil = qr.make_image(fill_color="black", back_color="white")
            img_pil = img_pil.resize((160, 160), Image.LANCZOS)
            ctk_img = CTkImage(light_image=img_pil, dark_image=img_pil, size=(160, 160))
            lbl_qr = ctk.CTkLabel(right_col, image=ctk_img, text="")
            lbl_qr.image = ctk_img
            lbl_qr.pack(pady=(0, 10))
        except Exception as e:
            ctk.CTkLabel(right_col, text=f"Erro ao gerar QR:\n{e}", text_color="red").pack(pady=10)

        ctk.CTkLabel(right_col, text=REPO_URL, wraplength=160,
                     font=("Arial", 10), justify="center").pack()

        # ========== ABA SOBRE O PROJETO (com sections) ==========
        # Frame interno para organizar as seções com espaçamento
        sobre_frame = ctk.CTkFrame(tab_sobre, fg_color="transparent")
        sobre_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Função auxiliar para criar uma seção com título e conteúdo
        def add_section(title, content_lines, is_list=False):
            # Título
            ctk.CTkLabel(sobre_frame, text=title, font=("Arial", 14, "bold"),
                         anchor="w").pack(anchor="w", pady=(15, 5))
            # Separador
            ctk.CTkFrame(sobre_frame, height=2, fg_color="#333355").pack(fill="x", pady=(0, 10))
            # Conteúdo
            if is_list:
                for line in content_lines:
                    ctk.CTkLabel(sobre_frame, text=line, font=("Arial", 12),
                                 anchor="w", justify="left").pack(anchor="w", pady=1)
            else:
                # Texto contínuo (wraplength)
                ctk.CTkLabel(sobre_frame, text=content_lines, wraplength=800,
                             font=("Arial", 12), justify="left").pack(anchor="w", pady=5)

        # Seção Descrição
        add_section(
            "📌 Descrição",
            "Sistema de análise de redes complexas implementado inteiramente em Python nativo "
            "(sem NetworkX). O projeto carrega grafos em formato GEXF, mina repositórios do GitHub "
            "e calcula 11 métricas de redes complexas."
        )

        # Seção Arquitetura
        add_section(
            "🏗️ Arquitetura",
            [
                "• grafo/graph/       — Estruturas de dados (AbstractGraph, AdjacencyListGraph, AdjacencyMatrixGraph)",
                "• grafo/networkx_pure/ — Algoritmos nativos (centrality, structure, communities) + Adapter",
                "• grafo/utils/       — Parser GEXF nativo (xml.etree.ElementTree)",
                "• miner/             — Mineradores multithread (CommonMiner, HybridMiner) + Checkpoint + RateLimiter",
                "• gui/               — Interface CustomTkinter com navegação por telas",
                "• viz/               — Layout force-directed (Fruchterman-Reingold) + Renderer SVG",
                "• tests/             — 43 testes unitários (pytest)",
            ],
            is_list=True
        )

        # Seção Métricas
        metricas_groups = [
            ("Centralidade", [
                "1. Degree Centrality (in/out, normalizada)",
                "2. Betweenness Centrality (Algoritmo de Brandes)",
                "3. Closeness Centrality (Wasserman-Faust)",
                "4. PageRank (iteração de potência, damping=0.85)",
            ]),
            ("Estrutura", [
                "5. Densidade da rede",
                "6. Coeficiente de Aglomeração (clustering)",
                "7. Assortatividade (correlação de Pearson)",
                "8. Diâmetro e Caminho Médio",
            ]),
            ("Comunidade", [
                "9.  Label Propagation Communities",
                "10. Modularidade Q (Newman)",
                "11. Bridging Ties",
            ]),
        ]
        # Título da seção Métricas
        ctk.CTkLabel(sobre_frame, text="📐 11 Métricas Implementadas", font=("Arial", 14, "bold"),
                     anchor="w").pack(anchor="w", pady=(15, 5))
        ctk.CTkFrame(sobre_frame, height=2, fg_color="#333355").pack(fill="x", pady=(0, 10))
        for cat, items in metricas_groups:
            ctk.CTkLabel(sobre_frame, text=cat, font=("Arial", 13, "bold"),
                         anchor="w").pack(anchor="w", padx=20, pady=(5, 0))
            for item in items:
                ctk.CTkLabel(sobre_frame, text=f"  {item}", font=("Arial", 12),
                             anchor="w").pack(anchor="w", padx=40, pady=1)

        # Seção Tecnologias
        add_section(
            "⚙️ Tecnologias",
            "Python 3.11+  ·  CustomTkinter 5.x  ·  xml.etree.ElementTree  ·  "
            "threading / concurrent.futures  ·  pytest  ·  requests"
        )

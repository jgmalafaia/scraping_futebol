"""Funções utilitárias compartilhadas entre os scrapers."""

import os
import json
from datetime import datetime

import pandas as pd

from .config import OUTPUT_DIR


def garantir_diretorio_saida() -> str:
    """Cria o diretório de saída se não existir e retorna o caminho."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return OUTPUT_DIR


def salvar_csv(dados: list[dict], nome_arquivo: str) -> str:
    """Salva lista de dicionários como CSV e retorna o caminho do arquivo."""
    diretorio = garantir_diretorio_saida()
    caminho = os.path.join(diretorio, nome_arquivo)
    df = pd.DataFrame(dados)
    df.to_csv(caminho, index=False, encoding="utf-8-sig")
    print(f"  -> Arquivo salvo: {caminho}")
    return caminho


def salvar_json(dados: list[dict] | dict, nome_arquivo: str) -> str:
    """Salva dados como JSON e retorna o caminho do arquivo."""
    diretorio = garantir_diretorio_saida()
    caminho = os.path.join(diretorio, nome_arquivo)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"  -> Arquivo salvo: {caminho}")
    return caminho


def timestamp_arquivo() -> str:
    """Retorna string com timestamp para usar em nomes de arquivo."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

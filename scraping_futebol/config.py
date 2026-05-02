"""Configurações e constantes para os scrapers."""

import os

# Diretório de saída para os arquivos gerados
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dados_futebol")

# Headers para simular navegador nas requisições
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Timeout padrão para requisições HTTP (segundos)
REQUEST_TIMEOUT = 15

# --- ESPN API ---
ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer"

# Ligas disponíveis (ESPN slug → nome)
LIGAS = {
    "brasileirao": {"slug": "bra.1", "nome": "Brasileirão Série A"},
    "brasileirao-b": {"slug": "bra.2", "nome": "Brasileirão Série B"},
    "premier-league": {"slug": "eng.1", "nome": "Premier League"},
    "la-liga": {"slug": "esp.1", "nome": "La Liga"},
    "serie-a": {"slug": "ita.1", "nome": "Serie A (Itália)"},
    "bundesliga": {"slug": "ger.1", "nome": "Bundesliga"},
    "ligue-1": {"slug": "fra.1", "nome": "Ligue 1"},
    "champions-league": {"slug": "uefa.champions", "nome": "Champions League"},
    "libertadores": {"slug": "conmebol.libertadores", "nome": "Copa Libertadores"},
    "copa-do-brasil": {"slug": "bra.copa_do_brasil", "nome": "Copa do Brasil"},
    "mls": {"slug": "usa.1", "nome": "MLS"},
    "liga-portugal": {"slug": "por.1", "nome": "Liga Portugal"},
    "eredivisie": {"slug": "ned.1", "nome": "Eredivisie"},
}

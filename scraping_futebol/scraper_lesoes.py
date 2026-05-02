"""
Scraper de Lesões de Futebol.

Fontes de dados:
  - ESPN API: lista de lesões por liga (gratuita)
  - Transfermarkt: histórico detalhado de lesões (scraping HTML)

Uso:
  from scraping_futebol.scraper_lesoes import ScraperLesoes

  scraper = ScraperLesoes()
  lesoes = scraper.buscar_lesoes_por_liga("premier-league")
  lesoes = scraper.buscar_lesoes_transfermarkt("flamengo", 614)
"""

import requests
from bs4 import BeautifulSoup

from .config import ESPN_BASE_URL, HEADERS, LIGAS, REQUEST_TIMEOUT
from .utils import salvar_csv, salvar_json, timestamp_arquivo


class ScraperLesoes:
    """Raspa informações de lesões de jogadores de futebol."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str, headers: dict | None = None) -> dict | None:
        """Faz requisição GET e retorna JSON ou None."""
        try:
            h = {**self.session.headers, **(headers or {})}
            resp = self.session.get(url, headers=h, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"  [ERRO] Falha na requisição: {url}")
            print(f"         {e}")
            return None

    def _get_html(self, url: str, headers: dict | None = None) -> str | None:
        """Faz requisição GET e retorna HTML ou None."""
        try:
            h = {**self.session.headers, **(headers or {})}
            h["Accept"] = "text/html,application/xhtml+xml"
            resp = self.session.get(url, headers=h, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            print(f"  [ERRO] Falha na requisição HTML: {url}")
            print(f"         {e}")
            return None

    def _resolver_liga(self, liga: str) -> dict | None:
        """Retorna info da liga ou None se não encontrada."""
        info = LIGAS.get(liga)
        if not info:
            print(f"  Liga '{liga}' não encontrada. Opções: {list(LIGAS.keys())}")
        return info

    # -----------------------------------------------------------------
    # ESPN – lesões por liga
    # -----------------------------------------------------------------

    def buscar_lesoes_por_liga(
        self, liga: str = "brasileirao", salvar: bool = True
    ) -> list[dict]:
        """
        Busca lesões de todos os times de uma liga via ESPN.

        Args:
            liga: Chave da liga (ex: 'brasileirao', 'premier-league').
            salvar: Se True, salva resultados em CSV/JSON.

        Returns:
            Lista de dicionários com informações dos jogadores lesionados.
        """
        info = self._resolver_liga(liga)
        if not info:
            return []

        print(f"\n=== Buscando lesões - {info['nome']} ===\n")

        url = f"{ESPN_BASE_URL}/{info['slug']}/injuries"
        resultado = self._get(url)

        if not resultado:
            return []

        todas_lesoes = []
        injuries_data = resultado.get("injuries", [])

        if not injuries_data:
            print(f"  Nenhuma lesão reportada para {info['nome']}.")
            print("  (Algumas ligas podem não ter dados de lesão disponíveis na ESPN)")
            return []

        for team_data in injuries_data:
            time_nome = team_data.get("team", {}).get("displayName", "")
            time_id = team_data.get("team", {}).get("id", "")

            for injury in team_data.get("injuries", []):
                atleta = injury.get("athlete", {})
                lesao = {
                    "liga": info["nome"],
                    "time": time_nome,
                    "time_id": time_id,
                    "jogador": atleta.get("displayName", ""),
                    "nome_curto": atleta.get("shortName", ""),
                    "posicao": atleta.get("position", {}).get("abbreviation", ""),
                    "status": injury.get("status", ""),
                    "tipo_lesao": injury.get("type", {}).get("description", ""),
                    "detalhe": injury.get("details", {}).get("detail", ""),
                    "data_lesao": injury.get("date", ""),
                }
                todas_lesoes.append(lesao)

        print(f"  Total: {len(todas_lesoes)} jogador(es) lesionado(s) na {info['nome']}")

        if salvar and todas_lesoes:
            ts = timestamp_arquivo()
            salvar_csv(todas_lesoes, f"lesoes_{liga}_{ts}.csv")
            salvar_json(todas_lesoes, f"lesoes_{liga}_{ts}.json")

        return todas_lesoes

    # -----------------------------------------------------------------
    # ESPN – lesões de um time específico
    # -----------------------------------------------------------------

    def buscar_lesoes_por_time(
        self, liga: str, time_id: str, salvar: bool = True
    ) -> list[dict]:
        """
        Busca lesões de um time específico.

        Args:
            liga: Chave da liga.
            time_id: ID do time na ESPN.
            salvar: Se True, salva resultados.

        Returns:
            Lista de lesões do time.
        """
        todas = self.buscar_lesoes_por_liga(liga, salvar=False)
        lesoes_time = [l for l in todas if str(l["time_id"]) == str(time_id)]

        if salvar and lesoes_time:
            ts = timestamp_arquivo()
            salvar_csv(lesoes_time, f"lesoes_time_{time_id}_{ts}.csv")
            salvar_json(lesoes_time, f"lesoes_time_{time_id}_{ts}.json")

        return lesoes_time

    # -----------------------------------------------------------------
    # ESPN – listar times de uma liga
    # -----------------------------------------------------------------

    def buscar_times(self, liga: str = "brasileirao") -> list[dict]:
        """
        Lista todos os times de uma liga.

        Args:
            liga: Chave da liga.

        Returns:
            Lista de times com id e nome.
        """
        info = self._resolver_liga(liga)
        if not info:
            return []

        url = f"{ESPN_BASE_URL}/{info['slug']}/teams"
        resultado = self._get(url)

        if not resultado:
            return []

        times = []
        sports = resultado.get("sports", [{}])
        leagues = sports[0].get("leagues", [{}]) if sports else [{}]
        teams_list = leagues[0].get("teams", []) if leagues else []

        for t in teams_list:
            team = t.get("team", {})
            times.append(
                {
                    "id": team.get("id", ""),
                    "nome": team.get("displayName", ""),
                    "abreviacao": team.get("abbreviation", ""),
                }
            )

        print(f"  {info['nome']}: {len(times)} time(s)")
        return times

    # -----------------------------------------------------------------
    # Transfermarkt – lesões detalhadas (scraping HTML)
    # -----------------------------------------------------------------

    def buscar_lesoes_transfermarkt(
        self, time_slug: str, time_id_tm: int, salvar: bool = True
    ) -> list[dict]:
        """
        Busca jogadores lesionados no Transfermarkt (via página de elenco).

        Args:
            time_slug: Slug do time (ex: 'flamengo', 'manchester-city').
            time_id_tm: ID do time no Transfermarkt (ex: 614).
            salvar: Se True, salva resultados.

        Returns:
            Lista de lesões com detalhes.

        Exemplos de times populares:
            flamengo (614), palmeiras (1023), corinthians (199),
            real-madrid (418), barcelona (131), manchester-city (281)
        """
        url = (
            f"https://www.transfermarkt.com/{time_slug}"
            f"/kader/verein/{time_id_tm}"
        )
        headers_tm = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "pt-BR,pt;q=0.9",
            "Referer": "https://www.transfermarkt.com/",
        }

        print(f"\n=== Transfermarkt: {time_slug} (ID: {time_id_tm}) ===\n")

        html = self._get_html(url, headers=headers_tm)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        tabela = soup.find("table", class_="items")

        if not tabela:
            print(f"  Nenhuma tabela encontrada para {time_slug}.")
            print("  (Transfermarkt pode bloquear scraping em alguns casos)")
            return []

        lesoes = []
        tbody = tabela.find("tbody")
        if not tbody:
            return lesoes

        for row in tbody.find_all("tr", recursive=False):
            injury_span = row.find("span", class_="verletzt-table")
            if not injury_span:
                continue

            player_name = ""
            position = ""

            for link in row.find_all("a"):
                href = link.get("href", "")
                if "/profil/spieler/" in href:
                    text = link.get_text(strip=True)
                    if text:
                        player_name = text
                        break

            pos_cell = row.find("td", class_="posrela")
            if pos_cell:
                pos_tds = pos_cell.find_all("td")
                for td in pos_tds:
                    text = td.get_text(strip=True)
                    if text and text != player_name:
                        position = text

            injury_text = injury_span.get("title", "")
            lesao_parts = injury_text.split(" - ")
            tipo_lesao = lesao_parts[0] if lesao_parts else injury_text
            previsao = lesao_parts[1] if len(lesao_parts) > 1 else ""

            lesoes.append(
                {
                    "jogador": player_name,
                    "time": time_slug,
                    "posicao": position,
                    "tipo_lesao": tipo_lesao,
                    "previsao_retorno": previsao,
                    "detalhe": injury_text,
                }
            )

        print(f"  Encontrados: {len(lesoes)} jogador(es) lesionado(s)")

        if salvar and lesoes:
            ts = timestamp_arquivo()
            salvar_csv(lesoes, f"lesoes_tm_{time_slug}_{ts}.csv")
            salvar_json(lesoes, f"lesoes_tm_{time_slug}_{ts}.json")

        return lesoes

    # -----------------------------------------------------------------
    # Buscar lesões de múltiplas ligas
    # -----------------------------------------------------------------

    def buscar_lesoes_multiplas_ligas(
        self, ligas: list[str] | None = None, salvar: bool = True
    ) -> list[dict]:
        """
        Busca lesões de múltiplas ligas de uma vez.

        Args:
            ligas: Lista de chaves de ligas. Se None, busca das 5 principais.
            salvar: Se True, salva resultados.

        Returns:
            Lista consolidada de todas as lesões.
        """
        if ligas is None:
            ligas = ["brasileirao", "premier-league", "la-liga", "serie-a", "bundesliga"]

        todas_lesoes = []
        for liga in ligas:
            resultado = self.buscar_lesoes_por_liga(liga, salvar=False)
            todas_lesoes.extend(resultado)

        if salvar and todas_lesoes:
            ts = timestamp_arquivo()
            salvar_csv(todas_lesoes, f"lesoes_multiplas_{ts}.csv")
            salvar_json(todas_lesoes, f"lesoes_multiplas_{ts}.json")

        print(f"\n  Total geral: {len(todas_lesoes)} lesão(ões) em {len(ligas)} liga(s)")
        return todas_lesoes

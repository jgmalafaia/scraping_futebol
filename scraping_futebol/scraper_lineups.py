"""
Scraper de Lineups (Escalações) de Futebol.

Fonte de dados: ESPN API (gratuita, sem autenticação).

Uso:
  from scraping_futebol.scraper_lineups import ScraperLineups

  scraper = ScraperLineups()
  escalacoes = scraper.buscar_lineups_por_data(liga="brasileirao")
  escalacao = scraper.buscar_lineup_por_evento("brasileirao", evento_id="12345")
"""

from datetime import datetime, timedelta

import requests

from .config import ESPN_BASE_URL, HEADERS, LIGAS, REQUEST_TIMEOUT
from .utils import salvar_csv, salvar_json, timestamp_arquivo


class ScraperLineups:
    """Raspa escalações de partidas de futebol via ESPN API."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str) -> dict | None:
        """Faz requisição GET e retorna JSON ou None em caso de erro."""
        try:
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"  [ERRO] Falha na requisição: {url}")
            print(f"         {e}")
            return None

    def _resolver_liga(self, liga: str) -> dict | None:
        """Retorna info da liga ou None se não encontrada."""
        info = LIGAS.get(liga)
        if not info:
            print(f"  Liga '{liga}' não encontrada. Opções: {list(LIGAS.keys())}")
        return info

    # -----------------------------------------------------------------
    # Buscar eventos (partidas) por data
    # -----------------------------------------------------------------

    def buscar_eventos_por_data(
        self, liga: str = "brasileirao", data: str | None = None
    ) -> list[dict]:
        """
        Busca partidas agendadas/realizadas para uma data.

        Args:
            liga: Chave da liga (ex: 'brasileirao', 'premier-league').
            data: Data 'YYYY-MM-DD'. Se None, usa hoje.

        Returns:
            Lista de dicionários com informações das partidas.
        """
        info = self._resolver_liga(liga)
        if not info:
            return []

        data_fmt = data or datetime.now().strftime("%Y-%m-%d")
        data_param = data_fmt.replace("-", "")

        url = f"{ESPN_BASE_URL}/{info['slug']}/scoreboard?dates={data_param}"
        resultado = self._get(url)

        if not resultado or "events" not in resultado:
            print(f"  Nenhum evento encontrado para {data_fmt} ({info['nome']}).")
            return []

        partidas = []
        for evento in resultado["events"]:
            comp = evento.get("competitions", [{}])[0]
            competidores = comp.get("competitors", [])

            time_casa = time_fora = {}
            for c in competidores:
                if c.get("homeAway") == "home":
                    time_casa = c
                else:
                    time_fora = c

            status = comp.get("status", {}).get("type", {})

            partida = {
                "evento_id": evento.get("id", ""),
                "data": data_fmt,
                "liga": info["nome"],
                "time_casa": time_casa.get("team", {}).get("displayName", ""),
                "time_casa_id": time_casa.get("team", {}).get("id", ""),
                "time_fora": time_fora.get("team", {}).get("displayName", ""),
                "time_fora_id": time_fora.get("team", {}).get("id", ""),
                "placar_casa": time_casa.get("score", ""),
                "placar_fora": time_fora.get("score", ""),
                "status": status.get("description", ""),
                "status_code": status.get("name", ""),
                "concluido": status.get("completed", False),
                "local": comp.get("venue", {}).get("fullName", ""),
            }
            partidas.append(partida)

        print(f"  {info['nome']} ({data_fmt}): {len(partidas)} jogo(s) encontrado(s)")
        return partidas

    # -----------------------------------------------------------------
    # Buscar lineup de um evento específico
    # -----------------------------------------------------------------

    def buscar_lineup_por_evento(
        self, liga: str, evento_id: str
    ) -> dict | None:
        """
        Busca a escalação de uma partida via ESPN summary.

        Args:
            liga: Chave da liga.
            evento_id: ID do evento na ESPN.

        Returns:
            Dicionário com escalações e formações, ou None.
        """
        info = self._resolver_liga(liga)
        if not info:
            return None

        url = f"{ESPN_BASE_URL}/{info['slug']}/summary?event={evento_id}"
        resultado = self._get(url)

        if not resultado:
            return None

        rosters = resultado.get("rosters", [])
        if not rosters:
            print(f"  Escalação não disponível para evento {evento_id}.")
            return None

        escalacao: dict = {"evento_id": evento_id, "casa": {}, "fora": {}}

        for roster in rosters:
            lado = "casa" if roster.get("homeAway") == "home" else "fora"
            time_nome = roster.get("team", {}).get("displayName", "")
            formacao = roster.get("formation", "")

            jogadores = []
            for entry in roster.get("roster", []):
                atleta = entry.get("athlete", {})
                posicao = entry.get("position", {})
                stats = entry.get("stats", [])

                stats_dict = {}
                for s in stats:
                    stats_dict[s.get("name", "")] = s.get("displayValue", "")

                jogadores.append(
                    {
                        "nome": atleta.get("displayName", ""),
                        "nome_curto": atleta.get("shortName", ""),
                        "numero_camisa": entry.get("jersey", ""),
                        "posicao": posicao.get("displayName", ""),
                        "titular": entry.get("starter", False),
                        "gols": stats_dict.get("totalGoals", "0"),
                        "assistencias": stats_dict.get("goalAssists", "0"),
                        "finalizacoes": stats_dict.get("totalShots", "0"),
                        "passes_certos": stats_dict.get("accuratePasses", "0"),
                        "faltas": stats_dict.get("foulsCommitted", "0"),
                        "cartao_amarelo": stats_dict.get("yellowCards", "0"),
                        "cartao_vermelho": stats_dict.get("redCards", "0"),
                    }
                )

            escalacao[lado] = {
                "time": time_nome,
                "formacao": formacao,
                "jogadores": jogadores,
            }

        titulares_casa = sum(1 for j in escalacao["casa"].get("jogadores", []) if j["titular"])
        titulares_fora = sum(1 for j in escalacao["fora"].get("jogadores", []) if j["titular"])
        print(
            f"  Evento {evento_id}: "
            f"{escalacao['casa'].get('time', '?')} ({escalacao['casa'].get('formacao', '?')}) "
            f"{titulares_casa} titulares | "
            f"{escalacao['fora'].get('time', '?')} ({escalacao['fora'].get('formacao', '?')}) "
            f"{titulares_fora} titulares"
        )
        return escalacao

    # -----------------------------------------------------------------
    # Buscar lineups de todos os jogos de uma data
    # -----------------------------------------------------------------

    def buscar_lineups_por_data(
        self,
        liga: str = "brasileirao",
        data: str | None = None,
        salvar: bool = True,
    ) -> list[dict]:
        """
        Busca escalações de todos os jogos de uma data.

        Args:
            liga: Chave da liga.
            data: Data 'YYYY-MM-DD'. Se None, usa hoje.
            salvar: Se True, salva resultados em CSV/JSON.

        Returns:
            Lista de escalações completas.
        """
        eventos = self.buscar_eventos_por_data(liga=liga, data=data)
        if not eventos:
            return []

        todas_escalacoes = []
        linhas_csv = []

        for evento in eventos:
            lineup = self.buscar_lineup_por_evento(liga, evento["evento_id"])
            if not lineup:
                continue

            for lado in ["casa", "fora"]:
                info_lado = lineup.get(lado, {})
                for jogador in info_lado.get("jogadores", []):
                    linhas_csv.append(
                        {
                            "data": evento["data"],
                            "liga": evento["liga"],
                            "time_casa": evento["time_casa"],
                            "time_fora": evento["time_fora"],
                            "placar_casa": evento["placar_casa"],
                            "placar_fora": evento["placar_fora"],
                            "time": info_lado.get("time", ""),
                            "formacao": info_lado.get("formacao", ""),
                            "lado": lado,
                            **jogador,
                        }
                    )

            todas_escalacoes.append({"evento": evento, "escalacao": lineup})

        if salvar and linhas_csv:
            ts = timestamp_arquivo()
            salvar_csv(linhas_csv, f"lineups_{liga}_{ts}.csv")
            salvar_json(todas_escalacoes, f"lineups_{liga}_{ts}.json")

        return todas_escalacoes

    # -----------------------------------------------------------------
    # Buscar lineups dos últimos N dias
    # -----------------------------------------------------------------

    def buscar_lineups_recentes(
        self,
        liga: str = "brasileirao",
        dias: int = 3,
        salvar: bool = True,
    ) -> list[dict]:
        """
        Busca escalações dos últimos N dias.

        Args:
            liga: Chave da liga.
            dias: Quantidade de dias para trás.
            salvar: Se True, salva resultados.

        Returns:
            Lista consolidada de escalações.
        """
        todas = []
        hoje = datetime.now()

        for i in range(dias):
            data = (hoje - timedelta(days=i)).strftime("%Y-%m-%d")
            print(f"\n--- {data} ---")
            resultado = self.buscar_lineups_por_data(liga=liga, data=data, salvar=False)
            todas.extend(resultado)

        if salvar and todas:
            linhas_csv = []
            for item in todas:
                evento = item["evento"]
                lineup = item["escalacao"]
                for lado in ["casa", "fora"]:
                    info_lado = lineup.get(lado, {})
                    for jogador in info_lado.get("jogadores", []):
                        linhas_csv.append(
                            {
                                "data": evento["data"],
                                "liga": evento["liga"],
                                "time_casa": evento["time_casa"],
                                "time_fora": evento["time_fora"],
                                "time": info_lado.get("time", ""),
                                "formacao": info_lado.get("formacao", ""),
                                "lado": lado,
                                **jogador,
                            }
                        )

            ts = timestamp_arquivo()
            salvar_csv(linhas_csv, f"lineups_{liga}_recentes_{ts}.csv")
            salvar_json(todas, f"lineups_{liga}_recentes_{ts}.json")

        return todas

    # -----------------------------------------------------------------
    # Buscar times de uma liga
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
                    "logo": team.get("logos", [{}])[0].get("href", "")
                    if team.get("logos")
                    else "",
                }
            )

        print(f"  {info['nome']}: {len(times)} time(s)")
        return times

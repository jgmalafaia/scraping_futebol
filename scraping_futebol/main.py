#!/usr/bin/env python3
"""
Scraper de Lineups e Lesões de Futebol
=======================================

Exemplos:
  python -m scraping_futebol lineups --liga brasileirao
  python -m scraping_futebol lineups --liga premier-league --data 2025-05-01
  python -m scraping_futebol lineups --recentes 3 --liga brasileirao
  python -m scraping_futebol lesoes --liga premier-league
  python -m scraping_futebol lesoes-tm --slug flamengo --id 614
  python -m scraping_futebol times --liga brasileirao
"""

import argparse
import sys
from datetime import datetime

from .config import LIGAS
from .scraper_lesoes import ScraperLesoes
from .scraper_lineups import ScraperLineups


def criar_parser() -> argparse.ArgumentParser:
    """Cria o parser de argumentos da CLI."""
    parser = argparse.ArgumentParser(
        description="Scraper de Lineups e Lesões de Futebol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ligas disponíveis:
  brasileirao       Brasileirão Série A
  brasileirao-b     Brasileirão Série B
  premier-league    Premier League
  la-liga           La Liga
  serie-a           Serie A (Itália)
  bundesliga        Bundesliga
  ligue-1           Ligue 1
  champions-league  Champions League
  libertadores      Copa Libertadores
  copa-do-brasil    Copa do Brasil
  mls               MLS
  liga-portugal     Liga Portugal
  eredivisie        Eredivisie

Exemplos:
  %(prog)s lineups --liga brasileirao
  %(prog)s lineups --liga premier-league --data 2025-05-01
  %(prog)s lineups --recentes 3 --liga brasileirao
  %(prog)s lesoes --liga premier-league
  %(prog)s lesoes-tm --slug flamengo --id 614
  %(prog)s times --liga brasileirao
        """,
    )

    subparsers = parser.add_subparsers(dest="comando", help="Comando a executar")

    # --- lineups ---
    p_lineups = subparsers.add_parser("lineups", help="Buscar escalações de jogos")
    p_lineups.add_argument(
        "--liga",
        type=str,
        default="brasileirao",
        choices=list(LIGAS.keys()),
        help="Liga para buscar (padrão: brasileirao)",
    )
    p_lineups.add_argument(
        "--data",
        type=str,
        default=None,
        help="Data no formato YYYY-MM-DD (padrão: hoje)",
    )
    p_lineups.add_argument(
        "--recentes",
        type=int,
        metavar="DIAS",
        help="Buscar escalações dos últimos N dias",
    )
    p_lineups.add_argument(
        "--evento-id",
        type=str,
        help="Buscar escalação de um evento específico pelo ID",
    )

    # --- lesoes ---
    p_lesoes = subparsers.add_parser("lesoes", help="Buscar lesões de jogadores (ESPN)")
    p_lesoes.add_argument(
        "--liga",
        type=str,
        default="brasileirao",
        choices=list(LIGAS.keys()),
        help="Liga para buscar (padrão: brasileirao)",
    )
    p_lesoes.add_argument(
        "--time-id",
        type=str,
        help="Filtrar por ID do time na ESPN",
    )
    p_lesoes.add_argument(
        "--todas-ligas",
        action="store_true",
        help="Buscar lesões das 5 principais ligas",
    )

    # --- lesoes-tm (Transfermarkt) ---
    p_lesoes_tm = subparsers.add_parser(
        "lesoes-tm", help="Buscar lesões no Transfermarkt"
    )
    p_lesoes_tm.add_argument(
        "--slug",
        type=str,
        required=True,
        help="Slug do time (ex: flamengo, manchester-city)",
    )
    p_lesoes_tm.add_argument(
        "--id",
        type=int,
        required=True,
        help="ID do time no Transfermarkt (ex: 614)",
    )

    # --- times ---
    p_times = subparsers.add_parser("times", help="Listar times de uma liga")
    p_times.add_argument(
        "--liga",
        type=str,
        default="brasileirao",
        choices=list(LIGAS.keys()),
        help="Liga para listar (padrão: brasileirao)",
    )

    return parser


def executar_lineups(args: argparse.Namespace) -> None:
    """Executa o comando de lineups."""
    scraper = ScraperLineups()

    if args.evento_id:
        print(f"\n=== Escalação do evento {args.evento_id} ===\n")
        lineup = scraper.buscar_lineup_por_evento(args.liga, args.evento_id)
        if lineup:
            for lado in ["casa", "fora"]:
                info = lineup.get(lado, {})
                print(f"\n  {info.get('time', '?')} (Formação: {info.get('formacao', '?')})")
                print("  " + "-" * 50)
                for j in info.get("jogadores", []):
                    tipo = "TITULAR" if j["titular"] else "RESERVA"
                    print(
                        f"  [{tipo:>7}] {j['numero_camisa']:>2} "
                        f"{j['nome']} ({j['posicao']})"
                    )
        return

    if args.recentes:
        print(f"\n=== Lineups dos últimos {args.recentes} dia(s) - {args.liga} ===\n")
        scraper.buscar_lineups_recentes(liga=args.liga, dias=args.recentes)
        return

    if args.data:
        try:
            datetime.strptime(args.data, "%Y-%m-%d")
        except ValueError:
            print("ERRO: Data deve estar no formato YYYY-MM-DD")
            sys.exit(1)

    liga_nome = LIGAS[args.liga]["nome"]
    data_str = args.data or "hoje"
    print(f"\n=== Lineups de {data_str} - {liga_nome} ===\n")
    scraper.buscar_lineups_por_data(liga=args.liga, data=args.data)


def executar_lesoes(args: argparse.Namespace) -> None:
    """Executa o comando de lesões."""
    scraper = ScraperLesoes()

    if args.todas_ligas:
        scraper.buscar_lesoes_multiplas_ligas()
        return

    if args.time_id:
        print(f"\n=== Lesões do time {args.time_id} ({args.liga}) ===\n")
        lesoes = scraper.buscar_lesoes_por_time(args.liga, args.time_id)
        for l in lesoes:
            print(f"  - {l['jogador']} ({l['posicao']}) | {l['status']} | {l['tipo_lesao']}")
        return

    scraper.buscar_lesoes_por_liga(args.liga)


def executar_lesoes_tm(args: argparse.Namespace) -> None:
    """Executa o comando de lesões do Transfermarkt."""
    scraper = ScraperLesoes()
    lesoes = scraper.buscar_lesoes_transfermarkt(args.slug, args.id)
    for l in lesoes:
        print(f"  - {l['jogador']} ({l['posicao']}): {l['tipo_lesao']} | {l['previsao_retorno']}")


def executar_times(args: argparse.Namespace) -> None:
    """Executa o comando de listar times."""
    scraper = ScraperLineups()
    print(f"\n=== Times - {LIGAS[args.liga]['nome']} ===\n")
    times = scraper.buscar_times(args.liga)
    for t in times:
        print(f"  ID: {t['id']:>6} | {t['nome']} ({t['abreviacao']})")


def main() -> None:
    """Ponto de entrada principal."""
    parser = criar_parser()
    args = parser.parse_args()

    if not args.comando:
        parser.print_help()
        sys.exit(0)

    comandos = {
        "lineups": executar_lineups,
        "lesoes": executar_lesoes,
        "lesoes-tm": executar_lesoes_tm,
        "times": executar_times,
    }

    func = comandos.get(args.comando)
    if func:
        func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

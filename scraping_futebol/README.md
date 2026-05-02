# Scraper de Lineups e Lesões de Futebol

Ferramenta para raspar dados de **escalações (lineups)** e **lesões** de jogadores de futebol.

## Fontes de Dados

| Fonte | Dados | Método |
|-------|-------|--------|
| **ESPN API** | Escalações, formações, estatísticas de partidas | API JSON (gratuita) |
| **Transfermarkt** | Jogadores lesionados, tipo de lesão, previsão de retorno | Scraping HTML |

## Instalação

```bash
pip install -r requirements.txt
```

## Uso via Linha de Comando

### Escalações (Lineups)

```bash
# Buscar escalações dos jogos de hoje (Brasileirão)
python -m scraping_futebol lineups --liga brasileirao

# Buscar escalações de uma data específica (Premier League)
python -m scraping_futebol lineups --liga premier-league --data 2025-05-01

# Buscar escalações dos últimos 3 dias
python -m scraping_futebol lineups --recentes 3 --liga brasileirao

# Buscar escalação de uma partida específica (pelo ID do evento ESPN)
python -m scraping_futebol lineups --liga premier-league --evento-id 740942
```

### Lesões

```bash
# Buscar lesões via ESPN (se disponível para a liga)
python -m scraping_futebol lesoes --liga premier-league

# Buscar lesões no Transfermarkt (fonte mais confiável)
python -m scraping_futebol lesoes-tm --slug flamengo --id 614
python -m scraping_futebol lesoes-tm --slug real-madrid --id 418
python -m scraping_futebol lesoes-tm --slug manchester-city --id 281
```

### Utilitários

```bash
# Listar times de uma liga (com IDs da ESPN)
python -m scraping_futebol times --liga brasileirao
```

## Uso via Python

```python
from scraping_futebol.scraper_lineups import ScraperLineups
from scraping_futebol.scraper_lesoes import ScraperLesoes

# --- Escalações ---
scraper_lineups = ScraperLineups()

# Listar times
times = scraper_lineups.buscar_times("brasileirao")

# Buscar escalações do dia
escalacoes = scraper_lineups.buscar_lineups_por_data(liga="brasileirao")

# Buscar escalação de um jogo específico
lineup = scraper_lineups.buscar_lineup_por_evento("premier-league", evento_id="740942")

# --- Lesões ---
scraper_lesoes = ScraperLesoes()

# Lesões via Transfermarkt (fonte principal)
lesoes = scraper_lesoes.buscar_lesoes_transfermarkt("flamengo", 614)

# Lesões via ESPN (quando disponível)
lesoes_espn = scraper_lesoes.buscar_lesoes_por_liga("premier-league")
```

## Ligas Disponíveis

| Chave | Liga |
|-------|------|
| `brasileirao` | Brasileirão Série A |
| `brasileirao-b` | Brasileirão Série B |
| `premier-league` | Premier League |
| `la-liga` | La Liga |
| `serie-a` | Serie A (Itália) |
| `bundesliga` | Bundesliga |
| `ligue-1` | Ligue 1 |
| `champions-league` | Champions League |
| `libertadores` | Copa Libertadores |
| `copa-do-brasil` | Copa do Brasil |
| `mls` | MLS |
| `liga-portugal` | Liga Portugal |
| `eredivisie` | Eredivisie |

## IDs Transfermarkt (Times Populares)

| Time | Slug | ID |
|------|------|----|
| Flamengo | `flamengo` | `614` |
| Palmeiras | `palmeiras` | `1023` |
| Corinthians | `corinthians` | `199` |
| São Paulo | `sao-paulo-fc` | `585` |
| Vasco da Gama | `cr-vasco-da-gama` | `978` |
| Real Madrid | `real-madrid` | `418` |
| Barcelona | `fc-barcelona` | `131` |
| Manchester City | `manchester-city` | `281` |
| Liverpool | `fc-liverpool` | `31` |

## Saída dos Dados

Os dados são salvos automaticamente no diretório `dados_futebol/` em dois formatos:

- **CSV**: Para uso em planilhas (Excel, Google Sheets)
- **JSON**: Para uso programático

### Exemplo de CSV de Lineups

| data | liga | time_casa | time_fora | time | formacao | nome | posicao | titular |
|------|------|-----------|-----------|------|----------|------|---------|---------|
| 2025-05-02 | Premier League | Leeds | Burnley | Leeds | 3-5-2 | Karl Darlow | Goalkeeper | True |

### Exemplo de CSV de Lesões (Transfermarkt)

| jogador | time | posicao | tipo_lesao | previsao_retorno |
|---------|------|---------|------------|------------------|
| Léo Pereira | flamengo | Centre-Back | Cut | Return unknown |

## Estrutura do Projeto

```
scraping_futebol/
├── __init__.py          # Inicialização do pacote
├── __main__.py          # Entry point (python -m scraping_futebol)
├── config.py            # Configurações e constantes
├── main.py              # CLI principal
├── scraper_lesoes.py    # Scraper de lesões
├── scraper_lineups.py   # Scraper de escalações
├── utils.py             # Funções utilitárias
└── README.md            # Esta documentação
```

## Observações

- A ESPN API é gratuita e não requer autenticação.
- O Transfermarkt usa proteção Cloudflare — o scraping pode falhar em alguns casos.
- Escalações só estão disponíveis para jogos que já foram realizados ou estão em andamento.
- Os dados são para uso pessoal e educacional. Respeite os termos de uso das fontes.

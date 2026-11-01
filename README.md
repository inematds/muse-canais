# muse-canais

**🇧🇷 Português · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## O que é

O muse-canais olha os seus canais do YouTube e mostra quais vídeos recentes estão indo bem acima do normal de cada canal. Serve para quem publica muito e quer repetir o que funciona em vez de adivinhar. Ele lê o feed público de cada canal (os 15 vídeos mais recentes, com as visualizações), calcula quantas visualizações por hora cada vídeo ganha e compara com o vídeo típico do mesmo canal. Os que passam de 2 vezes viram "vencedores" e, se você pedir, viram 8 ideias novas de vídeo. Precisa só de Python 3; as ideias usam o Claude Code pela assinatura.

## Usar

```bash
git clone https://github.com/inematds/muse-canais ~/projetos/muse-canais
cd ~/projetos/muse-canais
python3 muse.py --atualiza-canais --dry   # descobre os canais e só mostra
python3 muse.py --ideias                  # grava relatório + 8 ideias
```

Relatório: `~/projetos/output/muse-canais/<data>/muse.md` (e `muse.json`).

| Opção | Faz |
|---|---|
| `--ideias` | 8 ideias novas a partir dos vencedores (e das pautas do radar-pautas do dia, se houver) |
| `--n 12` | quantas ideias |
| `--limiar 3` | quantas vezes acima do normal do canal para ser vencedor (padrão 2) |
| `--canais lives1,lives11` | só esses canais |
| `--atualiza-canais` | relê a lista de canais do yt-pubx (só nome e endereço) e descobre o ID público de cada um |
| `--dry` | só imprime |

**Canais:** `canais.json` (chave, nome, endereço, ID público). No INEMA ele nasce do yt-pubx; fora dele, escreva à mão:
`{"meucanal": {"nome": "Meu canal", "url": "https://www.youtube.com/@meucanal", "id": "UC…"}}` (o ID sai com `--atualiza-canais` se o endereço estiver certo).

## Como a conta é feita

- **Velocidade** = visualizações ÷ horas desde a publicação. A partir da 2ª rodada, o histórico (`estado/historico.jsonl`) também guarda o ganho entre rodadas.
- **Normal do canal** = mediana da velocidade dos vídeos com mais de 6 h, com piso de 0,5 por hora (canal quase parado não infla o resultado).
- **Vencedor** = 2× o normal ou mais, entre 6 h e 30 dias de idade, com 50+ visualizações.

## O processo, do início ao fim

🧠 sessão com o Nei · ⚙️ script/timer · 🤖 `claude -p` (assinatura)

| # | Passo | Comando / o que acontece | Quem |
|---|---|---|---|
| 1 | Canais | `muse.py --atualiza-canais` lê nome e endereço do yt-pubx e descobre o ID público | ⚙️ |
| 2 | Leitura | feed RSS público de cada canal (15 vídeos, visualizações) | ⚙️ |
| 3 | Conta | velocidade, normal do canal, vencedores; histórico em `estado/` | ⚙️ |
| 4 | Ideias | `--ideias`: 8 vídeos novos no padrão dos vencedores (+ pautas do radar) | 🤖 |
| 5 | Escolha | o Nei escolhe quais ideias viram vídeo | 🧠 |
| 6 | Diário (opcional) | `systemd/muse-canais.timer` às 08:00 — **vem desligado** | ⚙️ |

## Limites

- O feed público só traz os 15 vídeos mais recentes de cada canal e não traz tempo assistido nem retenção.
- Visualizações do feed atrasam algumas horas em relação ao YouTube Studio.
- As ideias veem só título e números: o conteúdo de cada vídeo novo precisa de fonte própria.

Licença: MIT.

# muse-canais

[![muse-canais](guia/assets/banner-en.jpg)](https://inematds.github.io/muse-canais/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 English · 🇪🇸 [Español](README.es.md)**

📖 **User guide (landing + step by step):** **https://inematds.github.io/muse-canais/guia/en/**

## What it is

muse-canais looks at your YouTube channels and shows which recent videos are performing well above each channel’s norm. It’s for people who publish a lot and want to repeat what works instead of guessing. It reads each channel’s public feed (the 15 most recent videos, with views), calculates how many views per hour each video gets, and compares that with a typical video from the same channel. Videos that exceed 2 times the norm become “winners” and, if you ask, turn into 8 new video ideas. It only requires Python 3; ideas use Claude Code through the subscription.

## Use

```bash
git clone https://github.com/inematds/muse-canais ~/projetos/muse-canais
cd ~/projetos/muse-canais
python3 muse.py --atualiza-canais --dry   # discovers the channels and only displays them
python3 muse.py --ideias                  # saves a report + 8 ideas
```

Report: `~/projetos/output/muse-canais/<data>/muse.md` (and `muse.json`).

| Option | Does |
|---|---|
| `--ideias` | 8 new ideas based on the winners (and that day’s radar-pautas topics, if any) |
| `--n 12` | number of ideas |
| `--limiar 3` | how many times above the channel’s norm to qualify as a winner (default 2) |
| `--canais lives1,lives11` | only these channels |
| `--atualiza-canais` | rereads the channel list from yt-pubx (name and address only) and discovers each channel’s public ID |
| `--dry` | only prints |

**Channels:** `canais.json` (key, name, address, public ID). At INEMA it is created from yt-pubx; elsewhere, write it by hand:
`{"meucanal": {"nome": "Meu canal", "url": "https://www.youtube.com/@meucanal", "id": "UC…"}}` (the ID is obtained with `--atualiza-canais` if the address is correct).

## How the calculation works

- **Speed** = views ÷ hours since publication. Starting with the 2nd run, the history (`estado/historico.jsonl`) also stores the increase between runs.
- **Channel norm** = median speed of videos older than 6 h, with a floor of 0.5 per hour (a nearly inactive channel doesn’t inflate the result).
- **Winner** = 2× the norm or more, between 6 h and 30 days old, with 50+ views.

## The process, from start to finish

🧠 session with Nei · ⚙️ script/timer · 🤖 `claude -p` (subscription)

| # | Step | Command / what happens | Who |
|---|---|---|---|
| 1 | Channels | `muse.py --atualiza-canais` reads the name and address from yt-pubx and discovers the public ID | ⚙️ |
| 2 | Reading | each channel’s public RSS feed (15 videos, views) | ⚙️ |
| 3 | Calculation | speed, channel norm, winners; history in `estado/` | ⚙️ |
| 4 | Ideas | `--ideias`: 8 new videos in the winners’ style (+ radar topics) | 🤖 |
| 5 | Choice | Nei chooses which ideas become videos | 🧠 |
| 6 | Daily run (optional) | `systemd/muse-canais.timer` at 08:00 — **disabled by default** | ⚙️ |

## Limitations

- The public feed only provides each channel’s 15 most recent videos and doesn’t include watch time or retention.
- Feed view counts may lag YouTube Studio by several hours.
- Ideas use only titles and numbers: each new video’s content needs its own source.

License: MIT.
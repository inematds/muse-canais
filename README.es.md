# muse-canais

[![muse-canais](guia/assets/banner-es.jpg)](https://inematds.github.io/muse-canais/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 Español**

📖 **Guía de uso (landing + paso a paso):** **https://inematds.github.io/muse-canais/guia/es/**

## Qué es

muse-canais revisa tus canales de YouTube y muestra qué videos recientes están rindiendo muy por encima de lo habitual en cada canal. Sirve para quienes publican mucho y quieren repetir lo que funciona en vez de adivinar. Lee el feed público de cada canal (los 15 videos más recientes, con sus visualizaciones), calcula cuántas visualizaciones por hora gana cada video y lo compara con el video típico del mismo canal. Los que superan 2 veces esa cifra se convierten en «ganadores» y, si lo pides, en 8 ideas nuevas de video. Solo necesita Python 3; las ideas usan Claude Code con la suscripción.

## Usar

```bash
git clone https://github.com/inematds/muse-canais ~/projetos/muse-canais
cd ~/projetos/muse-canais
python3 muse.py --atualiza-canais --dry   # descubre los canales y solo muestra
python3 muse.py --ideias                  # guarda el informe + 8 ideas
```

Informe: `~/projetos/output/muse-canais/<data>/muse.md` (y `muse.json`).

| Opción | Hace |
|---|---|
| `--ideias` | 8 ideas nuevas a partir de los ganadores (y de los temas del radar-pautas del día, si los hay) |
| `--n 12` | cuántas ideas |
| `--limiar 3` | cuántas veces por encima de lo habitual del canal para ser ganador (por defecto 2) |
| `--canais lives1,lives11` | solo esos canales |
| `--atualiza-canais` | vuelve a leer la lista de canales de yt-pubx (solo nombre y dirección) y descubre el ID público de cada uno |
| `--dry` | solo muestra |

**Canales:** `canais.json` (clave, nombre, dirección, ID público). En INEMA se genera a partir de yt-pubx; fuera de ahí, escríbelo a mano:
`{"meucanal": {"nome": "Meu canal", "url": "https://www.youtube.com/@meucanal", "id": "UC…"}}` (el ID se obtiene con `python3 -c "import muse; print(muse.resolver_id('https://www.youtube.com/@meucanal'))"`, ejecutado en la carpeta del proyecto; `--atualiza-canais` solo sirve si usas yt-pubx).

## Cómo se calcula

- **Velocidad** = visualizaciones ÷ horas desde la publicación. A partir de la segunda ejecución, el historial (`estado/historico.jsonl`) también guarda el aumento entre ejecuciones.
- **Lo habitual del canal** = mediana de la velocidad de los videos con más de 6 h, con un mínimo de 0,5 por hora (un canal casi inactivo no infla el resultado).
- **Ganador** = 2× lo habitual o más, con entre 6 h y 30 días de antigüedad, y 50+ visualizaciones.

## El proceso, de principio a fin

🧠 sesión con Nei · ⚙️ script/timer · 🤖 `claude -p` (suscripción)

| # | Paso | Comando / qué ocurre | Quién |
|---|---|---|---|
| 1 | Canales | `muse.py --atualiza-canais` lee el nombre y la dirección de yt-pubx y descubre el ID público | ⚙️ |
| 2 | Lectura | feed RSS público de cada canal (15 videos, visualizaciones) | ⚙️ |
| 3 | Cálculo | velocidad, lo habitual del canal, ganadores; historial en `estado/` | ⚙️ |
| 4 | Ideas | `--ideias`: 8 videos nuevos según el patrón de los ganadores (+ temas de radar) | 🤖 |
| 5 | Elección | Nei elige qué ideas se convierten en video | 🧠 |
| 6 | Diario (opcional) | `systemd/muse-canais.timer` a las 08:00 — **viene desactivado** | ⚙️ |

## Límites

- El feed público solo muestra los 15 videos más recientes de cada canal y no incluye el tiempo de visualización ni la retención.
- Las visualizaciones del feed pueden tardar algunas horas en actualizarse con respecto a YouTube Studio.
- Las ideas solo tienen en cuenta los títulos y las cifras: el contenido de cada video nuevo necesita una fuente propia.

Licencia: MIT.
#!/usr/bin/env python3
"""muse-canais — o que está funcionando nos nossos canais do YouTube vira ideia nova.

Uso:
  python3 muse.py                    # lê os canais, acha os vídeos que se destacam, grava relatório
  python3 muse.py --ideias           # + 8 ideias novas a partir dos vencedores (claude -p, assinatura)
  python3 muse.py --dry              # só imprime
  python3 muse.py --canais lives1,lives11 --n 8

Dados: o feed RSS público de cada canal (os 15 vídeos mais recentes, com visualizações). Sem login, sem chave.
Velocidade = visualizações por hora desde a publicação; com histórico (rodadas anteriores), usa o ganho entre rodadas.
Destaque = velocidade ÷ mediana do próprio canal (2× ou mais = vencedor).
Canais: canais.json (gerado do yt-pubx com --atualiza-canais) ou o que você escrever nele.
"""
import argparse
import concurrent.futures as cf
import html
import json
import os
import re
import statistics
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0 (muse-canais)"}
SAIDA = Path(os.environ.get("MUSE_SAIDA", Path.home() / "projetos/output/muse-canais"))
HIST = RAIZ / "estado/historico.jsonl"
RADAR = Path.home() / "projetos/output/radar-pautas"


def baixar(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf8", "ignore")


def resolver_id(url):
    m = re.search(r"/channel/(UC[\w-]{22})", url)
    if m:
        return m.group(1)
    m = re.search(r'"(?:channelId|externalId)":"(UC[\w-]{22})"', baixar(url))
    return m.group(1) if m else None


def atualiza_canais():
    """Lê só nome e endereço dos canais do yt-pubx (nunca credencial) e resolve o ID público de cada um."""
    cfg = json.loads((Path.home() / ".config/yt-pubx/config.json").read_text())
    canais = cfg.get("canais", cfg)
    atual = json.loads((RAIZ / "canais.json").read_text()) if (RAIZ / "canais.json").exists() else {}
    for k, v in canais.items():
        if not isinstance(v, dict) or not v.get("url"):
            continue
        if k in atual and atual[k].get("id"):
            continue
        try:
            cid = resolver_id(v["url"])
        except Exception as e:
            print("sem id:", k, str(e)[:60])
            continue
        atual[k] = {"nome": v.get("nome") or k, "url": v["url"], "id": cid, "idioma": v.get("idioma", "pt")}
        print("ok", k, cid)
    (RAIZ / "canais.json").write_text(json.dumps(atual, ensure_ascii=False, indent=2) + "\n")
    return atual


def ler_canal(item):
    chave, c = item
    try:
        x = baixar(f"https://www.youtube.com/feeds/videos.xml?channel_id={c['id']}")
    except Exception as e:
        return chave, [], str(e)[:80]
    videos = []
    for e in re.findall(r"<entry>(.*?)</entry>", x, re.S):
        vid = re.search(r"<yt:videoId>([^<]+)", e)
        tit = re.search(r"<title>([^<]*)</title>", e)
        pub = re.search(r"<published>([^<]+)", e)
        vw = re.search(r'<media:statistics views="(\d+)"', e)
        if not (vid and pub):
            continue
        link = re.search(r'<link rel="alternate" href="([^"]+)"', e)
        videos.append({"canal": chave, "nome_canal": c["nome"], "id": vid.group(1), "titulo": html.unescape(tit.group(1) if tit else ""),
                       "publicado": pub.group(1), "views": int(vw.group(1)) if vw else 0,
                       "link": link.group(1) if link else f"https://youtu.be/{vid.group(1)}",
                       "short": bool(link and "/shorts/" in link.group(1))})
    return chave, videos, ""


def historico_anterior():
    """Última leitura de cada vídeo (de rodadas anteriores)."""
    ult = {}
    if HIST.exists():
        for l in HIST.read_text().splitlines():
            try:
                d = json.loads(l)
            except Exception:
                continue
            ult[d["id"]] = d
    return ult


def calcula(videos, agora, antes):
    for v in videos:
        pub = datetime.fromisoformat(v["publicado"].replace("Z", "+00:00"))
        v["idade_h"] = max(0.5, (agora - pub).total_seconds() / 3600)
        v["vel"] = v["views"] / v["idade_h"]
        a = antes.get(v["id"])
        if a:
            dt = (agora - datetime.fromisoformat(a["quando"])).total_seconds() / 3600
            if dt >= 1:
                v["vel_recente"] = max(0.0, (v["views"] - a["views"]) / dt)
    por_canal = {}
    for v in videos:
        por_canal.setdefault(v["canal"], []).append(v)
    for lista in por_canal.values():
        # compara só com vídeos de mais de 6 h: vídeo de 1 h ainda não diz nada
        base = [v["vel"] for v in lista if v["idade_h"] >= 6] or [v["vel"] for v in lista]
        # piso de 0,5 visualização/hora: em canal quase parado, a mediana perto de zero inflava o destaque (244×)
        med = max(0.5, statistics.median(base)) if base else 0.5
        for v in lista:
            v["mediana_canal"] = round(med, 2)
            v["destaque"] = round(v["vel"] / med, 2) if med > 0 else 0.0
    return por_canal


def ideias(vencedores, n, radar):
    linhas = "\n".join(f"- [{v['nome_canal']}] \"{v['titulo']}\" — {v['views']} visualizações em {v['idade_h']:.0f} h, "
                       f"{v['destaque']}× a média do canal{' (short)' if v['short'] else ''}" for v in vencedores)
    extra = ""
    if radar:
        extra = "\nPautas em alta hoje (radar), para combinar com o que funciona:\n" + "\n".join(f"- {p}" for p in radar[:6])
    pedido = f"""Você é o pauteiro do INEMA (canais brasileiros que ensinam IA na prática, de graça, para gente comum, sem hype).
Estes vídeos dos NOSSOS canais estão indo melhor que a média do próprio canal:
{linhas}
{extra}

Proponha {n} vídeos NOVOS que repitam o que fez estes funcionarem (tipo de tema, promessa do título, formato), sem copiar o título.
Não invente número nem fato: se a ideia precisa de dado, diga "dado a confirmar".
Vídeos da mesma série (1/3, 2/3…) contam como UM padrão; não proponha continuação de série (parte 4) nem fato sobre o conteúdo deles: só o padrão do título e do tema.
Devolva APENAS um JSON (lista) com objetos:
{{"titulo": "até 70 caracteres", "gancho": "primeira frase do vídeo, até 14 palavras",
 "por_que": "qual vencedor inspira e o padrão que ele mostra (1 frase)", "formato": "short 9:16" | "16:9" | "carrossel",
 "canal": "a chave do canal (ex.: lives11) mais adequado"}}"""
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}  # assinatura, nunca API
    env["PATH"] = f"{Path.home()}/.local/bin:{Path.home()}/.npm-global/bin:" + env.get("PATH", "")
    try:
        out = subprocess.run(["claude", "-p", "--allowedTools", ""], input=pedido, capture_output=True, text=True, timeout=300, env=env).stdout
        m = re.search(r"\[.*\]", out, re.S)
        return json.loads(m.group(0)) if m else []
    except Exception as e:
        print("aviso: ideias não geradas:", str(e)[:100], file=sys.stderr)
        return []


def pautas_do_radar():
    if not RADAR.exists():
        return []
    dias = sorted(p for p in RADAR.iterdir() if (p / "pautas.json").exists())
    if not dias:
        return []
    d = json.loads((dias[-1] / "pautas.json").read_text())
    return [(p.get("angulo") or {}).get("titulo_pt") or p["titulo"] for p in d.get("pautas", [])]


def escreve(pasta, por_canal, vencedores, idei, meta):
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "muse.json").write_text(json.dumps({"meta": meta, "vencedores": vencedores, "ideias": idei,
                                                 "canais": {k: sorted(v, key=lambda x: -x["destaque"]) for k, v in por_canal.items()}},
                                                ensure_ascii=False, indent=2))
    md = [f"# Muse — o que está funcionando · {meta['quando']}", "",
          f"{meta['videos']} vídeos de {meta['canais_ok']} canais. Sem resposta: {', '.join(meta['falhas']) or 'nenhum'}.", "",
          "## Vencedores (velocidade ≥ 2× a mediana do canal)", "",
          "| canal | vídeo | visualizações | idade | × mediana |", "|---|---|---|---|---|"]
    for v in vencedores:
        md.append(f"| {v['nome_canal']} | [{v['titulo'][:70]}]({v['link']}) | {v['views']} | {v['idade_h']:.0f} h | {v['destaque']}× |")
    if idei:
        md += ["", f"## {len(idei)} ideias novas", ""]
        for k, i in enumerate(idei, 1):
            md += [f"### {k}. {i.get('titulo', '')}", f"- **Gancho:** {i.get('gancho', '')}", f"- **Por quê:** {i.get('por_que', '')}",
                   f"- **Formato:** {i.get('formato', '')} · **canal:** {i.get('canal', '')}", ""]
    md += ["", "## Por canal (melhor vídeo recente)", "", "| canal | melhor vídeo | visualizações | × mediana |", "|---|---|---|---|"]
    for k, lista in sorted(por_canal.items()):
        if lista:
            b = max(lista, key=lambda x: x["destaque"])
            md.append(f"| {b['nome_canal']} | {b['titulo'][:60]} | {b['views']} | {b['destaque']}× |")
    (pasta / "muse.md").write_text("\n".join(md) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ideias", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--canais", default="")
    ap.add_argument("--limiar", type=float, default=2.0)
    ap.add_argument("--atualiza-canais", action="store_true")
    a = ap.parse_args()

    canais = atualiza_canais() if a.atualiza_canais or not (RAIZ / "canais.json").exists() else json.loads((RAIZ / "canais.json").read_text())
    if a.canais:
        canais = {k: v for k, v in canais.items() if k in a.canais.split(",")}
    canais = {k: v for k, v in canais.items() if v.get("id")}
    agora = datetime.now(timezone.utc)
    antes = historico_anterior()

    videos, falhas, ok = [], [], 0
    with cf.ThreadPoolExecutor(8) as ex:
        for chave, vs, erro in ex.map(ler_canal, canais.items()):
            if erro:
                falhas.append(chave)
            else:
                ok += 1
                videos += vs
    por_canal = calcula(videos, agora, antes)
    # vencedor: destaque ≥ limiar, com pelo menos 6 h e 50 visualizações (evita o acaso de vídeo novo ou canal vazio)
    # e só dos últimos 30 dias: canal parado mostrava vídeo de meses atrás
    vencedores = sorted([v for v in videos if v["destaque"] >= a.limiar and 6 <= v["idade_h"] <= 720 and v["views"] >= 50],
                        key=lambda v: -v["destaque"])[:15]
    idei = ideias(vencedores, a.n, pautas_do_radar()) if a.ideias and vencedores else []
    meta = {"quando": datetime.now().strftime("%d/%m/%Y %H:%M"), "videos": len(videos), "canais_ok": ok, "falhas": falhas}

    for v in vencedores:
        print(f"{v['destaque']:>5}×  {v['nome_canal'][:18]:18} {v['views']:>7} vis. {v['idade_h']:>5.0f} h {v['vel']:>6.1f}/h  {v['titulo'][:64]}")
    for k, i in enumerate(idei, 1):
        print(f"ideia {k}: {i.get('titulo', '')} [{i.get('formato', '')} · {i.get('canal', '')}]")
    print(f"\n{len(videos)} vídeos de {ok} canais; {len(vencedores)} vencedores; sem resposta: {', '.join(falhas) or 'nenhum'}")

    if not a.dry:
        HIST.parent.mkdir(exist_ok=True)
        with HIST.open("a") as f:
            for v in videos:
                f.write(json.dumps({"id": v["id"], "views": v["views"], "quando": agora.isoformat()}) + "\n")
        pasta = SAIDA / datetime.now().strftime("%Y-%m-%d")
        escreve(pasta, por_canal, vencedores, idei, meta)
        print(f"gravado: {pasta}/muse.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

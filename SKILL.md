---
name: muse-canais
description: O que está funcionando nos nossos canais do YouTube — lê o feed público dos 18 canais (yt-pubx), acha os vídeos recentes que estão 2× acima do normal do próprio canal e transforma os vencedores (mais as pautas do radar do dia) em 8 ideias de vídeo. Gatilho: "o que está funcionando", "muse", "quais vídeos estão indo bem", "ideias a partir dos nossos canais", "o que repetir".
---

# muse-canais

```bash
cd ~/projetos/muse-canais
python3 muse.py --ideias          # vencedores + 8 ideias → ~/projetos/output/muse-canais/<data>/muse.md
python3 muse.py --dry             # só olhar
```

- Mostre ao Nei a tabela de vencedores e as 8 ideias; ele escolhe. Nada é produzido sem escolha.
- Rodar o radar-pautas antes (`python3 ~/projetos/radar-pautas/radar.py --angulos`) deixa as ideias combinarem "o que funciona" com "o que está em alta".
- Dados só públicos (RSS do YouTube). Nada de credencial do YouTube, nada de API com chave. Ideias pelo `claude -p` (assinatura).
- Vencedor de uma série (ex.: partes 1/3, 2/3) conta como um padrão só: não proponha a parte 4 sem ela existir.

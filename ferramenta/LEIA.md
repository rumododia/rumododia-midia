# Como funciona

- `agenda.json`: um item por dia, com tipo (post ou reels), tema, arquivo, legenda e se já foi publicado.
- Links públicos dos arquivos: `https://raw.githubusercontent.com/rumododia/rumododia-midia/main/<arquivo>`
- `ferramenta/gerar_mes.py AAAA-MM-DD DIAS`: gera posts (fundo preto) e reels alternados, com os temas pelos pesos de `ferramenta/pesos.json`.
- `ferramenta/estudio.html`: cópia do Estúdio Rumo do Dia usada para desenhar as artes.
- Fonte Instrument Serif sob licença OFL (ver `ferramenta/fontes/OFL.txt`).
- `ferramenta/frases/AAAA-MM.json`: frases novas do mês por tema (`{"fe": [["frase com *destaque*", ""], ...]}`). Quando existe, o gerador usa essas frases primeiro; só completa com o banco do estúdio se faltar.

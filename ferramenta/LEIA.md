# Como funciona

- `agenda.json`: um item por dia, com tipo (post ou reels), tema, arquivo, legenda e se já foi publicado.
- Links públicos dos arquivos: `https://raw.githubusercontent.com/rumododia/rumododia-midia/main/<arquivo>`
- `ferramenta/gerar_mes.py AAAA-MM-DD DIAS`: gera posts (fundo preto) e reels alternados, com os temas pelos pesos de `ferramenta/pesos.json`.
- `ferramenta/estudio.html`: cópia do Estúdio Rumo do Dia usada para desenhar as artes.
- Fonte Instrument Serif sob licença OFL (ver `ferramenta/fontes/OFL.txt`).
- `ferramenta/frases/AAAA-MM.json`: frases novas do mês por tema (`{"fe": [["frase com *destaque*", ""], ...]}`). Quando existe, o gerador usa essas frases primeiro; só completa com o banco do estúdio se faltar.
- `ferramenta/inspiracao.md`: o que mais engaja em perfis de frases. LEIA ANTES de escrever as frases novas de cada mês e siga as regras práticas dele.
- No arquivo de frases do mês, a chave `_datas` fixa a frase de um dia e turno: `{"_datas": {"2026-12-25": {"manha": ["frase", "autor", "tema"], "noite": [...]}}}`. Datas fixas têm prioridade.
- Visual: o gerador alterna 4 combinações a cada publicação (marca-texto no preto, bloco no branco, marca-texto no branco, bloco no preto). O modelo "bloco" usa a fonte Newsreader, linhas centralizadas esticadas e palavras-chave em itálico. O campo `modelo` da agenda registra qual foi usado (dá pra comparar engajamento por modelo).

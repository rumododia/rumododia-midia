"""Gera os posts e reels de um período e atualiza a agenda.json.
Uso: python3 ferramenta/gerar_mes.py AAAA-MM-DD NUM_DIAS
Gera 2 publicações por dia: post estático (turno "manha", 6h) e reels (turno "noite", 19h), com temas diferentes.
Precisa de: playwright (python), google-chrome, ffmpeg."""
import asyncio, base64, json, os, subprocess, sys, pathlib
from playwright.async_api import async_playwright
ROOT = pathlib.Path(__file__).resolve().parent.parent
FER = ROOT/"ferramenta"
start, n = sys.argv[1], int(sys.argv[2])
# 3º argumento opcional: turnos do dia, ex. "manha:post,tarde:post,noite:reels" (padrão: "manha:post,noite:reels")
SLOTS = [tuple(x.split(":")) for x in (sys.argv[3] if len(sys.argv) > 3 else "manha:post,noite:reels").split(",")]
pesos = json.load(open(FER/"pesos.json"))
# Frases novas do mês (opcional): ferramenta/frases/AAAA-MM.json = {"tema": [["frase com *destaque*", "autor ou vazio"], ...]}
fr_path = FER/"frases"/f"{start[:7]}.json"
frases = json.load(open(fr_path)) if fr_path.exists() else {}
if frases.get("_pesos"): pesos = frases["_pesos"]   # pesos só deste mês
mes_dir = ROOT/start[:7]; mes_dir.mkdir(exist_ok=True)
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
JS_ITEMS = r"""
async ({start, n, pesos, frases, slots}) => {
  const R = window.__rumo;
  Object.assign(R.state.weights, pesos);
  R.state.bg = 'preto';
  const [y,m,d] = start.split('-').map(Number);
  const seed = y*100+m+d;
  const S = slots.length;
  const cats = R.assignThemes(S*n, seed);   // S publicações por dia, temas diferentes
  const used = {}; const items = [];
  for (let i=0;i<S*n;i++){
    const date = new Date(y, m-1, d+Math.floor(i/S)); date.setHours(0,0,0,0);
    const cat = cats[i];
    const k = (used[cat]=(used[cat]||0)+1)-1;
    const turno = slots[i%S][0], kind = slots[i%S][1]==="reels" ? "reel" : "static", iso = R.isoOf(date);
    const fixa = frases && frases._datas && frases._datas[iso] && frases._datas[iso][turno];
    if (fixa) { used[cat]--; items.push({iso, cat: fixa[2]||cat, text:fixa[0], author:fixa[1]||"", kind, turno}); continue; }
    const novas = (frases && frases[cat]) || [];
    const p = k < novas.length ? novas[k] : R.BANK[cat][(seed*7+k) % R.BANK[cat].length];
    items.push({iso, cat, text:p[0], author:p[1]||"", kind, turno});
  }
  return items;
}"""
JS_STATIC = r"""
async (it) => {
  const R = window.__rumo; const [y,m,d] = it.iso.split('-').map(Number);
  const S = {date:new Date(y,m-1,d), cat:it.cat, text:it.text, author:it.author};
  R.draw(S); return {img: R.cv.toDataURL('image/jpeg', 0.93), cap: R.captionFor(S)};
}"""
JS_REEL = r"""
async (it) => {
  const R = window.__rumo; const [y,m,d] = it.iso.split('-').map(Number);
  const S = {date:new Date(y,m-1,d), cat:it.cat, text:it.text, author:it.author};
  const r = await R.recordReel(S); const dur = R.draw.duration;
  R.draw(S, {t:1e6}); const cover = R.cv.toDataURL('image/jpeg', 0.92);
  const u8 = new Uint8Array(await r.blob.arrayBuffer()); let bin='';
  for (let i=0;i<u8.length;i+=0x8000) bin+=String.fromCharCode.apply(null,u8.subarray(i,i+0x8000));
  return {vid: btoa(bin), ext:r.ext, dur, cover, cap: R.captionFor(S)};
}"""
FONT_CSS = f"""
@font-face{{font-family:"Instrument Serif";font-style:normal;font-weight:400;src:url(file://{FER}/fontes/InstrumentSerif-Regular.ttf)}}
@font-face{{font-family:"Instrument Serif";font-style:italic;font-weight:400;src:url(file://{FER}/fontes/InstrumentSerif-Italic.ttf)}}
"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width":1200,"height":900})
        await pg.goto(f"file://{FER}/estudio.html")
        await pg.add_style_tag(content=FONT_CSS)
        await pg.evaluate("Promise.all([document.fonts.load('400 100px \"Instrument Serif\"'),document.fonts.load('italic 400 100px \"Instrument Serif\"')])")
        assert await pg.evaluate("document.fonts.check('400 100px \"Instrument Serif\"')"), "fonte não carregou"
        items = await pg.evaluate(JS_ITEMS, {"start":start, "n":n, "pesos":pesos, "frases":frases, "slots":[list(x) for x in SLOTS]})
        novos = []
        for it in items:
            base = mes_dir/it["iso"]
            if it["kind"]=="static":
                r = await pg.evaluate(JS_STATIC, it)
                (mes_dir/f"{it['iso']}-{it['turno']}-post.jpg").write_bytes(base64.b64decode(r["img"].split(",")[1]))
                novos.append({"data":it["iso"],"turno":it["turno"],"tipo":"post","tema":it["cat"],"arquivo":f"{start[:7]}/{it['iso']}-{it['turno']}-post.jpg","legenda":r["cap"],"publicado":False})
            else:
                r = await pg.evaluate(JS_REEL, it)
                raw = mes_dir/f"{it['iso']}-{it['turno']}-raw.{r['ext']}"; raw.write_bytes(base64.b64decode(r["vid"]))
                mp4 = mes_dir/f"{it['iso']}-{it['turno']}-reels.mp4"
                subprocess.run(["ffmpeg","-loglevel","error","-y","-i",str(raw),"-f","lavfi","-i","anullsrc=r=44100:cl=stereo","-shortest",
                    "-c:v","libx264","-profile:v","high","-pix_fmt","yuv420p","-r","30","-preset","veryfast","-crf","20",
                    "-c:a","aac","-b:a","128k","-movflags","+faststart",str(mp4)], check=True)
                raw.unlink()
                (mes_dir/f"{it['iso']}-{it['turno']}-reels-capa.jpg").write_bytes(base64.b64decode(r["cover"].split(",")[1]))
                novos.append({"data":it["iso"],"turno":it["turno"],"tipo":"reels","tema":it["cat"],"arquivo":f"{start[:7]}/{it['iso']}-{it['turno']}-reels.mp4",
                    "capa":f"{start[:7]}/{it['iso']}-{it['turno']}-reels-capa.jpg","thumb_offset_ms":int((r["dur"]-1)*1000),"legenda":r["cap"],"publicado":False})
            print(it["iso"], it["kind"], it["cat"], flush=True)
        await b.close()
    ag_path = ROOT/"agenda.json"
    agenda = json.load(open(ag_path)) if ag_path.exists() else []
    datas = {x["data"] for x in novos}
    agenda = [x for x in agenda if x["data"] not in datas] + novos
    ordem = {"manha":0, "tarde":1, "noite":2}
    agenda.sort(key=lambda x: (x["data"], ordem.get(x.get("turno","manha"), 0)))
    json.dump(agenda, open(ag_path,"w"), ensure_ascii=False, indent=1)
asyncio.run(main())

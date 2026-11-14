#!/usr/bin/env python3
"""
update_instagram.py — Afegeix dades d'Instagram a un catàleg existent
=====================================================================
Llegeix els JSONs d'Instagram des d'una carpeta ja descomprimida
i actualitza el catalog_total.html sense tornar a escanejar els discs.

Ús:
    python3 update_instagram.py \
        --catalog ~/Desktop/catalog_total.html \
        --instagram ~/Desktop/instagram-francesc.ferre-2026-11-14-9GAXDpcn \
        --out ~/Desktop/catalog_instagram.html
"""

import json, re, sys, argparse
from pathlib import Path
from datetime import datetime

# ─── LECTURA INSTAGRAM ──────────────────────────────────────────────────────

def load_instagram_folder(ig_root):
    """Llegeix tots els JSONs de posts/reels/igtv d'una carpeta d'Instagram."""
    root = Path(ig_root).expanduser().resolve()

    # Cerca la carpeta de posts
    posts_dir = None
    for candidate in [
        root / 'your_instagram_activity' / 'posts' / 'media',
        root / 'your_instagram_activity' / 'posts',
        root / 'your_instagram_activity' / 'media',
        root / 'content',
        root / 'media',
        root,
    ]:
        if candidate.is_dir():
            posts_dir = candidate
            break

    if not posts_dir:
        print(f"⚠️  No trobada carpeta de posts a: {root}", file=sys.stderr)
        return {}

    print(f"📂  Llegint JSONs d'Instagram a: {posts_dir}")

    ig_map = {}  # date (YYYY-MM-DD) → {'caption': ..., 'ig_uri': ...}

    json_files = list(posts_dir.glob('*.json'))
    if not json_files:
        print(f"⚠️  Cap JSON trobat a: {posts_dir}", file=sys.stderr)
        return {}

    for jf in sorted(json_files):
        print(f"  Llegint {jf.name} ({jf.stat().st_size // 1024} KB)...")
        try:
            with open(jf, encoding='utf-8') as f:
                raw = json.load(f)
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
            continue

        items = []
        if isinstance(raw, list):
            items = raw
        elif isinstance(raw, dict):
            # Reels: {"ig_reels_media": [...]}
            # Stories: {"ig_stories": [...]}
            for key in raw:
                if isinstance(raw[key], list):
                    items.extend(raw[key])

        for item in items:
            caption = item.get('title', '')
            media_list = item.get('media', [item])

            for m in media_list:
                ts = m.get('creation_timestamp') or m.get('taken_at')
                if not caption:
                    caption = m.get('title', '')
                ig_uri = m.get('uri', '')
                if ts:
                    d = datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d')
                    if d not in ig_map:  # primer post del dia guanya
                        ig_map[d] = {
                            'caption': caption or '',
                            'ig_uri': ig_uri,
                        }

    print(f"  → {len(ig_map)} dates úniques d'Instagram trobades")
    return ig_map

# ─── LECTURA CATÀLEG HTML ───────────────────────────────────────────────────

def read_catalog(html_path):
    """Extreu el DATA array d'un catàleg HTML generat per catalog_videos.py."""
    text = Path(html_path).expanduser().read_text(encoding='utf-8')
    m = re.search(r'const DATA = (\[.*?\]);', text, re.DOTALL)
    if not m:
        print(f"⚠️  No trobat DATA al fitxer: {html_path}", file=sys.stderr)
        sys.exit(1)
    return json.loads(m.group(1))

# ─── ACTUALITZACIÓ ──────────────────────────────────────────────────────────

def update_videos(videos, ig_map):
    """Marca els vídeos que coincideixen per data amb Instagram."""
    matched = 0
    for v in videos:
        date = v.get('date', '')
        if date and date in ig_map:
            v['ig_caption'] = ig_map[date]['caption']
            v['ig_date'] = date
            matched += 1
        else:
            v.setdefault('ig_caption', None)
            v.setdefault('ig_date', None)
    print(f"\n✅  {matched} vídeos marcats com a Instagram de {len(videos)} totals")
    return videos

# ─── GENERACIÓ HTML ─────────────────────────────────────────────────────────

def dur_str(s):
    if not s:
        return ''
    m, sec = divmod(int(s), 60)
    h, m = divmod(m, 60)
    return f'{h}:{m:02d}:{sec:02d}' if h else f'{m}:{sec:02d}'

def res_label(w):
    if not w:
        return ''
    if w >= 3840: return '4K'
    if w >= 1920: return 'FHD'
    if w >= 1280: return 'HD'
    return 'SD'

def build_html(videos, output_path):
    total_mb  = sum(v.get('size_mb') or 0 for v in videos)
    total_gb  = round(total_mb / 1024, 1)
    years     = sorted({v['year'] for v in videos if v.get('year')}, reverse=True)
    generated = datetime.now().strftime('%d/%m/%Y %H:%M')
    ig_count  = sum(1 for v in videos if v.get('ig_caption') is not None)

    videos_out = sorted(videos, key=lambda v: v.get('date') or '', reverse=True)
    data_js    = json.dumps(videos_out, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arxiu de Vídeos</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#1a1510;--surface:#231e18;--surface2:#2c261f;
  --text:#f0e8d8;--muted:#8c7d6a;--accent:#e8a84a;
  --ig:#c06090;--border:#3d352b;
}}
body{{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:14px}}
header{{background:var(--surface);border-bottom:1px solid var(--border);padding:16px 20px;position:sticky;top:0;z-index:10}}
.header-top{{display:flex;align-items:center;gap:12px;flex-wrap:wrap}}
h1{{font-size:1.3rem;font-weight:700;color:var(--accent)}}
.stats{{color:var(--muted);font-size:0.8rem;margin-top:4px}}
.controls{{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center}}
input[type=text]{{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:6px 10px;border-radius:6px;font-size:13px;width:220px}}
input::placeholder{{color:var(--muted)}}
select{{background:var(--surface2);border:1px solid var(--border);color:var(--text);padding:6px 8px;border-radius:6px;font-size:13px}}
.btn{{background:var(--surface2);border:1px solid var(--border);color:var(--muted);padding:4px 10px;border-radius:5px;cursor:pointer;font-size:12px;white-space:nowrap}}
.btn.active,.btn:hover{{background:var(--accent);color:#111;border-color:var(--accent)}}
.btn.ig{{border-color:var(--ig);color:var(--ig)}}
.btn.ig.active{{background:var(--ig);color:#fff;border-color:var(--ig)}}
.year-btns{{display:flex;gap:4px;flex-wrap:wrap}}
main{{padding:16px 20px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px;cursor:pointer;transition:border-color .15s}}
.card:hover{{border-color:var(--accent)}}
.card.ig-match{{border-left:3px solid var(--ig)}}
.card-name{{font-size:0.85rem;font-weight:600;color:var(--text);word-break:break-all;margin-bottom:6px}}
.card-meta{{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:6px}}
.tag{{font-size:0.7rem;padding:2px 6px;border-radius:4px;background:var(--surface2)}}
.tag-ig{{background:#4a1a30;color:var(--ig)}}
.caption{{font-size:0.75rem;color:var(--muted);font-style:italic;margin-top:4px;word-break:break-word}}
.path{{font-size:0.65rem;color:var(--muted);margin-top:6px;word-break:break-all}}
.copy-btn{{display:inline-block;margin-top:6px;font-size:0.65rem;background:var(--surface2);border:1px solid var(--border);color:var(--muted);padding:2px 8px;border-radius:4px;cursor:pointer}}
.copy-btn:hover{{color:var(--accent);border-color:var(--accent)}}
.empty{{grid-column:1/-1;text-align:center;padding:60px;color:var(--muted)}}
#count{{color:var(--muted);font-size:0.8rem}}
</style>
</head>
<body>
<header>
  <div class="header-top">
    <h1>📼 Arxiu de Vídeos</h1>
    <span id="count"></span>
  </div>
  <div class="stats">{len(videos):,} vídeos · {total_gb:,} GB · {ig_count:,} coincidències Instagram · Generat {generated}</div>
  <div class="controls">
    <input type="text" id="search" placeholder="Buscar per nom o descripció...">
    <select id="sort">
      <option value="date_desc">Data ↓</option>
      <option value="date_asc">Data ↑</option>
      <option value="size_desc">Mida ↓</option>
      <option value="name_asc">Nom A-Z</option>
    </select>
    <select id="res_filter">
      <option value="">Totes les resolucions</option>
      <option value="4K">4K</option>
      <option value="FHD">Full HD</option>
      <option value="HD">HD</option>
      <option value="SD">SD/desconegut</option>
    </select>
    <button class="btn ig" id="ig_btn" onclick="toggleIG()">📸 Instagram ({ig_count:,})</button>
  </div>
  <div class="controls year-btns">
    <button class="btn active" onclick="setYear(null,this)">Tots</button>
    {''.join(f'<button class="btn" onclick="setYear({y},this)">{y}</button>' for y in years)}
  </div>
</header>
<main>
  <div class="grid" id="grid"></div>
</main>
<script>
const DATA = {data_js};
let curYear = null, curIG = false;

function res_label(w) {{
  if(!w) return '';
  if(w>=3840) return '4K';
  if(w>=1920) return 'FHD';
  if(w>=1280) return 'HD';
  return 'SD';
}}
function dur_str(s) {{
  if(!s) return '';
  let m=Math.floor(s/60), sec=s%60, h=Math.floor(m/60);
  m=m%60;
  return h?`${{h}}:${{String(m).padStart(2,'0')}}:${{String(sec).padStart(2,'0')}}`:`${{m}}:${{String(sec).padStart(2,'0')}}`;
}}
function escHtml(s) {{ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }}

function render() {{
  const q = document.getElementById('search').value.toLowerCase();
  const sort = document.getElementById('sort').value;
  const res_f = document.getElementById('res_filter').value;

  let data = DATA.filter(v => {{
    if(curYear && v.year !== curYear) return false;
    if(curIG && !v.ig_caption) return false;
    if(res_f) {{
      const r = res_label(v.width);
      if(res_f === 'SD' && r !== 'SD' && r !== '') return false;
      if(res_f !== 'SD' && r !== res_f) return false;
    }}
    if(q) {{
      const hay = (v.name+'|'+(v.ig_caption||'')+'|'+v.path).toLowerCase();
      if(!hay.includes(q)) return false;
    }}
    return true;
  }});

  data.sort((a,b) => {{
    if(sort==='date_desc') return (b.date||'').localeCompare(a.date||'');
    if(sort==='date_asc')  return (a.date||'').localeCompare(b.date||'');
    if(sort==='size_desc') return (b.size_mb||0)-(a.size_mb||0);
    if(sort==='name_asc')  return a.name.localeCompare(b.name);
    return 0;
  }});

  document.getElementById('count').textContent = data.length.toLocaleString() + ' vídeos';

  const html = data.map(v => {{
    const rl = res_label(v.width);
    const ig = v.ig_caption !== null && v.ig_caption !== undefined;
    return `<div class="card${{ig?' ig-match':''}}">
  <div class="card-name">${{escHtml(v.name)}}</div>
  <div class="card-meta">
    <span class="tag">${{escHtml(v.date||'?')}}</span>
    ${{rl?`<span class="tag">${{rl}}</span>`:''}}
    ${{v.duration?`<span class="tag">${{dur_str(v.duration)}}</span>`:''}}
    ${{v.size_mb?`<span class="tag">${{v.size_mb}} MB</span>`:''}}
    ${{ig?`<span class="tag tag-ig">📸 Instagram</span>`:''}}
  </div>
  ${{ig&&v.ig_caption?`<div class="caption">"${{escHtml(v.ig_caption.substring(0,100))}}${{v.ig_caption.length>100?'…':''}}"</div>`:''}}
  <div class="path">${{escHtml(v.path)}}</div>
  <span class="copy-btn" onclick="navigator.clipboard.writeText('${{v.path.replace(/'/g,"\\\\'")}}');this.textContent='✓ Copiat!'">Copiar ruta</span>
</div>`;
  }}).join('') || '<div class="empty">Cap vídeo trobat</div>';

  document.getElementById('grid').innerHTML = html;
}}

function setYear(y, el) {{
  curYear = y;
  document.querySelectorAll('.year-btns .btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  render();
}}
function toggleIG() {{
  curIG = !curIG;
  document.getElementById('ig_btn').classList.toggle('active', curIG);
  render();
}}

document.getElementById('search').addEventListener('input', render);
document.getElementById('sort').addEventListener('change', render);
document.getElementById('res_filter').addEventListener('change', render);
render();
</script>
</body>
</html>"""

    out = Path(output_path).expanduser()
    out.write_text(html, encoding='utf-8')
    print(f"\n✅  Catàleg generat: {out}")
    print(f"    Vídeos totals:  {len(videos):,}")
    print(f"    Instagram:      {ig_count:,} coincidències")
    print(f"    Mida total:     {total_gb} GB")

# ─── MAIN ───────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description='Actualitza catàleg amb dades d\'Instagram')
    p.add_argument('--catalog',   required=True, help='catalog_total.html existent')
    p.add_argument('--instagram', required=True, help='Carpeta de l\'export d\'Instagram')
    p.add_argument('--out',       default='~/Desktop/catalog_instagram.html')
    args = p.parse_args()

    print("🔍  Llegint catàleg existent...")
    videos = read_catalog(args.catalog)
    print(f"    {len(videos):,} vídeos carregats")

    ig_map = load_instagram_folder(args.instagram)
    if not ig_map:
        print("⚠️  No s'han pogut llegir les dades d'Instagram. Sortint.", file=sys.stderr)
        sys.exit(1)

    videos = update_videos(videos, ig_map)
    build_html(videos, args.out)

if __name__ == '__main__':
    main()

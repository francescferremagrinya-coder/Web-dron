#!/usr/bin/env python3
"""
merge_catalogs.py — Uneix diversos catàlegs HTML en un de sol
Ús: python3 merge_catalogs.py catalog.html catalog_francesc.html catalog_francesc2.html
Genera: catalog_total.html
"""

import sys, json, re
from pathlib import Path
from datetime import datetime

def extract_data(html_path):
    text = Path(html_path).read_text(encoding='utf-8')
    m = re.search(r'const DATA = (\[.*?\]);', text, re.DOTALL)
    if not m:
        print(f"⚠️  No s'ha trobat DATA a {html_path}")
        return []
    data = json.loads(m.group(1))
    print(f"  ✓ {Path(html_path).name}: {len(data)} vídeos")
    return data

def build_html(videos, output_path):
    total_mb  = sum(v.get('size_mb') or 0 for v in videos)
    total_gb  = round(total_mb / 1024, 1)
    years     = sorted({v['year'] for v in videos if v.get('year')}, reverse=True)
    generated = datetime.now().strftime('%d/%m/%Y %H:%M')
    ig_count  = sum(1 for v in videos if v.get('ig_caption'))

    videos_out = sorted(videos, key=lambda v: v.get('date') or '', reverse=True)
    data_js    = json.dumps(videos_out, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Arxiu de Vídeos — Total</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0e0c09;--bg2:#161210;--card:#1d1810;--card-h:#261f15;
  --gold:#d4a640;--gold-l:#f0c96a;--amber:#c97c2e;
  --white:#f5ede0;--grey:#7a6b58;--grey-l:#a89070;
  --border:rgba(212,166,64,.12);--border-h:rgba(212,166,64,.3);
  --rad:10px;--font:'Segoe UI',system-ui,sans-serif;
}}
body{{background:var(--bg);color:var(--white);font-family:var(--font);min-height:100vh;padding:0 0 60px}}
.header{{background:var(--bg2);border-bottom:1px solid var(--border);padding:20px 24px;
  display:flex;align-items:center;gap:16px;flex-wrap:wrap}}
.header__title{{font-size:1.4rem;font-weight:700;color:var(--gold-l);flex:1;min-width:200px}}
.header__meta{{font-size:.8rem;color:var(--grey);line-height:1.6}}
.stats{{display:flex;gap:20px;flex-wrap:wrap}}
.stat{{text-align:center}}
.stat__n{{font-size:1.5rem;font-weight:700;color:var(--gold)}}
.stat__l{{font-size:.7rem;color:var(--grey);text-transform:uppercase;letter-spacing:.06em}}
.controls{{background:var(--bg2);border-bottom:1px solid var(--border);padding:14px 24px;
  display:flex;flex-wrap:wrap;gap:12px;align-items:center;position:sticky;top:0;z-index:10}}
.search{{flex:1;min-width:200px;background:var(--card);border:1px solid var(--border);
  border-radius:var(--rad);padding:9px 14px;color:var(--white);font-size:.9rem;outline:none}}
.search:focus{{border-color:var(--gold);box-shadow:0 0 0 3px rgba(212,166,64,.1)}}
.search::placeholder{{color:var(--grey)}}
.filters{{display:flex;flex-wrap:wrap;gap:6px}}
.btn{{background:var(--card);border:1px solid var(--border);color:var(--grey-l);
  padding:5px 12px;border-radius:20px;font-size:.78rem;cursor:pointer;transition:.2s}}
.btn:hover{{border-color:var(--gold);color:var(--gold)}}
.btn.active{{background:rgba(212,166,64,.15);border-color:var(--gold);color:var(--gold-l);font-weight:600}}
.sep{{width:1px;background:var(--border);align-self:stretch;margin:2px 4px}}
select{{background:var(--card);border:1px solid var(--border);color:var(--grey-l);
  padding:5px 10px;border-radius:var(--rad);font-size:.78rem;cursor:pointer;outline:none}}
select:focus{{border-color:var(--gold)}}
.results-info{{padding:10px 24px;font-size:.8rem;color:var(--grey)}}
.list{{padding:0 24px}}
.item{{background:var(--card);border:1px solid var(--border);border-radius:var(--rad);
  padding:14px 16px;margin-bottom:8px;display:grid;
  grid-template-columns:1fr auto;gap:8px 16px;transition:.2s}}
.item:hover{{background:var(--card-h);border-color:var(--border-h)}}
.item__main{{min-width:0}}
.item__name{{font-size:.95rem;font-weight:600;color:var(--white);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:4px}}
.item__path{{font-size:.72rem;color:var(--grey);font-family:monospace;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:6px}}
.item__meta{{display:flex;flex-wrap:wrap;gap:6px;align-items:center}}
.tag{{font-size:.7rem;padding:2px 8px;border-radius:12px;border:1px solid var(--border)}}
.tag--year{{color:var(--gold);border-color:rgba(212,166,64,.3)}}
.tag--dur{{color:var(--grey-l)}}
.tag--res{{color:#7ab8d4;border-color:rgba(122,184,212,.3)}}
.tag--4k{{color:#a0d47a;border-color:rgba(160,212,122,.3)}}
.tag--size{{color:var(--grey)}}
.tag--ig{{color:#d478a0;border-color:rgba(212,120,160,.3)}}
.tag--disc{{color:#c4a87a;border-color:rgba(196,168,122,.3)}}
.item__caption{{font-size:.8rem;color:var(--grey-l);margin-top:6px;
  font-style:italic;line-height:1.4;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.item__actions{{display:flex;flex-direction:column;gap:6px;align-items:flex-end;flex-shrink:0}}
.copy-btn{{background:transparent;border:1px solid var(--border);color:var(--grey);
  padding:4px 10px;border-radius:6px;font-size:.72rem;cursor:pointer;transition:.2s;white-space:nowrap}}
.copy-btn:hover{{border-color:var(--gold);color:var(--gold)}}
.copy-btn.copied{{border-color:#6dbf6d;color:#6dbf6d}}
.item__date{{font-size:.72rem;color:var(--grey);text-align:right}}
.empty{{text-align:center;padding:60px 24px;color:var(--grey)}}
.empty__icon{{font-size:3rem;margin-bottom:16px;opacity:.4}}
.footer{{text-align:center;padding:30px;font-size:.75rem;color:var(--grey)}}
@media(max-width:600px){{
  .header{{padding:16px}}
  .controls{{padding:12px 16px}}
  .list{{padding:0 12px}}
  .item{{grid-template-columns:1fr}}
  .item__actions{{flex-direction:row;align-items:center}}
}}
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="header__title">Arxiu de Vídeos — Total</div>
    <div class="header__meta">Generat el {generated}</div>
  </div>
  <div class="stats">
    <div class="stat"><div class="stat__n" id="s-total">0</div><div class="stat__l">vídeos</div></div>
    <div class="stat"><div class="stat__n">{total_gb}GB</div><div class="stat__l">total disc</div></div>
    <div class="stat"><div class="stat__n">{len(years)}</div><div class="stat__l">anys</div></div>
    <div class="stat"><div class="stat__n" id="s-ig">0</div><div class="stat__l">a Instagram</div></div>
  </div>
</div>

<div class="controls">
  <input type="search" class="search" id="q" placeholder="Cerca per nom, ruta o descripció…" autocomplete="off">

  <div class="filters" id="year-btns">
    <button class="btn active" data-year="all">Tots els anys</button>
  </div>

  <div class="sep"></div>

  <div class="filters">
    <button class="btn active" data-res="all">Tota resolució</button>
    <button class="btn" data-res="4k">4K</button>
    <button class="btn" data-res="hd">HD</button>
    <button class="btn" data-res="sd">SD</button>
  </div>

  <div class="sep"></div>

  <div class="filters" id="disc-btns">
    <button class="btn active" data-disc="all">Tots els discs</button>
  </div>

  <div class="sep"></div>

  <div class="filters">
    <button class="btn active" data-ig="all">Tot</button>
    <button class="btn" data-ig="yes">Només Instagram</button>
    <button class="btn" data-ig="no">Sense Instagram</button>
  </div>

  <div class="sep"></div>

  <select id="sort">
    <option value="date-desc">Data ↓</option>
    <option value="date-asc">Data ↑</option>
    <option value="name-asc">Nom A–Z</option>
    <option value="name-desc">Nom Z–A</option>
    <option value="size-desc">Mida ↓</option>
    <option value="dur-desc">Durada ↓</option>
  </select>
</div>

<div class="results-info" id="results-info"></div>
<div class="list" id="list"></div>
<div class="empty" id="empty" style="display:none">
  <div class="empty__icon">🎬</div>
  <div>Cap vídeo coincideix amb el filtre</div>
</div>

<div class="footer">Generat amb merge_catalogs.py · {len(videos_out)} vídeos · {total_gb} GB</div>

<script>
const DATA = {data_js};

const igCount = DATA.filter(v => v.ig_caption).length;
document.getElementById('s-total').textContent = DATA.length;
document.getElementById('s-ig').textContent    = igCount;

// Year buttons
const years = [...new Set(DATA.map(v => v.year).filter(Boolean))].sort((a,b)=>b-a);
const ybContainer = document.getElementById('year-btns');
years.forEach(y => {{
  const b = document.createElement('button');
  b.className = 'btn'; b.dataset.year = y; b.textContent = y;
  ybContainer.appendChild(b);
}});

// Disc buttons
const discs = [...new Set(DATA.map(v => v.path.split('/')[2]).filter(Boolean))].sort();
const dbContainer = document.getElementById('disc-btns');
discs.forEach(d => {{
  const b = document.createElement('button');
  b.className = 'btn'; b.dataset.disc = d; b.textContent = d;
  dbContainer.appendChild(b);
}});

let activeYear = 'all', activeRes = 'all', activeIg = 'all', activeDisc = 'all', sortKey = 'date-desc';

document.querySelectorAll('[data-year]').forEach(b => b.addEventListener('click', () => {{
  activeYear = b.dataset.year;
  document.querySelectorAll('[data-year]').forEach(x => x.classList.toggle('active', x===b));
  render();
}}));
document.querySelectorAll('[data-res]').forEach(b => b.addEventListener('click', () => {{
  activeRes = b.dataset.res;
  document.querySelectorAll('[data-res]').forEach(x => x.classList.toggle('active', x===b));
  render();
}}));
document.querySelectorAll('[data-ig]').forEach(b => b.addEventListener('click', () => {{
  activeIg = b.dataset.ig;
  document.querySelectorAll('[data-ig]').forEach(x => x.classList.toggle('active', x===b));
  render();
}}));
document.getElementById('disc-btns').addEventListener('click', e => {{
  const b = e.target.closest('[data-disc]');
  if (!b) return;
  activeDisc = b.dataset.disc;
  document.querySelectorAll('[data-disc]').forEach(x => x.classList.toggle('active', x===b));
  render();
}});
document.getElementById('sort').addEventListener('change', e => {{ sortKey = e.target.value; render(); }});
document.getElementById('q').addEventListener('input', render);

function resCategory(v) {{
  if (!v.width) return 'unknown';
  if (v.width >= 3840) return '4k';
  if (v.width >= 1280) return 'hd';
  return 'sd';
}}
function resLabel(v) {{
  if (!v.width) return '';
  if (v.width >= 3840) return '4K';
  if (v.width >= 1920) return 'FHD';
  if (v.width >= 1280) return 'HD';
  return 'SD';
}}
function durStr(s) {{
  if (!s) return '';
  const m = Math.floor(s/60), sec = s%60, h = Math.floor(m/60), mm = m%60;
  return h ? `${{h}}:${{String(mm).padStart(2,'0')}}:${{String(sec).padStart(2,'0')}}` : `${{m}}:${{String(sec).padStart(2,'0')}}`;
}}
function discName(p) {{ return p.split('/')[2] || ''; }}
function abbrevPath(p) {{
  const parts = p.split('/');
  if (parts.length <= 5) return p;
  return parts.slice(0,3).join('/') + '/…/' + parts.slice(-2).join('/');
}}

function render() {{
  const q = document.getElementById('q').value.trim().toLowerCase();
  const list = document.getElementById('list');
  const empty = document.getElementById('empty');
  const info  = document.getElementById('results-info');

  let items = DATA.filter(v => {{
    if (activeYear !== 'all' && v.year !== +activeYear) return false;
    if (activeRes  !== 'all' && resCategory(v) !== activeRes) return false;
    if (activeDisc !== 'all' && discName(v.path) !== activeDisc) return false;
    if (activeIg === 'yes' && !v.ig_caption) return false;
    if (activeIg === 'no'  &&  v.ig_caption) return false;
    if (q) {{
      const h = (v.name + ' ' + v.path + ' ' + (v.ig_caption||'')).toLowerCase();
      if (!h.includes(q)) return false;
    }}
    return true;
  }});

  items = [...items].sort((a,b) => {{
    switch(sortKey) {{
      case 'date-asc':  return (a.date||'').localeCompare(b.date||'');
      case 'date-desc': return (b.date||'').localeCompare(a.date||'');
      case 'name-asc':  return a.name.localeCompare(b.name);
      case 'name-desc': return b.name.localeCompare(a.name);
      case 'size-desc': return (b.size_mb||0) - (a.size_mb||0);
      case 'dur-desc':  return (b.duration||0) - (a.duration||0);
      default: return 0;
    }}
  }});

  info.textContent = `Mostrant ${{items.length}} de ${{DATA.length}} vídeos`;

  if (!items.length) {{
    list.innerHTML = '';
    empty.style.display = '';
    return;
  }}
  empty.style.display = 'none';

  const frag = document.createDocumentFragment();
  items.forEach(v => {{
    const rl = resLabel(v);
    const rlClass = v.width >= 3840 ? 'tag--4k' : 'tag--res';
    const ig = v.ig_caption || '';
    const igTrunc = ig.length > 120 ? ig.slice(0,120)+'…' : ig;
    const disc = discName(v.path);

    const el = document.createElement('div');
    el.className = 'item';
    el.innerHTML = `
      <div class="item__main">
        <div class="item__name" title="${{v.name}}">${{escHtml(v.name)}}</div>
        <div class="item__path" title="${{v.path}}">${{escHtml(abbrevPath(v.path))}}</div>
        <div class="item__meta">
          ${{disc ? `<span class="tag tag--disc">${{escHtml(disc)}}</span>` : ''}}
          ${{v.year  ? `<span class="tag tag--year">${{v.year}}</span>` : ''}}
          ${{v.duration ? `<span class="tag tag--dur">${{durStr(v.duration)}}</span>` : ''}}
          ${{rl ? `<span class="tag ${{rlClass}}">${{rl}}${{v.res ? ' · '+v.res : ''}}</span>` : ''}}
          ${{v.size_mb ? `<span class="tag tag--size">${{v.size_mb}}MB</span>` : ''}}
          ${{ig ? `<span class="tag tag--ig">Instagram</span>` : ''}}
        </div>
        ${{ig ? `<div class="item__caption">${{escHtml(igTrunc)}}</div>` : ''}}
      </div>
      <div class="item__actions">
        <button class="copy-btn" data-path="${{escAttr(v.path)}}">Copiar ruta</button>
        <div class="item__date">${{v.date||''}}</div>
      </div>
    `;
    frag.appendChild(el);
  }});

  list.innerHTML = '';
  list.appendChild(frag);

  list.querySelectorAll('.copy-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      navigator.clipboard.writeText(btn.dataset.path).then(() => {{
        const orig = btn.textContent;
        btn.textContent = '✓ Copiada!';
        btn.classList.add('copied');
        setTimeout(() => {{ btn.textContent = orig; btn.classList.remove('copied'); }}, 2000);
      }});
    }});
  }});
}}

function escHtml(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}
function escAttr(s) {{
  return String(s).replace(/"/g,'&quot;');
}}

render();
</script>
</body>
</html>"""

    Path(output_path).write_text(html, encoding='utf-8')
    print(f"\n✅  Generat: {output_path}")
    print(f"   Obre-ho amb: open \"{output_path}\"")

def main():
    if len(sys.argv) < 2:
        print("Ús: python3 merge_catalogs.py catalog1.html catalog2.html ...")
        sys.exit(1)

    all_videos = []
    for path in sys.argv[1:]:
        videos = extract_data(path)
        all_videos.extend(videos)

    total_gb = round(sum(v.get('size_mb',0) for v in all_videos) / 1024, 1)
    print(f"\n📊  Total: {len(all_videos)} vídeos · {total_gb} GB")

    build_html(all_videos, 'catalog_total.html')

if __name__ == '__main__':
    main()

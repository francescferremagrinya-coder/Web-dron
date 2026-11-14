#!/usr/bin/env python3
"""
catalog_videos.py — Escàner i catalogador de vídeos per a Mac
=============================================================
Requisits:
    brew install ffmpeg          (per extreure durada i resolució)
    pip3 install tqdm            (opcional, barra de progrés)

Ús:
    python3 catalog_videos.py /Volumes/Disc1
    python3 catalog_videos.py /Volumes/Disc1 /Volumes/Disc2
    python3 catalog_videos.py /Volumes/Disc1 --instagram ~/Downloads/instagram-20240101.zip
    python3 catalog_videos.py /Volumes/Disc1 --out ~/Desktop/catalog.html

Genera: catalog.html (autocontingut, s'obre directament al navegador)
"""

import os, sys, json, subprocess, zipfile, argparse
from pathlib import Path
from datetime import datetime

VIDEO_EXTS = {
    '.mp4', '.mov', '.avi', '.m4v', '.mkv', '.mts', '.m2ts',
    '.wmv', '.flv', '.webm', '.3gp', '.mpg', '.mpeg', '.dv', '.mxf'
}

# ─── METADADES DE VÍDEO ────────────────────────────────────────────────────

def run_ffprobe(path):
    try:
        r = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json',
             '-show_streams', '-show_format', str(path)],
            capture_output=True, text=True, timeout=20
        )
        return json.loads(r.stdout)
    except Exception:
        return {}

def extract_meta(path):
    d = run_ffprobe(path)
    fmt   = d.get('format', {})
    tags  = fmt.get('tags', {})

    dur_s = fmt.get('duration')
    dur   = int(float(dur_s)) if dur_s else None

    ct = (tags.get('creation_time') or
          tags.get('com.apple.quicktime.creationdate') or
          tags.get('date') or '')
    if ct:
        ct = ct[:10]  # YYYY-MM-DD

    w = h = None
    for s in d.get('streams', []):
        if s.get('codec_type') == 'video':
            w = s.get('width')
            h = s.get('height')
            if not ct:
                st = (s.get('tags') or {}).get('creation_time', '')
                if st:
                    ct = st[:10]
            break

    return {
        'duration': dur,
        'width': w,
        'height': h,
        'meta_date': ct or None,
    }

def file_dates(path):
    st = path.stat()
    mtime = datetime.fromtimestamp(st.st_mtime)
    try:
        ctime = datetime.fromtimestamp(st.st_birthtime)   # Mac
    except AttributeError:
        ctime = datetime.fromtimestamp(st.st_ctime)
    return mtime, ctime

# ─── ESCANEIG ──────────────────────────────────────────────────────────────

def scan_drives(roots, verbose=True):
    videos = []
    for root_str in roots:
        root = Path(root_str).expanduser().resolve()
        if not root.exists():
            print(f"⚠️  No existeix: {root}", file=sys.stderr)
            continue
        print(f"\n📂  Escanejar: {root}")
        count = 0
        for p in root.rglob('*'):
            if p.suffix.lower() not in VIDEO_EXTS:
                continue
            if p.name.startswith('.') or '/.Spotlight-' in str(p):
                continue
            try:
                mtime, ctime = file_dates(p)
                meta = extract_meta(p)
                best_date = meta.get('meta_date') or ctime.strftime('%Y-%m-%d')
                size_mb = round(p.stat().st_size / 1_048_576, 1)
                res = f"{meta['width']}×{meta['height']}" if meta.get('width') else None

                videos.append({
                    'name': p.name,
                    'stem': p.stem,
                    'path': str(p),
                    'size_mb': size_mb,
                    'date': best_date,
                    'year': int(best_date[:4]),
                    'duration': meta.get('duration'),
                    'res': res,
                    'width': meta.get('width'),
                    'height': meta.get('height'),
                    'ig_caption': None,
                    'ig_date': None,
                })
                count += 1
                if verbose:
                    print(f"  [{count}] {p.name}")
            except Exception as e:
                if verbose:
                    print(f"  ✗ {p.name}: {e}")

        print(f"  → {count} vídeos trobats a {root.name}")
    return videos

# ─── INSTAGRAM ARCHIVE ─────────────────────────────────────────────────────

def load_instagram(zip_path, videos):
    """Creua l'arxiu d'Instagram amb els vídeos per data."""
    ig_map = {}   # date (YYYY-MM-DD) → caption

    try:
        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()

            # Localitza fitxers de posts/reels
            candidates = [
                n for n in names
                if n.endswith('.json') and any(k in n for k in
                   ['posts_1', 'posts_2', 'reels', 'videos', 'media'])
            ]

            for cname in candidates:
                try:
                    with z.open(cname) as f:
                        raw = json.load(f)
                except Exception:
                    continue

                items = raw if isinstance(raw, list) else raw.get('media', [])

                for item in items:
                    # Accepta format nou (llista d'items) i format antic
                    media_list = item.get('media', [item])
                    caption = item.get('title', '')

                    for m in media_list:
                        ts = m.get('creation_timestamp') or m.get('taken_at')
                        if not caption:
                            caption = m.get('title', '')
                        if ts:
                            d = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                            ig_map[d] = caption

        matched = 0
        for v in videos:
            if v['date'] in ig_map:
                v['ig_caption'] = ig_map[v['date']]
                v['ig_date'] = v['date']
                matched += 1

        print(f"\n📸  Instagram: {len(ig_map)} posts → {matched} vídeos coincidents per data")

    except zipfile.BadZipFile:
        print(f"⚠️  El fitxer {zip_path} no és un ZIP vàlid")
    except Exception as e:
        print(f"⚠️  Error llegint l'arxiu d'Instagram: {e}")

# ─── GENERACIÓ HTML ────────────────────────────────────────────────────────

def dur_str(s):
    if not s:
        return ''
    m, sec = divmod(int(s), 60)
    h, m = divmod(m, 60)
    return f'{h}:{m:02d}:{sec:02d}' if h else f'{m}:{sec:02d}'

def res_label(w):
    if not w:
        return ''
    if w >= 3840:
        return '4K'
    if w >= 1920:
        return 'FHD'
    if w >= 1280:
        return 'HD'
    return 'SD'

def build_html(videos, output_path):
    total_mb  = sum(v.get('size_mb') or 0 for v in videos)
    total_gb  = round(total_mb / 1024, 1)
    years     = sorted({v['year'] for v in videos if v.get('year')}, reverse=True)
    generated = datetime.now().strftime('%d/%m/%Y %H:%M')

    # Neteja i ordena
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
  --bg:#0e0c09;--bg2:#161210;--card:#1d1810;--card-h:#261f15;
  --gold:#d4a640;--gold-l:#f0c96a;--amber:#c97c2e;
  --white:#f5ede0;--grey:#7a6b58;--grey-l:#a89070;
  --border:rgba(212,166,64,.12);--border-h:rgba(212,166,64,.3);
  --rad:10px;--font:'Segoe UI',system-ui,sans-serif;
}}
body{{background:var(--bg);color:var(--white);font-family:var(--font);min-height:100vh;padding:0 0 60px}}
a{{color:var(--gold);text-decoration:none}}

/* ─── HEADER ─────────────────────────────────── */
.header{{background:var(--bg2);border-bottom:1px solid var(--border);padding:20px 24px;
  display:flex;align-items:center;gap:16px;flex-wrap:wrap}}
.header__title{{font-size:1.4rem;font-weight:700;color:var(--gold-l);flex:1;min-width:200px}}
.header__meta{{font-size:.8rem;color:var(--grey);line-height:1.6}}
.stats{{display:flex;gap:20px;flex-wrap:wrap}}
.stat{{text-align:center}}
.stat__n{{font-size:1.5rem;font-weight:700;color:var(--gold)}}
.stat__l{{font-size:.7rem;color:var(--grey);text-transform:uppercase;letter-spacing:.06em}}

/* ─── CONTROLS ───────────────────────────────── */
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

/* ─── RESULTS INFO ───────────────────────────── */
.results-info{{padding:10px 24px;font-size:.8rem;color:var(--grey)}}

/* ─── LLISTA ──────────────────────────────────── */
.list{{padding:0 24px}}
.item{{background:var(--card);border:1px solid var(--border);border-radius:var(--rad);
  padding:14px 16px;margin-bottom:8px;display:grid;
  grid-template-columns:1fr auto;gap:8px 16px;
  transition:.2s}}
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
.item__caption{{font-size:.8rem;color:var(--grey-l);margin-top:6px;
  font-style:italic;line-height:1.4;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.item__actions{{display:flex;flex-direction:column;gap:6px;align-items:flex-end;flex-shrink:0}}
.copy-btn{{background:transparent;border:1px solid var(--border);color:var(--grey);
  padding:4px 10px;border-radius:6px;font-size:.72rem;cursor:pointer;transition:.2s;white-space:nowrap}}
.copy-btn:hover{{border-color:var(--gold);color:var(--gold)}}
.copy-btn.copied{{border-color:#6dbf6d;color:#6dbf6d}}
.item__date{{font-size:.72rem;color:var(--grey);text-align:right}}

/* ─── EMPTY ───────────────────────────────────── */
.empty{{text-align:center;padding:60px 24px;color:var(--grey)}}
.empty__icon{{font-size:3rem;margin-bottom:16px;opacity:.4}}

/* ─── FOOTER ──────────────────────────────────── */
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
    <div class="header__title">Arxiu de Vídeos</div>
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

<div class="footer">Generat amb catalog_videos.py · {len(videos_out)} vídeos · {total_gb} GB</div>

<script>
const DATA = {data_js};

// ─── Stats inicials ────────────────────────────────────
const igCount = DATA.filter(v => v.ig_caption).length;
document.getElementById('s-total').textContent = DATA.length;
document.getElementById('s-ig').textContent    = igCount;

// ─── Year buttons ──────────────────────────────────────
const years = [...new Set(DATA.map(v => v.year).filter(Boolean))].sort((a,b)=>b-a);
const ybContainer = document.getElementById('year-btns');
years.forEach(y => {{
  const b = document.createElement('button');
  b.className = 'btn'; b.dataset.year = y; b.textContent = y;
  ybContainer.appendChild(b);
}});

// ─── State ────────────────────────────────────────────
let activeYear = 'all', activeRes = 'all', activeIg = 'all', sortKey = 'date-desc';

// ─── Filters ──────────────────────────────────────────
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
document.getElementById('sort').addEventListener('change', e => {{ sortKey = e.target.value; render(); }});
document.getElementById('q').addEventListener('input', render);

// ─── Helpers ──────────────────────────────────────────
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
function abbrevPath(p) {{
  const parts = p.split('/');
  if (parts.length <= 5) return p;
  return parts.slice(0,3).join('/') + '/…/' + parts.slice(-2).join('/');
}}

// ─── Render ───────────────────────────────────────────
function render() {{
  const q   = document.getElementById('q').value.trim().toLowerCase();
  const list = document.getElementById('list');
  const empty = document.getElementById('empty');
  const info  = document.getElementById('results-info');

  let items = DATA.filter(v => {{
    if (activeYear !== 'all' && v.year !== +activeYear) return false;
    if (activeRes !== 'all' && resCategory(v) !== activeRes) return false;
    if (activeIg === 'yes' && !v.ig_caption) return false;
    if (activeIg === 'no'  &&  v.ig_caption) return false;
    if (q) {{
      const haystack = (v.name + ' ' + v.path + ' ' + (v.ig_caption||'')).toLowerCase();
      if (!haystack.includes(q)) return false;
    }}
    return true;
  }});

  // Sort
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

    const el = document.createElement('div');
    el.className = 'item';
    el.innerHTML = `
      <div class="item__main">
        <div class="item__name" title="${{v.name}}">${{escHtml(v.name)}}</div>
        <div class="item__path" title="${{v.path}}">${{escHtml(abbrevPath(v.path))}}</div>
        <div class="item__meta">
          ${{v.year  ? `<span class="tag tag--year">${{v.year}}</span>` : ''}}
          ${{v.duration ? `<span class="tag tag--dur">${{durStr(v.duration)}}</span>` : ''}}
          ${{rl ? `<span class="tag ${{rlClass}}">${{rl}}${{v.width ? ' · '+v.res : ''}}</span>` : ''}}
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

# ─── MAIN ──────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description='Catalogador de vídeos — genera un catàleg HTML buscable'
    )
    p.add_argument('roots', nargs='+', help='Discs o carpetes a escanejar')
    p.add_argument('--instagram', metavar='ZIP', help='Ruta al ZIP de l\'arxiu d\'Instagram')
    p.add_argument('--out', metavar='PATH', default='catalog.html',
                   help='Fitxer de sortida (default: catalog.html)')
    p.add_argument('--quiet', action='store_true', help='Menys sortida per pantalla')
    args = p.parse_args()

    # Comprova ffprobe
    ffprobe_ok = subprocess.run(['which','ffprobe'], capture_output=True).returncode == 0
    if not ffprobe_ok:
        print("⚠️  ffprobe no trobat. Durades i resolucions no estaran disponibles.")
        print("   Instal·la-ho amb: brew install ffmpeg\n")

    videos = scan_drives(args.roots, verbose=not args.quiet)

    if not videos:
        print("No s'ha trobat cap vídeo.", file=sys.stderr)
        sys.exit(1)

    if args.instagram:
        load_instagram(args.instagram, videos)

    # Resum
    ig_count = sum(1 for v in videos if v.get('ig_caption'))
    total_gb = round(sum(v.get('size_mb',0) for v in videos) / 1024, 1)
    print(f"\n📊  Resum:")
    print(f"   {len(videos)} vídeos · {total_gb} GB total")
    if ig_count:
        print(f"   {ig_count} vídeos coincidents amb Instagram")

    build_html(videos, args.out)

if __name__ == '__main__':
    main()

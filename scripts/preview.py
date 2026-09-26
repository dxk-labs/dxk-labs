"""Live preview of the profile README, GitHub-style, with hot reload.

Run:  py scripts/preview.py      then open http://localhost:8787
- Editing README.md or anything in assets/ re-renders in place (scroll is kept).
- Editing scripts/build_assets.py regenerates the SVGs first.
- The "edit" button opens a side-by-side editor that autosaves README.md.
"""
import http.server
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8787
BUILD = ROOT / "scripts" / "build_assets.py"

PAGE = """<!doctype html>
<html lang="en" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Profile Preview</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@5/github-markdown.min.css">
<script src="https://cdn.jsdelivr.net/npm/marked@12/marked.min.js"></script>
<style>
  :root { --bg:#ffffff; --panel:#f6f8fa; --border:#d0d7de; --fg:#1f2328; --muted:#59636e; --ok:#1a7f37; }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#0d1117; --panel:#161b22; --border:#30363d; --fg:#f0f6fc; --muted:#8b949e; --ok:#3fb950; } }
  :root[data-theme="dark"] { --bg:#0d1117; --panel:#161b22; --border:#30363d; --fg:#f0f6fc; --muted:#8b949e; --ok:#3fb950; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--fg); font:14px -apple-system,'Segoe UI',Helvetica,Arial,sans-serif; }
  .bar { position:sticky; top:0; z-index:5; display:flex; gap:12px; align-items:center; padding:10px 16px;
         background:var(--panel); border-bottom:1px solid var(--border); }
  .bar b { font-weight:600; }
  .dot { width:8px; height:8px; border-radius:50%; background:var(--ok); transition:transform .2s; }
  .dot.flash { transform:scale(2.2); }
  .status { color:var(--muted); font-family:ui-monospace,Consolas,monospace; font-size:12px; flex:1; }
  .bar button { font:inherit; color:var(--fg); background:var(--bg); border:1px solid var(--border);
                border-radius:6px; padding:4px 10px; cursor:pointer; }
  .bar button[aria-pressed="true"] { border-color:var(--ok); }
  main { max-width:896px; margin:24px auto; padding:0 16px; }
  .frame { border:1px solid var(--border); border-radius:6px; padding:24px; background:var(--bg); }
  .frame-label { font-size:12px; color:var(--muted); margin:0 0 8px; font-family:ui-monospace,Consolas,monospace; }
  .markdown-body { background:transparent !important; }
  @media (max-width:600px) { .frame { padding:16px; } }
  .editor { display:none; }
  body.editing main { max-width:none; display:grid; grid-template-columns:minmax(0,1fr) minmax(0,896px); gap:20px; }
  body.editing .editor { display:flex; flex-direction:column; position:sticky; top:62px; height:calc(100vh - 86px); }
  .editor textarea { flex:1; width:100%; resize:none; padding:14px; border:1px solid var(--border); border-radius:6px;
                     background:var(--panel); color:var(--fg); font:13px/1.55 ui-monospace,Consolas,monospace; tab-size:2; }
  .editor textarea:focus { outline:2px solid var(--ok); outline-offset:-1px; }
  .hint { font-size:12px; color:var(--muted); margin:8px 0 0; }
  kbd { font:11px ui-monospace,Consolas,monospace; border:1px solid var(--border); border-radius:4px; padding:1px 5px; }
  #next { display:none; }
  body.editing #next { display:inline-block; }
  @media (max-width:900px) { body.editing main { grid-template-columns:minmax(0,1fr); } body.editing .editor { position:static; height:60vh; } }
</style>
</head>
<body>
<div class="bar">
  <span class="dot" id="dot"></span><b>Profile preview</b>
  <span class="status" id="status">connecting…</span>
  <button id="next" title="Jump to the next [PLACEHOLDER] (Ctrl+.)">next placeholder</button>
  <button id="edit" aria-pressed="false">edit</button>
  <button data-t="auto" aria-pressed="true">auto</button>
  <button data-t="light" aria-pressed="false">light</button>
  <button data-t="dark" aria-pressed="false">dark</button>
</div>
<main>
  <section class="editor">
    <textarea id="src" spellcheck="false" aria-label="README.md source"></textarea>
    <p class="hint">Autosaves to README.md as you type · <kbd>Ctrl</kbd>+<kbd>.</kbd> jumps to the next <code>[PLACEHOLDER]</code></p>
  </section>
  <div>
    <p class="frame-label">dxk-labs / README.md</p>
    <div class="frame"><article class="markdown-body" id="out"></article></div>
  </div>
</main>
<script>
const out = document.getElementById('out'), statusEl = document.getElementById('status'), dot = document.getElementById('dot');
let theme = 'auto', md = '', stamp = Date.now();
try { theme = localStorage.getItem('pv-theme') || 'auto'; } catch (e) {}

function effectiveDark() {
  return theme === 'dark' || (theme === 'auto' && matchMedia('(prefers-color-scheme: dark)').matches);
}
function bust(url) {
  return /^(https?:|mailto:|#|data:)/.test(url) ? url : url + (url.includes('?') ? '&' : '?') + 't=' + stamp;
}
function render() {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = effectiveDark() ? 'dark' : 'light';
  document.querySelectorAll('[data-t]').forEach(b => b.setAttribute('aria-pressed', b.dataset.t === theme));
  out.innerHTML = marked.parse(md, { gfm: true });
  // <picture> follows the OS theme; resolve it ourselves so the toggle works like GitHub's.
  const dark = effectiveDark();
  out.querySelectorAll('picture').forEach(p => {
    const img = p.querySelector('img'), src = p.querySelector('source[media*="dark"]');
    if (img && src && dark) img.setAttribute('src', src.getAttribute('srcset'));
    p.querySelectorAll('source').forEach(s => s.remove());
  });
  out.querySelectorAll('img').forEach(i => i.setAttribute('src', bust(i.getAttribute('src'))));
}
function note(msg) {
  statusEl.textContent = msg + ' · ' + new Date().toLocaleTimeString();
  dot.classList.add('flash'); setTimeout(() => dot.classList.remove('flash'), 250);
}
const src = document.getElementById('src');
let saved = null, saveTimer = 0, renderTimer = 0;

async function load(reason) {
  const text = await (await fetch('/README.md?t=' + Date.now())).text();
  if (text === saved && reason === 'README.md changed') return;  // our own autosave echoing back
  const y = scrollY;
  if (src.value === (saved ?? '') || src.value === '') { src.value = text; saved = text; }
  md = src.value;
  stamp = Date.now();
  render();
  scrollTo(0, y);
  note(reason);
}
src.addEventListener('input', () => {
  clearTimeout(renderTimer); renderTimer = setTimeout(() => { md = src.value; render(); }, 120);
  clearTimeout(saveTimer); statusEl.textContent = 'unsaved…';
  saveTimer = setTimeout(async () => {
    const body = src.value;
    const r = await fetch('/__save', { method: 'POST', body });
    if (r.ok) { saved = body; note('saved'); } else note('save failed');
  }, 600);
});
function nextPlaceholder() {
  const re = /\\[[A-Z][^\\]\\n]*\\]/g;
  re.lastIndex = src.selectionEnd;
  const m = re.exec(src.value) || (re.lastIndex = 0, re.exec(src.value));
  if (!m) { note('no placeholders left 🎉'); return; }
  src.focus(); src.setSelectionRange(m.index, m.index + m[0].length);
  const line = src.value.slice(0, m.index).split('\\n').length;
  src.scrollTop = Math.max(0, (line - 6) * parseFloat(getComputedStyle(src).lineHeight));
}
document.getElementById('next').onclick = nextPlaceholder;
addEventListener('keydown', e => { if (e.ctrlKey && e.key === '.') { e.preventDefault(); nextPlaceholder(); } });
const editBtn = document.getElementById('edit');
function setEditing(on) {
  document.body.classList.toggle('editing', on);
  editBtn.setAttribute('aria-pressed', on);
  try { localStorage.setItem('pv-edit', on ? '1' : ''); } catch (e) {}
}
editBtn.onclick = () => setEditing(!document.body.classList.contains('editing'));
try { setEditing(localStorage.getItem('pv-edit') === '1'); } catch (e) {}

document.querySelectorAll('[data-t]').forEach(b => b.onclick = () => {
  theme = b.dataset.t;
  try { localStorage.setItem('pv-theme', theme); } catch (e) {}
  render();
});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => theme === 'auto' && render());

const es = new EventSource('/__events');
es.onmessage = e => load(e.data);
es.onerror = () => { statusEl.textContent = 'disconnected — is preview.py still running?'; };
load('loaded');
</script>
</body>
</html>"""


def snapshot():
    files = [ROOT / "README.md", BUILD, *(ROOT / "assets").glob("*.svg")]
    return {f: f.stat().st_mtime for f in files if f.exists()}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/__events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            seen = snapshot()
            try:
                while True:
                    time.sleep(0.4)
                    now = snapshot()
                    if now == seen:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                        continue
                    changed = [f for f in now if now[f] != seen.get(f)]
                    reason = "README.md changed"
                    if BUILD in changed:
                        r = subprocess.run([sys.executable, str(BUILD)], capture_output=True, text=True)
                        reason = "SVGs rebuilt" if r.returncode == 0 else "build error: " + r.stderr.strip().splitlines()[-1]
                        print(r.stdout or r.stderr, end="")
                        now = snapshot()
                    elif all(f.suffix == ".svg" for f in changed):
                        reason = "assets changed"
                    seen = now
                    self.wfile.write(f"data: {reason}\n\n".encode())
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != "/__save":
            self.send_error(404)
            return
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        (ROOT / "README.md").write_bytes(body)
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"preview -> http://localhost:{PORT}", flush=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

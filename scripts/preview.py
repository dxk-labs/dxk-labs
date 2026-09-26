"""Live preview of the profile README, GitHub-style, with hot reload.

Run:  py scripts/preview.py      then open http://localhost:8787
- Editing README.md or anything in assets/ re-renders in place (scroll is kept).
- Editing scripts/build_assets.py regenerates the SVGs first.
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
</style>
</head>
<body>
<div class="bar">
  <span class="dot" id="dot"></span><b>Profile preview</b>
  <span class="status" id="status">connecting…</span>
  <button data-t="auto" aria-pressed="true">auto</button>
  <button data-t="light" aria-pressed="false">light</button>
  <button data-t="dark" aria-pressed="false">dark</button>
</div>
<main>
  <p class="frame-label">dxk-labs / README.md</p>
  <div class="frame"><article class="markdown-body" id="out"></article></div>
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
  document.querySelectorAll('.bar button').forEach(b => b.setAttribute('aria-pressed', b.dataset.t === theme));
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
async function load(reason) {
  const y = scrollY;
  md = await (await fetch('/README.md?t=' + Date.now())).text();
  stamp = Date.now();
  render();
  scrollTo(0, y);
  statusEl.textContent = reason + ' · ' + new Date().toLocaleTimeString();
  dot.classList.add('flash'); setTimeout(() => dot.classList.remove('flash'), 250);
}
document.querySelectorAll('.bar button').forEach(b => b.onclick = () => {
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


if __name__ == "__main__":
    print(f"preview -> http://localhost:{PORT}", flush=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()

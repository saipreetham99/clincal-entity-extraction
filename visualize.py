"""
Custom HTML visualization with document-level navigation.

Reads the JSONL output and generates an interactive HTML file with:
  - Sidebar listing all documents (click to switch)
  - Color-coded entity highlights in the clinical text
  - Click any entity to see its class, attributes, and source span
  - Summary stats bar at the top

Usage:
    python visualize.py                                  # default path
    python visualize.py --input output/clinical_extractions.jsonl
    python visualize.py --output my_visualization.html
"""

import argparse
import json
import html
from pathlib import Path
from collections import Counter


ENTITY_COLORS = {
    "medication": "#4A90D9",
    "dosage": "#D94A8C",
    "route": "#D9A04A",
    "frequency": "#4AD99B",
    "duration": "#9B4AD9",
    "diagnosis": "#D95A4A",
}

DEFAULT_COLOR = "#888888"


def load_documents(jsonl_path: str) -> list[dict]:
    docs = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


def get_extractions(doc: dict) -> list[dict]:
    return doc.get("extractions", [])


def get_text(doc: dict) -> str:
    return doc.get("text", "")


def highlight_text(text: str, extractions: list[dict]) -> str:
    """Build HTML with highlighted entity spans."""
    if not extractions:
        return f"<pre class='note-text'>{html.escape(text)}</pre>"

    # Build sorted, non-overlapping spans
    spans = []
    for i, ext in enumerate(extractions):
        ci = ext.get("char_interval", {})
        start = ci.get("start_pos")
        end = ci.get("end_pos")
        if start is not None and end is not None and start < end:
            spans.append((start, end, ext, i))

    # Sort by start position, then by longer span first
    spans.sort(key=lambda s: (s[0], -s[1]))

    # Remove overlaps — keep first (longest at same start)
    filtered = []
    last_end = -1
    for start, end, ext, idx in spans:
        if start >= last_end:
            filtered.append((start, end, ext, idx))
            last_end = end

    # Build highlighted HTML
    parts = []
    cursor = 0
    for start, end, ext, idx in filtered:
        # Text before this span
        if cursor < start:
            parts.append(html.escape(text[cursor:start]))

        cls = ext.get("extraction_class", "unknown")
        color = ENTITY_COLORS.get(cls, DEFAULT_COLOR)
        attrs = ext.get("attributes", {})
        attrs_str = html.escape(json.dumps(attrs)) if attrs else "{}"
        entity_text = html.escape(text[start:end])

        parts.append(
            f'<span class="entity" '
            f'data-class="{html.escape(cls)}" '
            f'data-attrs="{attrs_str}" '
            f'data-start="{start}" '
            f'data-end="{end}" '
            f'style="background-color: {color}22; '
            f"border-bottom: 2px solid {color}; "
            f'cursor: pointer; padding: 1px 2px; border-radius: 3px;" '
            f'onclick="showEntity(this)"'
            f">{entity_text}</span>"
        )
        cursor = end

    # Remaining text
    if cursor < len(text):
        parts.append(html.escape(text[cursor:]))

    return f"<pre class='note-text'>{''.join(parts)}</pre>"


def build_sidebar_items(docs: list[dict]) -> str:
    items = []
    for i, doc in enumerate(docs):
        text = get_text(doc)
        exts = get_extractions(doc)
        # Preview: first 60 chars
        preview = text[:60].replace("\n", " ").strip()
        if len(text) > 60:
            preview += "..."
        n_ent = len(exts)
        active = "active" if i == 0 else ""
        items.append(
            f'<div class="sidebar-item {active}" onclick="selectDoc({i})" id="sidebar-{i}">'
            f'<div class="sidebar-num">#{i + 1}</div>'
            f'<div class="sidebar-preview">{html.escape(preview)}</div>'
            f'<div class="sidebar-meta">{n_ent} entities · {len(text):,} chars</div>'
            f"</div>"
        )
    return "\n".join(items)


def build_doc_panels(docs: list[dict]) -> str:
    panels = []
    for i, doc in enumerate(docs):
        text = get_text(doc)
        exts = get_extractions(doc)
        display = "block" if i == 0 else "none"
        highlighted = highlight_text(text, exts)

        # Per-document entity counts
        counts = Counter(e.get("extraction_class", "unknown") for e in exts)
        tags_html = " ".join(
            f'<span class="doc-tag" style="background-color: {ENTITY_COLORS.get(cls, DEFAULT_COLOR)}33; '
            f"color: {ENTITY_COLORS.get(cls, DEFAULT_COLOR)}; "
            f'border: 1px solid {ENTITY_COLORS.get(cls, DEFAULT_COLOR)}66;">'
            f"{cls}: {count}</span>"
            for cls, count in counts.most_common()
        )

        panels.append(
            f'<div class="doc-panel" id="doc-{i}" style="display:{display}">'
            f'<div class="doc-header">'
            f'<h3>Document #{i + 1} <span class="doc-chars">({len(text):,} characters)</span></h3>'
            f'<div class="doc-tags">{tags_html}</div>'
            f"</div>"
            f'<div class="doc-body">{highlighted}</div>'
            f"</div>"
        )
    return "\n".join(panels)


def build_stats_bar(docs: list[dict]) -> str:
    total_ent = sum(len(get_extractions(d)) for d in docs)
    all_classes = Counter()
    for d in docs:
        for e in get_extractions(d):
            all_classes[e.get("extraction_class", "unknown")] += 1

    legend = " ".join(
        f'<span class="legend-item">'
        f'<span class="legend-dot" style="background:{ENTITY_COLORS.get(cls, DEFAULT_COLOR)}"></span>'
        f"{cls}: {count}</span>"
        for cls, count in all_classes.most_common()
    )

    return (
        f'<div class="stats-bar">'
        f"<strong>{len(docs)}</strong> documents · "
        f"<strong>{total_ent}</strong> entities · "
        f"{legend}"
        f"</div>"
    )


def generate_html(docs: list[dict]) -> str:
    stats_bar = build_stats_bar(docs)
    sidebar = build_sidebar_items(docs)
    panels = build_doc_panels(docs)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Clinical Entity Extraction — Visualization</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #1a1a1a; }}

  .stats-bar {{
    position: sticky; top: 0; z-index: 100;
    background: #1a1a2e; color: #e0e0e0; padding: 10px 20px;
    font-size: 14px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
  }}
  .legend-item {{ display: inline-flex; align-items: center; gap: 4px; margin-right: 8px; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}

  .layout {{ display: flex; height: calc(100vh - 42px); }}

  .sidebar {{
    width: 280px; min-width: 280px; background: #fff;
    border-right: 1px solid #ddd; overflow-y: auto; padding: 8px;
  }}
  .sidebar-item {{
    padding: 10px 12px; border-radius: 8px; cursor: pointer;
    margin-bottom: 4px; transition: background 0.15s;
  }}
  .sidebar-item:hover {{ background: #f0f4ff; }}
  .sidebar-item.active {{ background: #e3ecff; border-left: 3px solid #4A90D9; }}
  .sidebar-num {{ font-weight: 700; font-size: 12px; color: #4A90D9; margin-bottom: 2px; }}
  .sidebar-preview {{ font-size: 13px; color: #333; line-height: 1.4; }}
  .sidebar-meta {{ font-size: 11px; color: #888; margin-top: 4px; }}

  .main {{ flex: 1; overflow-y: auto; padding: 24px; }}

  .doc-panel {{ background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
  .doc-header {{ margin-bottom: 16px; }}
  .doc-header h3 {{ font-size: 18px; margin-bottom: 8px; }}
  .doc-chars {{ font-weight: 400; color: #888; font-size: 14px; }}
  .doc-tags {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .doc-tag {{
    font-size: 12px; font-weight: 600; padding: 3px 10px;
    border-radius: 12px; display: inline-block;
  }}

  .note-text {{
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    font-size: 13.5px; line-height: 1.8; white-space: pre-wrap;
    word-wrap: break-word; color: #2a2a2a;
  }}

  .entity:hover {{ filter: brightness(0.92); }}

  .inspector {{
    position: fixed; bottom: 20px; right: 20px;
    background: #1a1a2e; color: #e0e0e0; padding: 16px 20px;
    border-radius: 10px; font-size: 13px; min-width: 260px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25); display: none; z-index: 200;
    max-width: 400px;
  }}
  .inspector-title {{ font-weight: 700; font-size: 15px; margin-bottom: 8px; color: #fff; }}
  .inspector-row {{ margin-bottom: 4px; }}
  .inspector-label {{ color: #888; }}
  .inspector-close {{
    position: absolute; top: 8px; right: 12px; cursor: pointer;
    color: #666; font-size: 18px;
  }}
  .inspector-close:hover {{ color: #fff; }}

  .nav-bar {{
    display: flex; align-items: center; gap: 8px;
    padding: 12px 0; margin-bottom: 16px;
  }}
  .nav-btn {{
    padding: 6px 16px; border-radius: 6px; border: 1px solid #ccc;
    background: #fff; cursor: pointer; font-size: 13px; font-weight: 600;
  }}
  .nav-btn:hover {{ background: #f0f4ff; }}
  .nav-btn:disabled {{ opacity: 0.4; cursor: default; }}
  .nav-info {{ font-size: 13px; color: #666; }}
</style>
</head>
<body>

{stats_bar}

<div class="layout">
  <div class="sidebar" id="sidebar">
    {sidebar}
  </div>
  <div class="main" id="main">
    <div class="nav-bar">
      <button class="nav-btn" onclick="prevDoc()" id="prev-btn">← Previous</button>
      <span class="nav-info" id="nav-info">Document 1 of {len(docs)}</span>
      <button class="nav-btn" onclick="nextDoc()" id="next-btn">Next →</button>
    </div>
    {panels}
  </div>
</div>

<div class="inspector" id="inspector">
  <span class="inspector-close" onclick="hideInspector()">×</span>
  <div class="inspector-title" id="insp-text"></div>
  <div class="inspector-row"><span class="inspector-label">Class: </span><span id="insp-class"></span></div>
  <div class="inspector-row"><span class="inspector-label">Span: </span><span id="insp-span"></span></div>
  <div class="inspector-row"><span class="inspector-label">Attributes: </span><span id="insp-attrs"></span></div>
</div>

<script>
let currentDoc = 0;
const totalDocs = {len(docs)};

function selectDoc(idx) {{
  document.getElementById('doc-' + currentDoc).style.display = 'none';
  document.getElementById('sidebar-' + currentDoc).classList.remove('active');
  currentDoc = idx;
  document.getElementById('doc-' + currentDoc).style.display = 'block';
  document.getElementById('sidebar-' + currentDoc).classList.add('active');
  document.getElementById('sidebar-' + currentDoc).scrollIntoView({{ block: 'nearest' }});
  document.getElementById('nav-info').textContent = 'Document ' + (idx + 1) + ' of ' + totalDocs;
  document.getElementById('prev-btn').disabled = idx === 0;
  document.getElementById('next-btn').disabled = idx === totalDocs - 1;
  hideInspector();
}}

function prevDoc() {{ if (currentDoc > 0) selectDoc(currentDoc - 1); }}
function nextDoc() {{ if (currentDoc < totalDocs - 1) selectDoc(currentDoc + 1); }}

function showEntity(el) {{
  document.getElementById('insp-text').textContent = el.textContent;
  document.getElementById('insp-class').textContent = el.dataset.class;
  document.getElementById('insp-span').textContent = el.dataset.start + '–' + el.dataset.end;
  try {{
    const attrs = JSON.parse(el.dataset.attrs);
    const parts = Object.entries(attrs).map(([k,v]) => k + ': ' + v);
    document.getElementById('insp-attrs').textContent = parts.length ? parts.join(', ') : 'none';
  }} catch(e) {{
    document.getElementById('insp-attrs').textContent = el.dataset.attrs;
  }}
  document.getElementById('inspector').style.display = 'block';
}}

function hideInspector() {{ document.getElementById('inspector').style.display = 'none'; }}

document.addEventListener('keydown', function(e) {{
  if (e.key === 'ArrowLeft') prevDoc();
  if (e.key === 'ArrowRight') nextDoc();
  if (e.key === 'Escape') hideInspector();
}});

// Init
selectDoc(0);
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Generate custom entity visualization")
    parser.add_argument(
        "--input", default="output/clinical_extractions.jsonl", help="JSONL input path"
    )
    parser.add_argument(
        "--output", default="output/visualization.html", help="HTML output path"
    )
    args = parser.parse_args()

    docs = load_documents(args.input)
    print(f"Loaded {len(docs)} documents from {args.input}")

    html_content = generate_html(docs)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Visualization saved to {args.output}")


if __name__ == "__main__":
    main()

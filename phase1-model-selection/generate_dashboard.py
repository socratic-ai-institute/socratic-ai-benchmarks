#!/usr/bin/env python3
"""
Generate a static HTML dashboard from one or more benchmark result files.

Usage:
  python generate_dashboard.py                             # auto-detect latest comparison_results_*.json
  python generate_dashboard.py comparison_results_*.json   # specify one or more files

Outputs:
  dashboard.html in the current directory (phase1-model-selection)

Notes:
  - Works entirely offline once you have JSON files.
  - Uses Chart.js via CDN in the generated HTML (loaded by your browser).
"""

import argparse
import glob
import json
import os
from datetime import datetime
from typing import Any, Dict, List


def load_runs(files: List[str]) -> List[Dict[str, Any]]:
    runs: List[Dict[str, Any]] = []
    for path in files:
        try:
            with open(path, "r") as f:
                data = json.load(f)
                runs.append({"path": os.path.basename(path), "data": data})
        except Exception as e:
            print(f"⚠️  Skipping {path}: {e}")
    return runs


def autodetect_latest() -> List[str]:
    candidates = sorted(glob.glob("comparison_results_*.json"))
    return candidates[-1:] if candidates else []


def model_rows_from_run(run: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = run["data"].get("results", [])
    # Sort by avg_quality desc
    results_sorted = sorted(
        results, key=lambda r: r.get("avg_quality", 0), reverse=True
    )
    rows = []
    for r in results_sorted:
        rows.append(
            {
                "model_id": r.get("model_id", ""),
                "model_name": r.get("model_name", r.get("model_id", "")),
                "avg_quality": round(float(r.get("avg_quality", 0)), 3),
                "avg_latency_ms": round(float(r.get("avg_latency_ms", 0)), 1),
                "success_rate": round(float(r.get("success_rate", 0)) * 100, 1),
                "successful": r.get("successful", 0),
                "total_scenarios": r.get("total_scenarios", 0),
                "criteria_scores": r.get("criteria_scores", {}),
            }
        )
    return rows


def select_top_model(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return rows[0] if rows else {}


def escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_html(runs: List[Dict[str, Any]]) -> str:
    generated = datetime.now().isoformat(timespec="seconds")

    # Prepare JS data structures for charts
    run_blocks = []
    for run in runs:
        meta = run["data"].get("metadata", {})
        rows = model_rows_from_run(run)
        labels = [r["model_name"] for r in rows]
        qualities = [r["avg_quality"] for r in rows]
        latencies = [r["avg_latency_ms"] for r in rows]
        success = [r["success_rate"] for r in rows]
        crit = [r.get("criteria_scores", {}) for r in rows]
        crit_keys = [
            "open_ended",
            "probing",
            "builds_on_previous",
            "age_appropriate",
            "content_relevant",
        ]
        crit_series = {
            k: [round(float(c.get(k, 0)), 3) for c in crit] for k in crit_keys
        }

        run_blocks.append(
            {
                "title": f"Run: {escape_html(run['path'])}",
                "meta": meta,
                "rows": rows,
                "labels": labels,
                "qualities": qualities,
                "latencies": latencies,
                "success": success,
                "crit_keys": crit_keys,
                "crit_series": crit_series,
            }
        )

    html = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Socratic AI Benchmarks — Dashboard</title>
  <style>
    :root {{ --bg:#0b1020; --panel:#141a32; --text:#e6e9f5; --muted:#a7b0c5; --accent:#6dd3fb; --ok:#43d17a; --warn:#ffd166; --bad:#ef476f; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji','Segoe UI Emoji', 'Segoe UI Symbol'; background:var(--bg); color:var(--text); }}
    header {{ padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.06); display:flex; align-items:center; justify-content:space-between; }}
    h1 {{ margin:0; font-size: 20px; }}
    .meta {{ color:var(--muted); font-size: 13px; }}
    .container {{ padding: 20px; max-width: 1200px; margin: 0 auto; }}
    .grid {{ display:grid; grid-template-columns: repeat(12, 1fr); gap:16px; }}
    .card {{ background: var(--panel); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 16px; }}
    .span-12 {{ grid-column: span 12; }}
    .span-6 {{ grid-column: span 6; }}
    .span-4 {{ grid-column: span 4; }}
    table {{ width:100%; border-collapse: collapse; }}
    th, td {{ padding: 10px 8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.06); font-size: 14px; }}
    th {{ color: var(--muted); font-weight: 600; font-size:12px; text-transform: uppercase; letter-spacing: 0.04em; }}
    .badge {{ display:inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; color:#0a0f1f; }}
    .ok {{ background: var(--ok); }} .warn {{ background: var(--warn); }} .bad {{ background: var(--bad); }}
    .pill {{ font-size: 12px; color: var(--muted); padding: 2px 8px; border: 1px solid rgba(255,255,255,0.12); border-radius: 999px; }}
    .run-header {{ display:flex; gap:8px; align-items:center; justify-content:space-between; flex-wrap:wrap; }}
    .run-meta {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; }}
    .footer {{ color: var(--muted); font-size: 12px; margin-top: 24px; }}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <script>window.__RUNS__ = __RUNS_JSON__;</script>
  <script>
    function fmtLatency(ms) {{ return Math.round(ms) + ' ms'; }}
    function qualityBadge(q) {{
      if (q >= 0.85) return '<span class="badge ok">' + q.toFixed(3) + '</span>';
      if (q >= 0.7) return '<span class="badge warn">' + q.toFixed(3) + '</span>';
      return '<span class="badge bad">' + q.toFixed(3) + '</span>';
    }}
    function successPill(s) {{
      const cls = s >= 99 ? 'ok' : (s >= 90 ? 'warn' : 'bad');
      return '<span class="pill">Success: <span class="' + cls + ' badge">' + s.toFixed(1) + '%</span></span>';
    }}
    function renderTables() {{
      const root = document.getElementById('runs');
      const runs = window.__RUNS__;
      runs.forEach((run, idx) => {{
        const top = run.rows[0] || {{}};
        const meta = run.meta || {{}};
        const section = document.createElement('section');
        section.className = 'grid';
        section.innerHTML = `
          <div class="span-12 card">
            <div class="run-header">
              <div>
                <h2 style="margin:0 0 4px 0; font-size:16px;">${run.title}</h2>
                <div class="meta">Timestamp: ${meta.timestamp || '—'} · Profile: ${meta.aws_profile || '—'} · Region: ${meta.aws_region || '—'} · Scenarios: ${meta.total_scenarios || '—'} · Models: ${meta.models_tested || '—'}</div>
              </div>
              <div class="run-meta">
                <span class="pill">Top Model: <b>${(top.model_name || '—')}</b></span>
                <span class="pill">Top Quality: ${(top.avg_quality ?? 0).toFixed(3)}</span>
                <span class="pill">Top Latency: ${fmtLatency(top.avg_latency_ms || 0)}</span>
              </div>
            </div>
          </div>

          <div class="span-6 card">
            <h3 style="margin:0 0 8px 0; font-size:14px; color:var(--muted);">Ranking</h3>
            <table>
              <thead><tr>
                <th>#</th><th>Model</th><th>Quality</th><th>Latency</th><th>Success</th>
              </tr></thead>
              <tbody>
                ${run.rows.map((r,i) => `
                  <tr>
                    <td>${i+1}</td>
                    <td>${r.model_name}</td>
                    <td>${qualityBadge(r.avg_quality)}</td>
                    <td>${fmtLatency(r.avg_latency_ms)}</td>
                    <td>${successPill(r.success_rate)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>

          <div class="span-6 card">
            <h3 style="margin:0 0 8px 0; font-size:14px; color:var(--muted);">Quality by Model</h3>
            <canvas id="qbar_${idx}"></canvas>
          </div>

          <div class="span-6 card">
            <h3 style="margin:0 0 8px 0; font-size:14px; color:var(--muted);">Quality vs Latency</h3>
            <canvas id="scatter_${idx}"></canvas>
          </div>

          <div class="span-6 card">
            <h3 style="margin:0 0 8px 0; font-size:14px; color:var(--muted);">Criteria Breakdown</h3>
            <canvas id="crit_${idx}"></canvas>
          </div>
        `;
        root.appendChild(section);

        // Bar: Quality by Model
        new Chart(document.getElementById('qbar_'+idx).getContext('2d'), {{
          type: 'bar',
          data: {{
            labels: run.labels,
            datasets: [{{
              label: 'Avg Quality',
              data: run.qualities,
              backgroundColor: 'rgba(109, 211, 251, 0.6)',
              borderColor: 'rgba(109, 211, 251, 1)',
              borderWidth: 1,
            }}]
          }},
          options: {{
            scales: {{ y: {{ beginAtZero: true, max: 1 }} }}
          }}
        }});

        // Scatter: Quality vs Latency
        new Chart(document.getElementById('scatter_'+idx).getContext('2d'), {{
          type: 'scatter',
          data: {{
            datasets: [{{
              label: 'Models',
              data: run.labels.map((label, i) => ({{ x: run.latencies[i], y: run.qualities[i], label }})),
              backgroundColor: 'rgba(67, 209, 122, 0.7)'
            }}]
          }},
          options: {{
            parsing: false,
            plugins: {{
              tooltip: {{
                callbacks: {{
                  label: (ctx) => `${{ctx.raw.label}} — Q:${{ctx.raw.y.toFixed(3)}} · L:${{Math.round(ctx.raw.x)}}ms`
                }}
              }}
            }},
            scales: {{ x: {{ title: {{ display:true, text:'Latency (ms)'}} }}, y: {{ beginAtZero:true, max:1, title: {{ display:true, text:'Quality'}} }} }}
          }}
        }});

        // Stacked bars: Criteria Breakdown
        const critKeys = run.crit_keys;
        const colors = ['#7ad7f0','#6dd3fb','#a9e5bb','#ffe19c','#f7a1be'];
        new Chart(document.getElementById('crit_'+idx).getContext('2d'), {{
          type: 'bar',
          data: {{
            labels: run.labels,
            datasets: critKeys.map((k, i) => ({{
              label: k,
              data: run.crit_series[k],
              backgroundColor: colors[i % colors.length]
            }}))
          }},
          options: {{
            scales: {{
              x: {{ stacked: true }},
              y: {{ stacked: true, beginAtZero: true, max: 1 }}
            }}
          }}
        }});
      }});
    }
    window.addEventListener('DOMContentLoaded', renderTables);
  </script>
</head>
<body>
  <header>
    <h1>Socratic AI Benchmarks — Phase 1 Dashboard</h1>
    <div class="meta">Generated: __GENERATED__</div>
  </header>
  <div class="container">
    <div id="runs" class="grid"></div>
    <div class="footer">Static report generated from comparison_results_*.json. Adjust weights and deeper drill-down can be added in the interactive app.</div>
  </div>
</body>
</html>
"""
    html = html.replace("__RUNS_JSON__", json.dumps(run_blocks))
    html = html.replace("__GENERATED__", generated)
    return html


def main():
    parser = argparse.ArgumentParser(
        description="Generate static dashboard from benchmark results"
    )
    parser.add_argument("files", nargs="*", help="comparison_results_*.json files")
    parser.add_argument(
        "-o",
        "--output",
        default="dashboard.html",
        help="Output HTML file (default: dashboard.html in input file directory)",
    )
    args = parser.parse_args()

    files = args.files or autodetect_latest()
    if not files:
        print(
            "❌ No comparison_results_*.json found. Run benchmark.py first or pass files explicitly."
        )
        return

    runs = load_runs(files)
    if not runs:
        print("❌ No valid runs loaded.")
        return

    # Determine default output location if user didn't specify a path
    output_path = args.output
    if args.output == "dashboard.html":
        base_dir = (
            os.path.dirname(os.path.abspath(files[0]))
            if files
            else os.path.dirname(os.path.abspath(__file__))
        )
        output_path = os.path.join(base_dir, "dashboard.html")

    html = build_html(runs)
    with open(output_path, "w") as f:
        f.write(html)
    print(f"✅ Dashboard generated: {output_path}")


if __name__ == "__main__":
    main()

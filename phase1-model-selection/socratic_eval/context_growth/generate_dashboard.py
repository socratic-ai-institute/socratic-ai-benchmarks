"""
Dashboard Generator for Context Growth Evaluation Results

Creates an interactive HTML dashboard for comparing reasoning vs. non-reasoning models.

Usage:
    python generate_dashboard.py results.json --output dashboard.html
"""

import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional


def generate_html_dashboard(results: Dict, output_path: str = "context_growth_dashboard.html"):
    """
    Generate interactive HTML dashboard from evaluation results.

    Args:
        results: Results dict from context_growth evaluation
        output_path: Path to save HTML file
    """

    metadata = results.get("metadata", {})
    summary = results.get("summary", {})
    scenario_results = results.get("scenario_results", [])

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Context Growth Evaluation Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f7fa;
            color: #2d3748;
            line-height: 1.6;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .metadata {{
            background: #edf2f7;
            padding: 20px 40px;
            border-bottom: 2px solid #cbd5e0;
        }}

        .metadata-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}

        .metadata-item {{
            display: flex;
            flex-direction: column;
        }}

        .metadata-item label {{
            font-size: 0.85em;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}

        .metadata-item value {{
            font-size: 1.1em;
            font-weight: 600;
            color: #2d3748;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 50px;
        }}

        .section-title {{
            font-size: 1.8em;
            color: #2d3748;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        .model-comparison {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}

        .model-card {{
            background: #f7fafc;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            padding: 25px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .model-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.1);
        }}

        .model-card h3 {{
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #667eea;
        }}

        .metric-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #e2e8f0;
        }}

        .metric-row:last-child {{
            border-bottom: none;
        }}

        .metric-label {{
            font-size: 0.95em;
            color: #4a5568;
        }}

        .metric-value {{
            font-size: 1.2em;
            font-weight: 700;
            color: #2d3748;
        }}

        .metric-bar {{
            width: 100%;
            height: 8px;
            background: #e2e8f0;
            border-radius: 4px;
            margin-top: 5px;
            overflow: hidden;
        }}

        .metric-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
            transition: width 0.5s ease;
        }}

        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 40px;
        }}

        .scenario-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}

        .scenario-table th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}

        .scenario-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
        }}

        .scenario-table tr:hover {{
            background: #f7fafc;
        }}

        .score-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }}

        .score-excellent {{ background: #48bb78; color: white; }}
        .score-good {{ background: #38b2ac; color: white; }}
        .score-fair {{ background: #ed8936; color: white; }}
        .score-poor {{ background: #f56565; color: white; }}

        .test-type-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .badge-consistency {{ background: #bee3f8; color: #2c5282; }}
        .badge-complexity {{ background: #fbd38d; color: #7c2d12; }}
        .badge-ambiguity {{ background: #c6f6d5; color: #22543d; }}
        .badge-interrupt_redirect {{ background: #fed7d7; color: #742a2a; }}
        .badge-chain_of_thought {{ background: #e9d8fd; color: #44337a; }}

        .winner-banner {{
            background: linear-gradient(135deg, #48bb78 0%, #38b2ac 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 40px;
        }}

        .winner-banner h2 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}

        .winner-banner p {{
            font-size: 1.2em;
            opacity: 0.95;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Context Growth Evaluation</h1>
            <p>Reasoning vs. Non-Reasoning Models in Socratic Use Cases</p>
        </div>

        <div class="metadata">
            <div class="metadata-grid">
                <div class="metadata-item">
                    <label>Timestamp</label>
                    <value>{metadata.get('timestamp', 'N/A')}</value>
                </div>
                <div class="metadata-item">
                    <label>Models Tested</label>
                    <value>{len(metadata.get('models', []))}</value>
                </div>
                <div class="metadata-item">
                    <label>Scenarios</label>
                    <value>{metadata.get('num_scenarios', 0)}</value>
                </div>
                <div class="metadata-item">
                    <label>AWS Region</label>
                    <value>{metadata.get('aws_region', 'N/A')}</value>
                </div>
            </div>
        </div>

        <div class="content">
            {_generate_winner_section(summary)}

            {_generate_model_comparison_section(summary)}

            {_generate_radar_chart_section(summary)}

            {_generate_test_type_section(summary)}

            {_generate_detailed_results_section(scenario_results)}
        </div>
    </div>

    <script>
        // Initialize charts
        {_generate_chart_scripts(summary, scenario_results)}
    </script>
</body>
</html>
    """

    with open(output_path, "w") as f:
        f.write(html)

    print(f"Dashboard generated: {output_path}")


def _generate_winner_section(summary: Dict) -> str:
    """Generate winner announcement section."""

    by_model = summary.get("by_model", {})

    if not by_model:
        return ""

    # Find best model
    best_model = None
    best_score = 0

    for model_id, scores in by_model.items():
        overall = scores.get("overall_mean", 0)
        if overall > best_score:
            best_score = overall
            best_model = model_id

    if not best_model:
        return ""

    return f"""
    <div class="winner-banner">
        <h2>🏆 Winner: {best_model}</h2>
        <p>Overall Score: {best_score:.2f}/10</p>
    </div>
    """


def _generate_model_comparison_section(summary: Dict) -> str:
    """Generate model comparison cards."""

    by_model = summary.get("by_model", {})

    if not by_model:
        return ""

    cards_html = ""

    for model_id, scores in by_model.items():
        metrics = [
            ("Overall", scores.get("overall_mean", 0), 10),
            ("Persistence", scores.get("persistence_mean", 0), 10),
            ("Cognitive Depth", scores.get("cognitive_depth_mean", 0), 10),
            ("Context Adaptability", scores.get("context_adaptability_mean", 0), 10),
            ("Resistance to Drift", scores.get("resistance_to_drift_mean", 0), 10),
            ("Memory Preservation", scores.get("memory_preservation_mean", 0), 10),
        ]

        # Add answer quality metrics if available
        has_answer_quality = 'avg_composite_quality_mean' in scores
        if has_answer_quality:
            metrics.append(("─── Answer Quality ───", None, None))  # Separator
            metrics.append(("Composite Quality", scores.get("avg_composite_quality_mean", 0), 1.0))
            metrics.append(("Directional Socraticism", scores.get("avg_directional_socraticism_mean", 0), 1.0))
            metrics.append(("Socratic Endings", scores.get("pct_socratic_endings_mean", 0), 100))
            metrics.append(("Avg Verbosity (tokens)", scores.get("avg_verbosity_tokens_mean", 0), 200))

        metrics_html = ""
        for metric_data in metrics:
            if len(metric_data) == 3:
                label, value, max_value = metric_data

                # Skip separator rendering as metric, render as text
                if value is None:
                    metrics_html += f"""
                    <div style="margin-top: 15px; margin-bottom: 10px; font-weight: bold; color: #667eea; font-size: 0.9em;">
                        {label}
                    </div>
                    """
                    continue

                bar_width = (value / max_value) * 100 if max_value > 0 else 0

                # Format value based on type
                if max_value == 100:  # Percentage
                    value_str = f"{value:.1f}%"
                elif max_value == 1.0:  # 0.00-1.00 scale
                    value_str = f"{value:.2f}"
                elif max_value == 200:  # Token count
                    value_str = f"{value:.0f}"
                else:  # 0-10 scale
                    value_str = f"{value:.2f}"

                metrics_html += f"""
                <div class="metric-row">
                    <span class="metric-label">{label}</span>
                    <span class="metric-value">{value_str}</span>
                </div>
                <div class="metric-bar">
                    <div class="metric-bar-fill" style="width: {bar_width}%"></div>
                </div>
                """

        cards_html += f"""
        <div class="model-card">
            <h3>{model_id}</h3>
            {metrics_html}
        </div>
        """

    return f"""
    <div class="section">
        <h2 class="section-title">Model Comparison</h2>
        <div class="model-comparison">
            {cards_html}
        </div>
    </div>
    """


def _generate_radar_chart_section(summary: Dict) -> str:
    """Generate radar chart section."""

    return """
    <div class="section">
        <h2 class="section-title">Metric Comparison</h2>
        <div class="chart-container">
            <canvas id="radarChart"></canvas>
        </div>
    </div>
    """


def _generate_test_type_section(summary: Dict) -> str:
    """Generate test type breakdown."""

    by_test_type = summary.get("by_test_type", {})

    if not by_test_type:
        return ""

    return """
    <div class="section">
        <h2 class="section-title">Performance by Test Type</h2>
        <div class="chart-container">
            <canvas id="testTypeChart"></canvas>
        </div>
    </div>
    """


def _generate_detailed_results_section(scenario_results: List[Dict]) -> str:
    """Generate detailed scenario results table."""

    rows_html = ""

    for scenario in scenario_results:
        scenario_id = scenario.get("scenario_id", "N/A")
        scenario_name = scenario.get("scenario_name", "N/A")
        test_type = scenario.get("test_type", "unknown")

        for model_result in scenario.get("model_results", []):
            if model_result.get("status") != "success":
                continue

            model_id = model_result.get("model_id", "N/A")
            overall_score = model_result.get("overall_score", {})
            overall = overall_score.get("overall", 0)

            # Score badge class
            if overall >= 8:
                badge_class = "score-excellent"
            elif overall >= 6:
                badge_class = "score-good"
            elif overall >= 4:
                badge_class = "score-fair"
            else:
                badge_class = "score-poor"

            rows_html += f"""
            <tr>
                <td><span class="test-type-badge badge-{test_type}">{test_type}</span></td>
                <td>{scenario_name}</td>
                <td>{model_id}</td>
                <td><span class="score-badge {badge_class}">{overall:.2f}/10</span></td>
                <td>{overall_score.get('persistence', 0):.2f}</td>
                <td>{overall_score.get('cognitive_depth', 0):.2f}</td>
                <td>{overall_score.get('context_adaptability', 0):.2f}</td>
            </tr>
            """

    return f"""
    <div class="section">
        <h2 class="section-title">Detailed Results</h2>
        <table class="scenario-table">
            <thead>
                <tr>
                    <th>Test Type</th>
                    <th>Scenario</th>
                    <th>Model</th>
                    <th>Overall</th>
                    <th>Persistence</th>
                    <th>Cognitive Depth</th>
                    <th>Context Adapt.</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """


def _generate_chart_scripts(summary: Dict, scenario_results: List[Dict]) -> str:
    """Generate Chart.js scripts."""

    by_model = summary.get("by_model", {})
    by_test_type = summary.get("by_test_type", {})

    # Prepare radar chart data
    models = list(by_model.keys())
    metrics = ["persistence", "cognitive_depth", "context_adaptability",
               "resistance_to_drift", "memory_preservation"]

    datasets = []
    colors = [
        "rgba(102, 126, 234, 0.6)",
        "rgba(237, 100, 166, 0.6)",
        "rgba(72, 187, 120, 0.6)",
        "rgba(237, 137, 54, 0.6)",
    ]

    for i, model_id in enumerate(models):
        scores = by_model[model_id]
        data = [scores.get(f"{metric}_mean", 0) for metric in metrics]

        datasets.append({
            "label": model_id,
            "data": data,
            "backgroundColor": colors[i % len(colors)],
            "borderColor": colors[i % len(colors)].replace("0.6", "1"),
            "borderWidth": 2
        })

    radar_data = {
        "labels": ["Persistence", "Cognitive Depth", "Context Adaptability",
                   "Resistance to Drift", "Memory Preservation"],
        "datasets": datasets
    }

    # Prepare test type chart data
    test_types = list(by_test_type.keys())
    test_type_scores = [by_test_type[tt].get("overall_mean", 0) for tt in test_types]

    test_type_data = {
        "labels": [tt.replace("_", " ").title() for tt in test_types],
        "datasets": [{
            "label": "Average Score",
            "data": test_type_scores,
            "backgroundColor": colors[:len(test_types)]
        }]
    }

    return f"""
        // Radar Chart
        const radarCtx = document.getElementById('radarChart').getContext('2d');
        new Chart(radarCtx, {{
            type: 'radar',
            data: {json.dumps(radar_data)},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{
                        min: 0,
                        max: 10,
                        ticks: {{
                            stepSize: 2
                        }}
                    }}
                }}
            }}
        }});

        // Test Type Chart
        const testTypeCtx = document.getElementById('testTypeChart').getContext('2d');
        new Chart(testTypeCtx, {{
            type: 'bar',
            data: {json.dumps(test_type_data)},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        min: 0,
                        max: 10,
                        ticks: {{
                            stepSize: 2
                        }}
                    }}
                }}
            }}
        }});
    """


def main():
    """CLI entry point."""

    parser = argparse.ArgumentParser(
        description="Generate HTML dashboard from context growth evaluation results"
    )

    parser.add_argument(
        "results_file",
        type=str,
        help="Path to results JSON file"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="context_growth_dashboard.html",
        help="Output HTML file path"
    )

    args = parser.parse_args()

    # Load results
    with open(args.results_file, "r") as f:
        results = json.load(f)

    # Generate dashboard
    generate_html_dashboard(results, args.output)


if __name__ == "__main__":
    main()

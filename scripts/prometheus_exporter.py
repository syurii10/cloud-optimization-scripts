#!/usr/bin/env python3
"""
Prometheus Metrics Exporter для TOPSIS Optimization System
Експортує метрики оптимізації в Prometheus format
"""

import json
from pathlib import Path
from typing import Dict
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse


class PrometheusMetrics:
    """Generator для Prometheus metrics"""

    def __init__(self, results_dir: str = "results/data"):
        self.results_dir = Path(results_dir)

    def load_results(self) -> Dict:
        """Завантажує всі результати"""
        results = {}

        # Optimization results
        opt_file = self.results_dir / "optimization_results.json"
        if opt_file.exists():
            with open(opt_file, 'r', encoding='utf-8') as f:
                results['optimization'] = json.load(f)

        # Monte Carlo results
        mc_file = self.results_dir / "monte_carlo_results.json"
        if mc_file.exists():
            with open(mc_file, 'r', encoding='utf-8') as f:
                results['monte_carlo'] = json.load(f)

        # Cost estimation
        cost_file = self.results_dir / "cost_estimate.json"
        if cost_file.exists():
            with open(cost_file, 'r', encoding='utf-8') as f:
                results['cost'] = json.load(f)

        return results

    def generate_metrics(self) -> str:
        """Генерує Prometheus metrics"""
        results = self.load_results()
        metrics = []

        # Header
        metrics.append("# HELP topsis_score TOPSIS optimization score (0-1)")
        metrics.append("# TYPE topsis_score gauge")

        # TOPSIS scores
        if 'optimization' in results:
            for result in results['optimization']['results']:
                instance = result['alternative']
                score = result['score']
                rank = result['rank']

                metrics.append(
                    f'topsis_score{{instance="{instance}",rank="{rank}"}} {score:.6f}'
                )

        # Monte Carlo probabilities
        if 'monte_carlo' in results:
            metrics.append("\n# HELP topsis_probability_best Probability of being best alternative")
            metrics.append("# TYPE topsis_probability_best gauge")

            for alt, data in results['monte_carlo']['alternatives'].items():
                prob = data['probability_best']
                metrics.append(
                    f'topsis_probability_best{{instance="{alt}"}} {prob:.6f}'
                )

            # Confidence intervals
            metrics.append("\n# HELP topsis_confidence_interval_lower 95% CI lower bound")
            metrics.append("# TYPE topsis_confidence_interval_lower gauge")
            metrics.append("# HELP topsis_confidence_interval_upper 95% CI upper bound")
            metrics.append("# TYPE topsis_confidence_interval_upper gauge")

            for alt, data in results['monte_carlo']['alternatives'].items():
                ci = data['confidence_interval']
                metrics.append(
                    f'topsis_confidence_interval_lower{{instance="{alt}"}} {ci["lower"]:.6f}'
                )
                metrics.append(
                    f'topsis_confidence_interval_upper{{instance="{alt}"}} {ci["upper"]:.6f}'
                )

        # Cost metrics
        if 'cost' in results:
            metrics.append("\n# HELP optimization_cost_dollars Total optimization cost in USD")
            metrics.append("# TYPE optimization_cost_dollars gauge")

            total_cost = results['cost'].get('total_cost', 0)
            metrics.append(f'optimization_cost_dollars {total_cost:.4f}')

        # System info
        metrics.append("\n# HELP optimization_timestamp_seconds Last optimization timestamp")
        metrics.append("# TYPE optimization_timestamp_seconds gauge")

        import time
        metrics.append(f'optimization_timestamp_seconds {time.time():.0f}')

        return "\n".join(metrics)


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler для /metrics endpoint"""

    exporter = None  # Will be set by serve()

    def do_GET(self):
        if self.path == '/metrics':
            metrics = self.exporter.generate_metrics()

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.end_headers()
            self.wfile.write(metrics.encode('utf-8'))

        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            html = """
            <html>
            <head><title>TOPSIS Metrics Exporter</title></head>
            <body>
                <h1>Prometheus Metrics Exporter</h1>
                <p>TOPSIS Cloud Optimization System</p>
                <p><a href="/metrics">View Metrics</a></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass


def serve(port: int = 9090):
    """Запускає Prometheus exporter"""
    print(f"\nPrometheus Metrics Exporter")
    print(f"{'='*50}")
    print(f"Listening on: http://localhost:{port}")
    print(f"Metrics URL: http://localhost:{port}/metrics")
    print(f"\nPress CTRL+C to stop\n")

    # Initialize exporter
    MetricsHandler.exporter = PrometheusMetrics()

    # Start server
    server = HTTPServer(('0.0.0.0', port), MetricsHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.shutdown()


def main():
    parser = argparse.ArgumentParser(
        description='Prometheus metrics exporter for TOPSIS optimization'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=9090,
        help='Port to listen on (default: 9090)'
    )

    args = parser.parse_args()
    serve(port=args.port)


if __name__ == "__main__":
    main()

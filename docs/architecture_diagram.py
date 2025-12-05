#!/usr/bin/env python3
"""
Генерація професійної діаграми архітектури системи
Використовує diagrams library для створення схеми
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EC2
from diagrams.aws.network import ELB
from diagrams.onprem.client import Users
from diagrams.onprem.compute import Server
from diagrams.programming.language import Python
from diagrams.programming.framework import Flask
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.vcs import Github
from diagrams.custom import Custom
from pathlib import Path

# Створюємо директорію для діаграм
output_dir = Path("docs/diagrams")
output_dir.mkdir(exist_ok=True, parents=True)

# Налаштування діаграми
graph_attr = {
    "fontsize": "14",
    "bgcolor": "white",
    "pad": "0.5",
}

node_attr = {
    "fontsize": "12",
}

edge_attr = {
    "fontsize": "10",
}

with Diagram(
    "Cloud Optimization System Architecture",
    filename=str(output_dir / "system_architecture"),
    show=False,
    direction="TB",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):

    # Користувач
    user = Users("DevOps Engineer")

    with Cluster("Control Layer"):
        control_panel = Python("Control Panel\n(Interactive Config)")
        dashboard = Python("Live Dashboard\n(HTTP Server)")

    with Cluster("Core Optimization Engine"):
        with Cluster("Data Collection"):
            request_sim = Python("Request Simulator\n(Load Generator)")
            metrics = Python("Metrics Collector\n(CPU/RAM/Latency)")

        with Cluster("MCDM Analysis"):
            optimizer = Python("TOPSIS Optimizer\n(5 Criteria)")
            sensitivity = Python("Sensitivity Analyzer\n(Weight Variations)")
            comparison = Python("Method Comparator\n(TOPSIS/SAW/WPM)")

        with Cluster("Reporting"):
            visualizer = Python("Results Visualizer\n(6 Charts)")
            report_gen = Python("Report Generator\n(Markdown/PDF)")
            cost_pred = Python("Cost Predictor\n(AWS Pricing)")

    with Cluster("AWS Infrastructure (Terraform)"):
        with Cluster("EC2 Instances"):
            micro = EC2("t3.micro\n1 vCPU, 1GB")
            small = EC2("t3.small\n2 vCPU, 2GB")
            medium = EC2("t3.medium\n2 vCPU, 4GB")

        cpu_server = Server("CPU-Intensive\nServer (Flask)")

    with Cluster("Results Storage"):
        json_data = PostgreSQL("JSON Files\n(results/data/)")
        charts = PostgreSQL("Visualizations\n(results/charts/)")

    with Cluster("Version Control"):
        github = Github("GitHub Repository")

    # Потоки даних
    user >> Edge(label="1. Configure Test") >> control_panel
    control_panel >> Edge(label="2. Deploy") >> [micro, small, medium]
    [micro, small, medium] >> Edge(label="CPU Server") >> cpu_server

    request_sim >> Edge(label="3. Load Test\n(500/2000/5000 RPS)") >> cpu_server
    cpu_server >> Edge(label="4. Collect Metrics") >> metrics

    metrics >> Edge(label="5. Raw Data") >> optimizer
    optimizer >> Edge(label="6. TOPSIS Scores") >> sensitivity
    sensitivity >> Edge(label="7. Stability Data") >> comparison

    comparison >> Edge(label="8. Validated Results") >> visualizer
    comparison >> Edge(label="9. Analysis Data") >> cost_pred

    visualizer >> Edge(label="10. Save Charts") >> charts
    cost_pred >> Edge(label="11. Save JSON") >> json_data

    [charts, json_data] >> Edge(label="12. Generate Report") >> report_gen
    [charts, json_data] >> Edge(label="13. Display") >> dashboard

    dashboard >> Edge(label="14. View Results") >> user

    [control_panel, optimizer, sensitivity, comparison, visualizer, report_gen] >> Edge(label="Git Push") >> github

print("\n" + "="*70)
print("ARCHITECTURE DIAGRAM GENERATION")
print("="*70)
print("\n[INFO] Generating system architecture diagram...")
print("[INFO] This requires 'diagrams' library: pip install diagrams")
print("\n[OK] Diagram will be saved to: docs/diagrams/system_architecture.png")
print("\nIf you don't have diagrams library installed:")
print("  pip install diagrams")
print("  or: py -m pip install diagrams")
print("\n" + "="*70)

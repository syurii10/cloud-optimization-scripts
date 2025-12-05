#!/usr/bin/env python3
"""
Візуалізація результатів оптимізації
Генерує професійні графіки для магістерської роботи
"""

import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path
from typing import Dict, List

# Налаштування для українського тексту
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


class ResultsVisualizer:
    """Візуалізатор результатів оптимізації"""

    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.charts_dir = self.results_dir / "charts"
        self.charts_dir.mkdir(exist_ok=True, parents=True)

        # Кольори для графіків (професійна палітра)
        self.colors = {
            't3.micro': '#FF6B6B',    # Червоний
            't3.small': '#4ECDC4',    # Бірюзовий
            't3.medium': '#95E1D3'    # М'ятний
        }

    def load_json(self, filename: str) -> Dict:
        """Завантажує JSON файл"""
        filepath = self.results_dir / "data" / filename
        if not filepath.exists():
            filepath = self.results_dir / filename

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def plot_sensitivity_analysis(self):
        """Графіки аналізу чутливості"""
        print("\n[Sensitivity Analysis] Generating charts...")

        data = self.load_json("sensitivity/sensitivity_analysis.json")
        sensitivity_results = data['sensitivity_results']

        # Створюємо 5 графіків (по одному для кожного критерію)
        criteria = list(sensitivity_results.keys())

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()

        for idx, criterion in enumerate(criteria):
            ax = axes[idx]
            result = sensitivity_results[criterion]

            weight_values = result['weight_values']
            scores = result['scores']

            # Малюємо лінії для кожної альтернативи
            for alt_name, alt_scores in scores.items():
                ax.plot(weight_values, alt_scores,
                       marker='o', linewidth=2, markersize=4,
                       label=alt_name, color=self.colors.get(alt_name, '#333'))

            ax.set_title(f'Criterion: {criterion}', fontsize=12, fontweight='bold')
            ax.set_xlabel(f'Weight of {criterion}', fontsize=10)
            ax.set_ylabel('TOPSIS Score', fontsize=10)
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 1])

        # Видаляємо зайвий subplot
        fig.delaxes(axes[5])

        plt.suptitle('Sensitivity Analysis: TOPSIS Scores vs Criterion Weights',
                     fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()

        output_path = self.charts_dir / "sensitivity_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  [OK] Saved: {output_path}")
        plt.close()

    def plot_topsis_comparison(self):
        """Порівняння TOPSIS оцінок"""
        print("\n[TOPSIS Comparison] Generating chart...")

        data = self.load_json("data/optimization_results.json")
        results = data['results']

        alternatives = [r['alternative'] for r in results]
        scores = [r['score'] for r in results]
        colors_list = [self.colors.get(alt, '#333') for alt in alternatives]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(alternatives, scores, color=colors_list, alpha=0.8, edgecolor='black', linewidth=1.5)

        # Додаємо значення на стовпчиках
        for bar, score in zip(bars, scores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{score:.4f}',
                   ha='center', va='bottom', fontsize=11, fontweight='bold')

        ax.set_title('TOPSIS Optimization Results', fontsize=16, fontweight='bold')
        ax.set_xlabel('EC2 Instance Type', fontsize=12)
        ax.set_ylabel('TOPSIS Score', fontsize=12)
        ax.set_ylim([0, 1])
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        output_path = self.charts_dir / "topsis_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  [OK] Saved: {output_path}")
        plt.close()

    def plot_method_comparison(self):
        """Порівняння методів MCDM"""
        print("\n[Method Comparison] Generating chart...")

        data = self.load_json("data/method_comparison.json")
        ranking = data['ranking_comparison']

        methods = ['TOPSIS', 'SAW', 'WPM']
        alternatives = list(ranking.keys())

        # Підготовка даних для групованого bar chart
        x = np.arange(len(alternatives))
        width = 0.25

        fig, ax = plt.subplots(figsize=(12, 7))

        for i, method in enumerate(methods):
            ranks = [ranking[alt][method] for alt in alternatives]
            offset = width * (i - 1)
            bars = ax.bar(x + offset, ranks, width, label=method, alpha=0.8, edgecolor='black')

            # Додаємо значення на стовпчиках
            for bar, rank in zip(bars, ranks):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'#{rank}',
                       ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.set_title('MCDM Methods Comparison: Rankings', fontsize=16, fontweight='bold')
        ax.set_xlabel('EC2 Instance Type', fontsize=12)
        ax.set_ylabel('Rank (1=best)', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(alternatives)
        ax.set_ylim([0, 4])
        ax.invert_yaxis()  # Rank 1 на верху
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        output_path = self.charts_dir / "method_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  [OK] Saved: {output_path}")
        plt.close()

    def plot_cost_breakdown(self):
        """Розподіл вартості"""
        print("\n[Cost Breakdown] Generating chart...")

        data = self.load_json("data/cost_estimate.json")
        costs = data['costs']

        # Pie chart
        labels = ['Compute', 'Data Transfer', 'Client Overhead', 'Setup/Teardown']
        values = [costs['compute'], costs['data_transfer'],
                 costs['client_overhead'], costs['setup_teardown']]
        colors_pie = ['#FF6B6B', '#4ECDC4', '#95E1D3', '#FFD93D']
        explode = (0.05, 0.05, 0, 0)  # Виділяємо найбільші частини

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Pie chart
        wedges, texts, autotexts = ax1.pie(values, explode=explode, labels=labels, colors=colors_pie,
                                            autopct='%1.1f%%', startangle=90, textprops={'fontsize': 11})
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax1.set_title(f'Cost Breakdown\nTotal: ${costs["total"]:.4f}',
                     fontsize=14, fontweight='bold')

        # Bar chart
        ax2.barh(labels, values, color=colors_pie, alpha=0.8, edgecolor='black', linewidth=1.5)
        ax2.set_xlabel('Cost (USD)', fontsize=12)
        ax2.set_title('Cost by Category', fontsize=14, fontweight='bold')

        for i, v in enumerate(values):
            ax2.text(v, i, f' ${v:.4f}', va='center', fontsize=10, fontweight='bold')

        ax2.grid(axis='x', alpha=0.3)

        plt.tight_layout()
        output_path = self.charts_dir / "cost_breakdown.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  [OK] Saved: {output_path}")
        plt.close()

    def plot_stability_indices(self):
        """Індекси стабільності альтернатив"""
        print("\n[Stability Indices] Generating chart...")

        data = self.load_json("sensitivity/sensitivity_analysis.json")
        stability = data['stability_indices']

        alternatives = list(stability.keys())
        indices = list(stability.values())
        colors_list = [self.colors.get(alt, '#333') for alt in alternatives]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(alternatives, indices, color=colors_list, alpha=0.8, edgecolor='black', linewidth=1.5)

        # Додаємо значення на стовпчиках
        for bar, idx in zip(bars, indices):
            height = bar.get_height()
            stability_label = "High" if idx > 0.8 else "Medium" if idx > 0.5 else "Low"
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{idx:.4f}\n({stability_label})',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Лінії порогів
        ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.5, label='High Stability Threshold')
        ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Medium Stability Threshold')

        ax.set_title('Stability Indices of Alternatives', fontsize=16, fontweight='bold')
        ax.set_xlabel('EC2 Instance Type', fontsize=12)
        ax.set_ylabel('Stability Index (0-1)', fontsize=12)
        ax.set_ylim([0, 1])
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        output_path = self.charts_dir / "stability_indices.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  [OK] Saved: {output_path}")
        plt.close()

    def plot_correlation_heatmap(self):
        """Heatmap кореляцій між методами"""
        print("\n[Correlation Heatmap] Generating chart...")

        data = self.load_json("data/method_comparison.json")
        correlations = data['consensus']['rank_correlations']

        # Матриця кореляцій
        methods = ['TOPSIS', 'SAW', 'WPM']
        matrix = np.array([
            [1.0, correlations['TOPSIS_vs_SAW'], correlations['TOPSIS_vs_WPM']],
            [correlations['TOPSIS_vs_SAW'], 1.0, correlations['SAW_vs_WPM']],
            [correlations['TOPSIS_vs_WPM'], correlations['SAW_vs_WPM'], 1.0]
        ])

        fig, ax = plt.subplots(figsize=(8, 7))
        im = ax.imshow(matrix, cmap='RdYlGn', vmin=0, vmax=1, aspect='auto')

        # Налаштування осей
        ax.set_xticks(np.arange(len(methods)))
        ax.set_yticks(np.arange(len(methods)))
        ax.set_xticklabels(methods, fontsize=12)
        ax.set_yticklabels(methods, fontsize=12)

        # Додаємо значення в клітинки
        for i in range(len(methods)):
            for j in range(len(methods)):
                text = ax.text(j, i, f'{matrix[i, j]:.4f}',
                             ha="center", va="center", color="black",
                             fontsize=14, fontweight='bold')

        ax.set_title('Rank Correlation Matrix (Kendall Tau)',
                    fontsize=16, fontweight='bold', pad=20)

        # Colorbar
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label('Correlation Coefficient', rotation=270, labelpad=20, fontsize=12)

        plt.tight_layout()
        output_path = self.charts_dir / "correlation_heatmap.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  [OK] Saved: {output_path}")
        plt.close()

    def generate_all_charts(self):
        """Генерує всі графіки"""
        print("\n" + "=" * 70)
        print("GENERATING ALL VISUALIZATIONS")
        print("=" * 70)

        try:
            self.plot_sensitivity_analysis()
            self.plot_topsis_comparison()
            self.plot_method_comparison()
            self.plot_cost_breakdown()
            self.plot_stability_indices()
            self.plot_correlation_heatmap()

            print("\n" + "=" * 70)
            print("[SUCCESS] ALL CHARTS GENERATED SUCCESSFULLY")
            print("=" * 70)
            print(f"\nCharts saved to: {self.charts_dir}/")
            print("\nGenerated files:")
            for chart_file in self.charts_dir.glob("*.png"):
                print(f"  - {chart_file.name}")

        except Exception as e:
            print(f"\n[ERROR]: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Головна функція"""
    visualizer = ResultsVisualizer()
    visualizer.generate_all_charts()


if __name__ == "__main__":
    main()

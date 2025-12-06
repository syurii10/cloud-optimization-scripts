#!/usr/bin/env python3
"""
Monte Carlo Simulation для валідації стабільності TOPSIS результатів
Виконує 10,000 симуляцій з випадковими вагами критеріїв
Обчислює довірчі інтервали, розподіл ймовірностей та статистичну значущість
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from collections import defaultdict
import sys

# Додаємо шлях до optimizer.py
sys.path.append(str(Path(__file__).parent))
from optimizer import TOPSISOptimizer


class MonteCarloValidator:
    """Monte Carlo валідація TOPSIS результатів"""

    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.data_dir = self.results_dir / "data"
        self.charts_dir = self.results_dir / "charts"
        self.charts_dir.mkdir(exist_ok=True, parents=True)

        # Кольори для графіків
        self.colors = {
            't3.micro': '#FF6B6B',
            't3.small': '#4ECDC4',
            't3.medium': '#95E1D3'
        }

        # Статистика
        self.simulation_results = defaultdict(list)
        self.rank_distributions = defaultdict(lambda: defaultdict(int))

    def load_optimization_results(self) -> Dict:
        """Завантажує результати TOPSIS оптимізації"""
        results_file = self.data_dir / "optimization_results.json"

        if not results_file.exists():
            raise FileNotFoundError(
                f"Optimization results not found: {results_file}\n"
                f"Run optimizer.py first!"
            )

        with open(results_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_random_weights(self, num_criteria: int = 5) -> np.ndarray:
        """
        Генерує випадкові ваги критеріїв
        Використовує Dirichlet distribution для гарантії sum = 1.0
        """
        # Dirichlet з alpha=1 дає uniform distribution
        weights = np.random.dirichlet(np.ones(num_criteria))
        return weights

    def run_simulation(self,
                      decision_matrix: np.ndarray,
                      benefit_criteria: List[bool],
                      alternatives: List[str],
                      num_simulations: int = 10000,
                      confidence_level: float = 0.95) -> Dict:
        """
        Виконує Monte Carlo симуляцію

        Args:
            decision_matrix: Матриця рішень (alternatives × criteria)
            benefit_criteria: Маска benefit/cost критеріїв
            alternatives: Назви альтернатив
            num_simulations: Кількість симуляцій
            confidence_level: Рівень довірчого інтервалу (0.95 = 95%)

        Returns:
            Словник з результатами симуляції
        """
        print(f"\n{'='*70}")
        print("MONTE CARLO SIMULATION")
        print(f"{'='*70}\n")
        print(f"Simulations: {num_simulations:,}")
        print(f"Confidence Level: {confidence_level*100}%")
        print(f"Alternatives: {', '.join(alternatives)}\n")

        optimizer = TOPSISOptimizer()

        # Зберігаємо результати кожної симуляції
        all_scores = defaultdict(list)
        all_ranks = defaultdict(list)

        # Прогрес бар
        progress_interval = num_simulations // 20

        for i in range(num_simulations):
            if (i + 1) % progress_interval == 0:
                progress = (i + 1) / num_simulations * 100
                print(f"Progress: {progress:.0f}% ({i+1:,}/{num_simulations:,})", end='\r')

            # Генеруємо випадкові ваги
            random_weights = self.generate_random_weights()

            # Запускаємо TOPSIS з цими вагами (повний workflow)
            # 1. Нормалізація
            normalized = optimizer.normalize_matrix(decision_matrix)

            # 2. Зважена матриця
            weighted = optimizer.calculate_weighted_matrix(normalized, random_weights)

            # 3. Ідеальні рішення
            ideal, anti_ideal = optimizer.find_ideal_solutions(weighted, benefit_criteria)

            # 4. Відстані
            dist_ideal, dist_anti_ideal = optimizer.calculate_distances(weighted, ideal, anti_ideal)

            # 5. Оцінки
            scores = optimizer.calculate_scores(dist_ideal, dist_anti_ideal)

            # Зберігаємо scores
            for alt, score in zip(alternatives, scores):
                all_scores[alt].append(score)

            # Обчислюємо ранги (1 = найкращий)
            ranks = stats.rankdata(-scores, method='min')
            for alt, rank in zip(alternatives, ranks):
                all_ranks[alt].append(int(rank))
                self.rank_distributions[alt][int(rank)] += 1

        print(f"Progress: 100% ({num_simulations:,}/{num_simulations:,})")
        print("\n[OK] Simulation complete!\n")

        # Обчислюємо статистику
        results = {
            'num_simulations': num_simulations,
            'confidence_level': confidence_level,
            'alternatives': {},
            'winner_distribution': {},
            'statistical_tests': {}
        }

        # Для кожної альтернативи
        for alt in alternatives:
            scores_array = np.array(all_scores[alt])
            ranks_array = np.array(all_ranks[alt])

            # Базова статистика
            mean_score = np.mean(scores_array)
            std_score = np.std(scores_array)
            median_score = np.median(scores_array)

            # Довірчий інтервал
            ci_lower, ci_upper = stats.t.interval(
                confidence_level,
                len(scores_array) - 1,
                loc=mean_score,
                scale=stats.sem(scores_array)
            )

            # Частота рангів
            rank_frequencies = {
                rank: self.rank_distributions[alt][rank] / num_simulations
                for rank in sorted(self.rank_distributions[alt].keys())
            }

            # Ймовірність бути найкращим (rank = 1)
            prob_best = self.rank_distributions[alt][1] / num_simulations

            # Середній ранг
            mean_rank = np.mean(ranks_array)

            results['alternatives'][alt] = {
                'mean_score': float(mean_score),
                'std_score': float(std_score),
                'median_score': float(median_score),
                'confidence_interval': {
                    'lower': float(ci_lower),
                    'upper': float(ci_upper),
                    'level': confidence_level
                },
                'rank_distribution': rank_frequencies,
                'probability_best': float(prob_best),
                'mean_rank': float(mean_rank),
                'scores_raw': scores_array.tolist()  # Для додаткового аналізу
            }

            # Частота перемог
            results['winner_distribution'][alt] = float(prob_best)

        # Статистичні тести
        # 1. Перевірка нормальності розподілу (Shapiro-Wilk test)
        for alt in alternatives:
            scores = all_scores[alt]
            stat, p_value = stats.shapiro(scores[:5000])  # Shapiro max 5000 samples
            results['statistical_tests'][f'{alt}_normality'] = {
                'test': 'Shapiro-Wilk',
                'statistic': float(stat),
                'p_value': float(p_value),
                'is_normal': bool(p_value > 0.05)
            }

        # 2. Порівняння альтернатив (ANOVA)
        if len(alternatives) > 2:
            scores_groups = [all_scores[alt] for alt in alternatives]
            f_stat, p_value = stats.f_oneway(*scores_groups)
            results['statistical_tests']['anova'] = {
                'test': 'One-way ANOVA',
                'f_statistic': float(f_stat),
                'p_value': float(p_value),
                'significant_difference': bool(p_value < 0.05)
            }

        # 3. Pairwise comparisons (t-test)
        pairwise_tests = {}
        for i, alt1 in enumerate(alternatives):
            for alt2 in alternatives[i+1:]:
                t_stat, p_value = stats.ttest_ind(all_scores[alt1], all_scores[alt2])
                pairwise_tests[f'{alt1}_vs_{alt2}'] = {
                    'test': 'Independent t-test',
                    't_statistic': float(t_stat),
                    'p_value': float(p_value),
                    'significant': bool(p_value < 0.05)
                }
        results['statistical_tests']['pairwise'] = pairwise_tests

        self.simulation_results = all_scores
        return results

    def visualize_results(self, results: Dict):
        """Створює візуалізації Monte Carlo результатів"""
        print("\n[INFO] Generating Monte Carlo visualizations...")

        alternatives = list(results['alternatives'].keys())

        # Створюємо фігуру з 4 графіками
        fig = plt.figure(figsize=(20, 12))

        # 1. Розподіл TOPSIS scores (violin plots)
        ax1 = plt.subplot(2, 3, 1)
        data_for_violin = [
            results['alternatives'][alt]['scores_raw']
            for alt in alternatives
        ]

        parts = ax1.violinplot(
            data_for_violin,
            positions=range(len(alternatives)),
            showmeans=True,
            showmedians=True
        )

        # Колір для violin plots
        for i, pc in enumerate(parts['bodies']):
            pc.set_facecolor(self.colors[alternatives[i]])
            pc.set_alpha(0.7)

        ax1.set_xticks(range(len(alternatives)))
        ax1.set_xticklabels(alternatives)
        ax1.set_ylabel('TOPSIS Score')
        ax1.set_title('Distribution of TOPSIS Scores\n(10,000 simulations)', fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)

        # 2. Довірчі інтервали
        ax2 = plt.subplot(2, 3, 2)

        means = [results['alternatives'][alt]['mean_score'] for alt in alternatives]
        ci_lowers = [results['alternatives'][alt]['confidence_interval']['lower'] for alt in alternatives]
        ci_uppers = [results['alternatives'][alt]['confidence_interval']['upper'] for alt in alternatives]
        errors = [
            [means[i] - ci_lowers[i], ci_uppers[i] - means[i]]
            for i in range(len(alternatives))
        ]

        x_pos = np.arange(len(alternatives))
        bars = ax2.bar(x_pos, means, color=[self.colors[alt] for alt in alternatives], alpha=0.7)
        ax2.errorbar(x_pos, means, yerr=np.array(errors).T, fmt='none', color='black', capsize=5)

        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(alternatives)
        ax2.set_ylabel('TOPSIS Score')
        ax2.set_title(f'Mean Scores with {int(results["confidence_level"]*100)}% Confidence Intervals', fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)

        # Додаємо значення на bars
        for i, (bar, mean) in enumerate(zip(bars, means)):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{mean:.4f}',
                    ha='center', va='bottom', fontsize=9)

        # 3. Розподіл рангів (stacked bar)
        ax3 = plt.subplot(2, 3, 3)

        rank_data = defaultdict(list)
        all_ranks = set()
        for alt in alternatives:
            rank_dist = results['alternatives'][alt]['rank_distribution']
            all_ranks.update([int(r) for r in rank_dist.keys()])

        # Створюємо повні дані для всіх рангів
        for rank in sorted(all_ranks):
            for alt in alternatives:
                rank_dist = results['alternatives'][alt]['rank_distribution']
                rank_data[rank].append(rank_dist.get(rank, 0) * 100)

        x_pos = np.arange(len(alternatives))
        bottom = np.zeros(len(alternatives))

        for rank in sorted(rank_data.keys()):
            ax3.bar(x_pos, rank_data[rank], bottom=bottom, label=f'Rank {rank}', alpha=0.8)
            bottom += np.array(rank_data[rank])

        ax3.set_xticks(x_pos)
        ax3.set_xticklabels(alternatives)
        ax3.set_ylabel('Probability (%)')
        ax3.set_title('Rank Distribution', fontweight='bold')
        ax3.legend()
        ax3.grid(axis='y', alpha=0.3)

        # 4. Ймовірність бути найкращим
        ax4 = plt.subplot(2, 3, 4)

        probs_best = [results['alternatives'][alt]['probability_best'] * 100 for alt in alternatives]
        bars = ax4.bar(x_pos, probs_best, color=[self.colors[alt] for alt in alternatives], alpha=0.7)

        ax4.set_xticks(x_pos)
        ax4.set_xticklabels(alternatives)
        ax4.set_ylabel('Probability (%)')
        ax4.set_title('Probability of Being Best Alternative', fontweight='bold')
        ax4.grid(axis='y', alpha=0.3)

        # Додаємо значення
        for bar, prob in zip(bars, probs_best):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{prob:.1f}%',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        # 5. Histogram для переможця
        ax5 = plt.subplot(2, 3, 5)

        # Знаходимо переможця (highest probability)
        winner = max(alternatives, key=lambda alt: results['alternatives'][alt]['probability_best'])
        winner_scores = results['alternatives'][winner]['scores_raw']

        ax5.hist(winner_scores, bins=50, color=self.colors[winner], alpha=0.7, edgecolor='black')

        mean_val = results['alternatives'][winner]['mean_score']
        ci_lower = results['alternatives'][winner]['confidence_interval']['lower']
        ci_upper = results['alternatives'][winner]['confidence_interval']['upper']

        ax5.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.4f}')
        ax5.axvline(ci_lower, color='orange', linestyle=':', linewidth=1.5, label=f'CI Lower: {ci_lower:.4f}')
        ax5.axvline(ci_upper, color='orange', linestyle=':', linewidth=1.5, label=f'CI Upper: {ci_upper:.4f}')

        ax5.set_xlabel('TOPSIS Score')
        ax5.set_ylabel('Frequency')
        ax5.set_title(f'Score Distribution for {winner} (Winner)', fontweight='bold')
        ax5.legend()
        ax5.grid(axis='y', alpha=0.3)

        # 6. Statistical summary (text)
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')

        summary_text = "STATISTICAL SUMMARY\n" + "="*40 + "\n\n"

        # Winner info
        summary_text += f"Winner: {winner}\n"
        summary_text += f"  Probability: {results['alternatives'][winner]['probability_best']*100:.1f}%\n"
        summary_text += f"  Mean Score: {results['alternatives'][winner]['mean_score']:.4f}\n"
        summary_text += f"  95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]\n\n"

        # ANOVA test
        if 'anova' in results['statistical_tests']:
            anova = results['statistical_tests']['anova']
            summary_text += f"ANOVA Test:\n"
            summary_text += f"  F-statistic: {anova['f_statistic']:.4f}\n"
            summary_text += f"  p-value: {anova['p_value']:.6f}\n"
            summary_text += f"  Significant: {'YES' if anova['significant_difference'] else 'NO'}\n\n"

        # Rankings
        summary_text += "Mean Rankings:\n"
        sorted_alts = sorted(alternatives,
                           key=lambda a: results['alternatives'][a]['mean_rank'])
        for i, alt in enumerate(sorted_alts, 1):
            mean_rank = results['alternatives'][alt]['mean_rank']
            summary_text += f"  {i}. {alt}: {mean_rank:.2f}\n"

        ax6.text(0.1, 0.9, summary_text, fontsize=10, verticalalignment='top',
                fontfamily='monospace', transform=ax6.transAxes)

        plt.tight_layout()

        # Зберігаємо
        output_path = self.charts_dir / "monte_carlo_analysis.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"[OK] Saved: {output_path}")

    def save_results(self, results: Dict):
        """Зберігає результати Monte Carlo симуляції"""
        output_file = self.data_dir / "monte_carlo_results.json"

        # Видаляємо raw scores для зменшення розміру файлу
        results_to_save = results.copy()
        for alt in results_to_save['alternatives']:
            # Зберігаємо тільки sample (1000 точок)
            raw_scores = results_to_save['alternatives'][alt]['scores_raw']
            results_to_save['alternatives'][alt]['scores_sample'] = raw_scores[::10]
            del results_to_save['alternatives'][alt]['scores_raw']

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_to_save, f, indent=2, ensure_ascii=False)

        print(f"[OK] Results saved: {output_file}")

    def print_summary(self, results: Dict):
        """Виводить summary результатів"""
        print(f"\n{'='*70}")
        print("MONTE CARLO VALIDATION SUMMARY")
        print(f"{'='*70}\n")

        alternatives = list(results['alternatives'].keys())

        # Сортуємо за ймовірністю бути найкращим
        sorted_alts = sorted(
            alternatives,
            key=lambda a: results['alternatives'][a]['probability_best'],
            reverse=True
        )

        print(f"Simulations: {results['num_simulations']:,}")
        print(f"Confidence Level: {results['confidence_level']*100}%\n")

        print("RANKINGS (by probability of being best):\n")
        for i, alt in enumerate(sorted_alts, 1):
            data = results['alternatives'][alt]
            prob_best = data['probability_best'] * 100
            mean_score = data['mean_score']
            ci_lower = data['confidence_interval']['lower']
            ci_upper = data['confidence_interval']['upper']
            mean_rank = data['mean_rank']

            print(f"#{i} {alt}")
            print(f"   Probability Best: {prob_best:.1f}%")
            print(f"   Mean TOPSIS Score: {mean_score:.4f}")
            print(f"   95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
            print(f"   Mean Rank: {mean_rank:.2f}")
            print()

        # Статистична значущість
        print("STATISTICAL SIGNIFICANCE:\n")

        if 'anova' in results['statistical_tests']:
            anova = results['statistical_tests']['anova']
            print(f"ANOVA Test:")
            print(f"  F-statistic: {anova['f_statistic']:.4f}")
            print(f"  p-value: {anova['p_value']:.6f}")

            if anova['p_value'] < 0.05:
                print(f"  Result: Alternatives are SIGNIFICANTLY DIFFERENT (p < 0.05)")
            else:
                print(f"  Result: No significant difference (p >= 0.05)")
            print()

        # Pairwise
        if 'pairwise' in results['statistical_tests']:
            print("Pairwise Comparisons (t-test):")
            for comparison, test_data in results['statistical_tests']['pairwise'].items():
                sig_marker = "***" if test_data['significant'] else ""
                print(f"  {comparison}: p={test_data['p_value']:.6f} {sig_marker}")

        print(f"\n{'='*70}\n")


def main():
    """Головна функція"""
    print("\n" + "="*70)
    print("MONTE CARLO VALIDATION FOR TOPSIS OPTIMIZATION")
    print("="*70 + "\n")

    validator = MonteCarloValidator()

    # Завантажуємо результати оптимізації
    print("[INFO] Loading optimization results...")
    opt_results = validator.load_optimization_results()
    print(f"[OK] Loaded results for {len(opt_results['results'])} alternatives\n")

    # Підготовка даних
    alternatives = [r['alternative'] for r in opt_results['results']]

    # Створюємо decision matrix з оригінальних даних
    decision_matrix = []
    for result in opt_results['results']:
        criteria = result['criteria']
        row = [
            criteria['performance'],
            criteria['response_time'],
            criteria['cpu_usage'],
            criteria['memory_usage'],
            criteria['cost']
        ]
        decision_matrix.append(row)

    decision_matrix = np.array(decision_matrix)

    # Benefit criteria (True = більше краще, False = менше краще)
    benefit_criteria = [True, False, False, False, False]

    # Запускаємо Monte Carlo симуляцію
    results = validator.run_simulation(
        decision_matrix=decision_matrix,
        benefit_criteria=benefit_criteria,
        alternatives=alternatives,
        num_simulations=10000,
        confidence_level=0.95
    )

    # Виводимо summary
    validator.print_summary(results)

    # Візуалізуємо
    validator.visualize_results(results)

    # Зберігаємо
    validator.save_results(results)

    print("\n[SUCCESS] Monte Carlo validation complete!")
    print("Check results/charts/monte_carlo_analysis.png for visualizations")
    print("Check results/data/monte_carlo_results.json for detailed statistics\n")


if __name__ == "__main__":
    main()

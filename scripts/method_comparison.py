#!/usr/bin/env python3
"""
Порівняння методів багатокритеріальної оптимізації
TOPSIS vs SAW (Simple Additive Weighting) vs WPM (Weighted Product Model)
"""

import numpy as np
import json
from typing import Dict, List
from optimizer import TOPSISOptimizer


class SAWOptimizer:
    """Simple Additive Weighting (SAW) метод"""

    def __init__(self, criteria_weights: Dict[str, float]):
        self.criteria_weights = criteria_weights

    def normalize_matrix(self, matrix: np.ndarray, benefit_criteria: List[bool]) -> np.ndarray:
        """
        Нормалізація для SAW (linear normalization)

        Для benefit criteria: xij / max(xj)
        Для cost criteria: min(xj) / xij
        """
        normalized = np.zeros_like(matrix, dtype=float)

        for j in range(matrix.shape[1]):
            col = matrix[:, j]
            if benefit_criteria[j]:
                # Більше = краще
                max_val = np.max(col)
                normalized[:, j] = col / max_val if max_val != 0 else col
            else:
                # Менше = краще
                min_val = np.min(col)
                normalized[:, j] = min_val / col if np.all(col != 0) else 1 / (col + 0.0001)

        return normalized

    def optimize(self, alternatives: Dict[str, Dict[str, float]]) -> Dict:
        """Виконує SAW оптимізацію"""
        alt_names = list(alternatives.keys())
        criteria_names = list(self.criteria_weights.keys())

        # Матриця рішень
        matrix = np.array([
            [alternatives[alt][criterion] for criterion in criteria_names]
            for alt in alt_names
        ])

        # Benefit criteria
        benefit_criteria = [True, False, False, False, False]

        # Нормалізація
        normalized = self.normalize_matrix(matrix, benefit_criteria)

        # Ваги
        weights = np.array([self.criteria_weights[c] for c in criteria_names])

        # Зважена сума
        scores = np.sum(normalized * weights, axis=1)

        # Формування результатів
        results = []
        for i, alt_name in enumerate(alt_names):
            results.append({
                'alternative': alt_name,
                'score': float(scores[i]),
                'rank': 0,
                'criteria': alternatives[alt_name]
            })

        # Сортування
        results.sort(key=lambda x: x['score'], reverse=True)

        for i, result in enumerate(results):
            result['rank'] = i + 1

        return {
            'method': 'SAW',
            'criteria_weights': self.criteria_weights,
            'results': results,
            'best_alternative': results[0]['alternative']
        }


class WPMOptimizer:
    """Weighted Product Model (WPM) метод"""

    def __init__(self, criteria_weights: Dict[str, float]):
        self.criteria_weights = criteria_weights

    def optimize(self, alternatives: Dict[str, Dict[str, float]]) -> Dict:
        """Виконує WPM оптимізацію"""
        alt_names = list(alternatives.keys())
        criteria_names = list(self.criteria_weights.keys())

        # Матриця рішень
        matrix = np.array([
            [alternatives[alt][criterion] for criterion in criteria_names]
            for alt in alt_names
        ])

        # Benefit criteria (False для cost criteria - потрібно інвертувати)
        benefit_criteria = [True, False, False, False, False]

        # Ваги
        weights = np.array([self.criteria_weights[c] for c in criteria_names])

        # WPM: Product of (value^weight)
        scores = np.ones(matrix.shape[0])

        for j in range(matrix.shape[1]):
            col = matrix[:, j]
            weight = weights[j]

            if benefit_criteria[j]:
                # Більше = краще: value^weight
                scores *= np.power(col, weight)
            else:
                # Менше = краще: (1/value)^weight
                scores *= np.power(1.0 / (col + 0.0001), weight)

        # Формування результатів
        results = []
        for i, alt_name in enumerate(alt_names):
            results.append({
                'alternative': alt_name,
                'score': float(scores[i]),
                'rank': 0,
                'criteria': alternatives[alt_name]
            })

        # Сортування
        results.sort(key=lambda x: x['score'], reverse=True)

        for i, result in enumerate(results):
            result['rank'] = i + 1

        return {
            'method': 'WPM',
            'criteria_weights': self.criteria_weights,
            'results': results,
            'best_alternative': results[0]['alternative']
        }


class MethodComparator:
    """Порівняння різних методів MCDM"""

    def __init__(self, alternatives: Dict[str, Dict[str, float]],
                 criteria_weights: Dict[str, float]):
        self.alternatives = alternatives
        self.criteria_weights = criteria_weights

    def compare_methods(self) -> Dict:
        """
        Порівнює TOPSIS, SAW, та WPM

        Returns:
            Результати порівняння
        """
        print("\n" + "=" * 70)
        print("ПОРІВНЯННЯ МЕТОДІВ БАГАТОКРИТЕРІАЛЬНОЇ ОПТИМІЗАЦІЇ")
        print("=" * 70)

        # TOPSIS
        print("\n[1/3] Виконання TOPSIS...")
        topsis = TOPSISOptimizer(self.criteria_weights)
        topsis_results = topsis.optimize(self.alternatives)

        # SAW
        print("[2/3] Виконання SAW...")
        saw = SAWOptimizer(self.criteria_weights)
        saw_results = saw.optimize(self.alternatives)

        # WPM
        print("[3/3] Виконання WPM...")
        wpm = WPMOptimizer(self.criteria_weights)
        wpm_results = wpm.optimize(self.alternatives)

        # Порівняння результатів
        comparison = {
            'methods': {
                'TOPSIS': topsis_results,
                'SAW': saw_results,
                'WPM': wpm_results
            },
            'ranking_comparison': self._compare_rankings(
                topsis_results, saw_results, wpm_results
            ),
            'consensus': self._calculate_consensus(
                topsis_results, saw_results, wpm_results
            )
        }

        self._print_comparison(comparison)

        return comparison

    def _compare_rankings(self, topsis: Dict, saw: Dict, wpm: Dict) -> Dict:
        """Порівнює рангування різних методів"""
        rankings = {}

        for alt_name in self.alternatives.keys():
            rankings[alt_name] = {
                'TOPSIS': self._get_rank(topsis, alt_name),
                'SAW': self._get_rank(saw, alt_name),
                'WPM': self._get_rank(wpm, alt_name)
            }

        return rankings

    def _get_rank(self, results: Dict, alt_name: str) -> int:
        """Отримує ранг альтернативи"""
        for result in results['results']:
            if result['alternative'] == alt_name:
                return result['rank']
        return -1

    def _calculate_consensus(self, topsis: Dict, saw: Dict, wpm: Dict) -> Dict:
        """
        Обчислює консенсус між методами

        Returns:
            Метрики консенсусу
        """
        # Перевіряємо чи всі методи обрали одного лідера
        leaders = {
            'TOPSIS': topsis['best_alternative'],
            'SAW': saw['best_alternative'],
            'WPM': wpm['best_alternative']
        }

        unanimous = len(set(leaders.values())) == 1

        # Kendall Tau rank correlation
        rankings_matrix = []
        for alt_name in self.alternatives.keys():
            rankings_matrix.append([
                self._get_rank(topsis, alt_name),
                self._get_rank(saw, alt_name),
                self._get_rank(wpm, alt_name)
            ])

        rankings_matrix = np.array(rankings_matrix)

        # Обчислюємо кореляції
        from scipy.stats import kendalltau

        correlations = {
            'TOPSIS_vs_SAW': kendalltau(rankings_matrix[:, 0], rankings_matrix[:, 1])[0],
            'TOPSIS_vs_WPM': kendalltau(rankings_matrix[:, 0], rankings_matrix[:, 2])[0],
            'SAW_vs_WPM': kendalltau(rankings_matrix[:, 1], rankings_matrix[:, 2])[0]
        }

        avg_correlation = np.mean(list(correlations.values()))

        return {
            'unanimous_leader': unanimous,
            'leaders': leaders,
            'rank_correlations': correlations,
            'average_correlation': float(avg_correlation),
            'consensus_level': 'високий' if avg_correlation > 0.8 else 'середній' if avg_correlation > 0.5 else 'низький'
        }

    def _print_comparison(self, comparison: Dict):
        """Виводить результати порівняння"""
        print("\n" + "=" * 70)
        print("РЕЗУЛЬТАТИ ПОРІВНЯННЯ")
        print("=" * 70)

        # Таблиця рангів
        print("\nРангування за методами:")
        print("-" * 70)
        print(f"{'Альтернатива':<15} {'TOPSIS':<15} {'SAW':<15} {'WPM':<15}")
        print("-" * 70)

        for alt_name, ranks in comparison['ranking_comparison'].items():
            print(f"{alt_name:<15} "
                  f"#{ranks['TOPSIS']:<14} "
                  f"#{ranks['SAW']:<14} "
                  f"#{ranks['WPM']:<14}")

        # Консенсус
        consensus = comparison['consensus']
        print("\n" + "=" * 70)
        print("КОНСЕНСУС МІЖ МЕТОДАМИ")
        print("=" * 70)

        print(f"\nОдностайність лідера: {'ТАК' if consensus['unanimous_leader'] else 'НІ'}")
        print("\nЛідери за методами:")
        for method, leader in consensus['leaders'].items():
            print(f"  {method}: {leader}")

        print(f"\nКореляції рангів (Kendall Tau):")
        for pair, corr in consensus['rank_correlations'].items():
            print(f"  {pair}: {corr:.4f}")

        print(f"\nСередня кореляція: {consensus['average_correlation']:.4f}")
        print(f"Рівень консенсусу: {consensus['consensus_level']}")

    def save_results(self, output_file: str = "results/method_comparison.json"):
        """Зберігає результати порівняння"""
        from pathlib import Path

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        comparison = self.compare_methods()

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Результати збережено: {output_file}")

        return comparison


def example_usage():
    """Приклад використання"""

    alternatives = {
        't3.micro': {
            'performance': 150,
            'response_time': 0.08,
            'cpu_usage': 45,
            'memory_usage': 35,
            'cost': 0.0104,
        },
        't3.small': {
            'performance': 300,
            'response_time': 0.04,
            'cpu_usage': 30,
            'memory_usage': 25,
            'cost': 0.0208,
        },
        't3.medium': {
            'performance': 600,
            'response_time': 0.02,
            'cpu_usage': 20,
            'memory_usage': 20,
            'cost': 0.0416,
        },
    }

    criteria_weights = {
        'performance': 0.35,
        'response_time': 0.25,
        'cpu_usage': 0.15,
        'memory_usage': 0.15,
        'cost': 0.10,
    }

    comparator = MethodComparator(alternatives, criteria_weights)
    comparator.save_results()


if __name__ == "__main__":
    # Перевіряємо наявність scipy
    try:
        import scipy
    except ImportError:
        print("ПОПЕРЕДЖЕННЯ: scipy не встановлено. Встановіть: pip install scipy")
        print("Деякі функції можуть не працювати.")

    example_usage()

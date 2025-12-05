#!/usr/bin/env python3
"""
Sensitivity Analysis для TOPSIS оптимізації
Аналіз чутливості результатів до зміни ваг критеріїв
"""

import numpy as np
import json
from typing import Dict, List
from optimizer import TOPSISOptimizer
import matplotlib.pyplot as plt
from pathlib import Path


class SensitivityAnalyzer:
    """Аналізатор чутливості TOPSIS до зміни ваг"""

    def __init__(self, alternatives: Dict[str, Dict[str, float]]):
        """
        Ініціалізація аналізатора

        Args:
            alternatives: Словник альтернатив з критеріями
        """
        self.alternatives = alternatives
        self.base_weights = {
            'performance': 0.35,
            'response_time': 0.25,
            'cpu_usage': 0.15,
            'memory_usage': 0.15,
            'cost': 0.10,
        }

    def vary_single_criterion(self, criterion: str, steps: int = 20) -> Dict:
        """
        Варіює вагу одного критерію та спостерігає зміни

        Args:
            criterion: Назва критерію для варіювання
            steps: Кількість кроків варіювання

        Returns:
            Результати аналізу чутливості
        """
        results = {
            'criterion': criterion,
            'weight_values': [],
            'rankings': {},
            'scores': {}
        }

        # Ініціалізуємо словники для кожної альтернативи
        for alt_name in self.alternatives.keys():
            results['rankings'][alt_name] = []
            results['scores'][alt_name] = []

        # Варіюємо вагу від 0.05 до 0.70
        for weight in np.linspace(0.05, 0.70, steps):
            # Створюємо нові ваги
            modified_weights = self._redistribute_weights(criterion, weight)

            # Виконуємо TOPSIS з новими вагами
            optimizer = TOPSISOptimizer(modified_weights)
            topsis_results = optimizer.optimize(self.alternatives)

            # Зберігаємо результати
            results['weight_values'].append(round(weight, 3))

            for result in topsis_results['results']:
                alt_name = result['alternative']
                results['rankings'][alt_name].append(result['rank'])
                results['scores'][alt_name].append(round(result['score'], 4))

        return results

    def _redistribute_weights(self, varied_criterion: str, new_weight: float) -> Dict[str, float]:
        """
        Перерозподіляє ваги пропорційно після зміни одного критерію

        Args:
            varied_criterion: Критерій що змінюється
            new_weight: Нова вага для критерію

        Returns:
            Оновлений словник ваг
        """
        # Копіюємо базові ваги
        weights = self.base_weights.copy()

        # Обчислюємо різницю
        old_weight = weights[varied_criterion]
        difference = old_weight - new_weight

        # Розподіляємо різницю пропорційно серед інших критеріїв
        other_criteria = [c for c in weights.keys() if c != varied_criterion]
        total_other_weights = sum(weights[c] for c in other_criteria)

        for criterion in other_criteria:
            proportion = weights[criterion] / total_other_weights
            weights[criterion] += difference * proportion

        # Встановлюємо нову вагу
        weights[varied_criterion] = new_weight

        # Нормалізуємо (сума = 1.0)
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}

        return weights

    def full_sensitivity_analysis(self) -> Dict:
        """
        Виконує повний аналіз чутливості для всіх критеріїв

        Returns:
            Результати для всіх критеріїв
        """
        all_results = {}

        print("\n" + "=" * 70)
        print("АНАЛІЗ ЧУТЛИВОСТІ (SENSITIVITY ANALYSIS)")
        print("=" * 70)

        for criterion in self.base_weights.keys():
            print(f"\nАналіз критерію: {criterion}")
            results = self.vary_single_criterion(criterion)
            all_results[criterion] = results

            # Виводимо короткий звіт
            self._print_criterion_summary(results)

        return all_results

    def _print_criterion_summary(self, results: Dict):
        """Виводить короткий звіт для одного критерію"""
        criterion = results['criterion']
        weight_values = results['weight_values']

        print(f"  Діапазон ваг: {min(weight_values):.2f} - {max(weight_values):.2f}")

        # Перевіряємо стабільність рангів
        rank_changes = {}
        for alt_name, rankings in results['rankings'].items():
            unique_ranks = len(set(rankings))
            rank_changes[alt_name] = unique_ranks

        print(f"  Зміни рангів:")
        for alt_name, changes in rank_changes.items():
            stability = "стабільний" if changes == 1 else f"змінювався ({changes} позицій)"
            print(f"    - {alt_name}: {stability}")

    def identify_breakpoints(self, criterion: str, steps: int = 50) -> List[Dict]:
        """
        Визначає точки перелому (коли змінюється лідер)

        Args:
            criterion: Критерій для аналізу
            steps: Кількість кроків

        Returns:
            Список точок перелому
        """
        results = self.vary_single_criterion(criterion, steps)
        breakpoints = []

        weight_values = results['weight_values']
        # Визначаємо лідера на кожному кроці
        leaders = []

        for i in range(len(weight_values)):
            min_rank = float('inf')
            leader = None

            for alt_name, rankings in results['rankings'].items():
                if rankings[i] < min_rank:
                    min_rank = rankings[i]
                    leader = alt_name

            leaders.append(leader)

        # Знаходимо зміни лідера
        for i in range(1, len(leaders)):
            if leaders[i] != leaders[i-1]:
                breakpoints.append({
                    'weight': weight_values[i],
                    'previous_leader': leaders[i-1],
                    'new_leader': leaders[i],
                    'criterion': criterion
                })

        return breakpoints

    def calculate_stability_index(self) -> Dict[str, float]:
        """
        Обчислює індекс стабільності для кожної альтернативи

        Індекс стабільності: чим менше ранг змінюється при варіюванні ваг,
        тим вище стабільність (від 0 до 1)

        Returns:
            Словник з індексами стабільності
        """
        stability_indices = {}

        # Аналізуємо всі критерії
        all_rank_variations = {alt: [] for alt in self.alternatives.keys()}

        for criterion in self.base_weights.keys():
            results = self.vary_single_criterion(criterion, steps=30)

            for alt_name, rankings in results['rankings'].items():
                # Стандартне відхилення рангів
                std_dev = np.std(rankings)
                all_rank_variations[alt_name].append(std_dev)

        # Обчислюємо загальний індекс стабільності
        for alt_name, variations in all_rank_variations.items():
            # Середнє стандартне відхилення
            avg_std = np.mean(variations)

            # Перетворюємо у індекс від 0 до 1 (менше відхилення = вища стабільність)
            # Максимальне можливе std для 3 альтернатив ≈ 0.82
            stability = max(0, 1 - (avg_std / 0.82))

            stability_indices[alt_name] = round(stability, 4)

        return stability_indices

    def save_results(self, output_dir: str = "results/sensitivity"):
        """
        Зберігає результати аналізу

        Args:
            output_dir: Директорія для збереження
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Повний аналіз
        full_results = self.full_sensitivity_analysis()

        # Індекси стабільності
        stability = self.calculate_stability_index()

        # Точки перелому
        all_breakpoints = {}
        for criterion in self.base_weights.keys():
            breakpoints = self.identify_breakpoints(criterion)
            if breakpoints:
                all_breakpoints[criterion] = breakpoints

        # Зберігаємо у JSON
        output = {
            'base_weights': self.base_weights,
            'sensitivity_results': full_results,
            'stability_indices': stability,
            'breakpoints': all_breakpoints
        }

        output_file = Path(output_dir) / "sensitivity_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Результати збережено: {output_file}")

        # Виводимо індекси стабільності
        print("\n" + "=" * 70)
        print("ІНДЕКСИ СТАБІЛЬНОСТІ АЛЬТЕРНАТИВ")
        print("=" * 70)
        for alt_name, index in sorted(stability.items(), key=lambda x: x[1], reverse=True):
            print(f"{alt_name}: {index:.4f} {'[Високостабільний]' if index > 0.8 else '[Середньостабільний]' if index > 0.5 else '[Низькостабільний]'}")

        # Виводимо точки перелому
        if all_breakpoints:
            print("\n" + "=" * 70)
            print("ТОЧКИ ПЕРЕЛОМУ (зміна лідера)")
            print("=" * 70)
            for criterion, breakpoints in all_breakpoints.items():
                print(f"\n{criterion}:")
                for bp in breakpoints:
                    print(f"  Вага {bp['weight']:.3f}: {bp['previous_leader']} → {bp['new_leader']}")

        return output


def example_usage():
    """Приклад використання"""

    # Приклад даних
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

    # Створюємо аналізатор
    analyzer = SensitivityAnalyzer(alternatives)

    # Виконуємо та зберігаємо результати
    analyzer.save_results()


if __name__ == "__main__":
    example_usage()

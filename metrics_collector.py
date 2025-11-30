#!/usr/bin/env python3
"""
Multi-Criteria Optimization using TOPSIS
Багатокритеріальна оптимізація методом TOPSIS
"""

import numpy as np
import json
from typing import Dict, List, Tuple

class TOPSISOptimizer:
    def __init__(self, criteria_weights: Dict[str, float] = None):
        """
        Ініціалізація оптимізатора TOPSIS
        
        Args:
            criteria_weights: Ваги критеріїв (сума має дорівнювати 1.0)
        """
        self.criteria_weights = criteria_weights or {
            'performance': 0.35,    # Продуктивність (requests/sec)
            'response_time': 0.25,  # Час відгуку
            'cpu_usage': 0.15,      # Використання CPU
            'memory_usage': 0.15,   # Використання RAM
            'cost': 0.10,           # Вартість
        }
        
        # Перевірка що сума ваг = 1.0
        total_weight = sum(self.criteria_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Сума ваг має дорівнювати 1.0, поточна: {total_weight}")
    
    def normalize_matrix(self, matrix: np.ndarray) -> np.ndarray:
        """Нормалізація матриці рішень"""
        # Векторна нормалізація
        col_sums = np.sqrt(np.sum(matrix ** 2, axis=0))
        return matrix / col_sums
    
    def calculate_weighted_matrix(self, normalized_matrix: np.ndarray, weights: np.ndarray) -> np.ndarray:
        """Обчислення зваженої нормалізованої матриці"""
        return normalized_matrix * weights
    
    def find_ideal_solutions(self, weighted_matrix: np.ndarray, 
                            benefit_criteria: List[bool]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Знаходить ідеальне та антиідеальне рішення
        
        Args:
            weighted_matrix: Зважена нормалізована матриця
            benefit_criteria: Список булевих значень (True якщо більше = краще)
        
        Returns:
            Tuple (ideal_solution, anti_ideal_solution)
        """
        ideal = np.zeros(weighted_matrix.shape[1])
        anti_ideal = np.zeros(weighted_matrix.shape[1])
        
        for j in range(weighted_matrix.shape[1]):
            if benefit_criteria[j]:
                # Для критеріїв вигоди: більше = краще
                ideal[j] = np.max(weighted_matrix[:, j])
                anti_ideal[j] = np.min(weighted_matrix[:, j])
            else:
                # Для критеріїв витрат: менше = краще
                ideal[j] = np.min(weighted_matrix[:, j])
                anti_ideal[j] = np.max(weighted_matrix[:, j])
        
        return ideal, anti_ideal
    
    def calculate_distances(self, weighted_matrix: np.ndarray, 
                           ideal: np.ndarray, 
                           anti_ideal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Обчислює відстані до ідеального та антиідеального рішення"""
        distance_to_ideal = np.sqrt(np.sum((weighted_matrix - ideal) ** 2, axis=1))
        distance_to_anti_ideal = np.sqrt(np.sum((weighted_matrix - anti_ideal) ** 2, axis=1))
        return distance_to_ideal, distance_to_anti_ideal
    
    def calculate_scores(self, distance_to_ideal: np.ndarray, 
                        distance_to_anti_ideal: np.ndarray) -> np.ndarray:
        """Обчислює фінальні оцінки близькості"""
        return distance_to_anti_ideal / (distance_to_ideal + distance_to_anti_ideal)
    
    def optimize(self, alternatives: Dict[str, Dict[str, float]]) -> Dict:
        """
        Виконує оптимізацію TOPSIS
        
        Args:
            alternatives: Словник альтернатив з їх критеріями
                Приклад: {
                    't3.micro': {'performance': 100, 'response_time': 0.05, ...},
                    't3.small': {'performance': 200, 'response_time': 0.03, ...},
                }
        
        Returns:
            Результати оптимізації з рейтингом
        """
        # Перетворення даних у матрицю
        alt_names = list(alternatives.keys())
        criteria_names = list(self.criteria_weights.keys())
        
        matrix = np.array([
            [alternatives[alt][criterion] for criterion in criteria_names]
            for alt in alt_names
        ])
        
        # Визначення типів критеріїв (більше = краще?)
        benefit_criteria = [
            True,   # performance - більше краще
            False,  # response_time - менше краще
            False,  # cpu_usage - менше краще
            False,  # memory_usage - менше краще
            False,  # cost - менше краще
        ]
        
        # Ваги як масив
        weights = np.array([self.criteria_weights[c] for c in criteria_names])
        
        # Крок 1: Нормалізація
        normalized = self.normalize_matrix(matrix)
        
        # Крок 2: Зважена матриця
        weighted = self.calculate_weighted_matrix(normalized, weights)
        
        # Крок 3: Ідеальні рішення
        ideal, anti_ideal = self.find_ideal_solutions(weighted, benefit_criteria)
        
        # Крок 4: Відстані
        dist_ideal, dist_anti_ideal = self.calculate_distances(weighted, ideal, anti_ideal)
        
        # Крок 5: Оцінки
        scores = self.calculate_scores(dist_ideal, dist_anti_ideal)
        
        # Формування результатів
        results = []
        for i, alt_name in enumerate(alt_names):
            results.append({
                'alternative': alt_name,
                'score': float(scores[i]),
                'rank': 0,  # Буде заповнено нижче
                'criteria': alternatives[alt_name]
            })
        
        # Сортування за оцінкою (більша оцінка = краще)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Додавання рангів
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
        return {
            'method': 'TOPSIS',
            'criteria_weights': self.criteria_weights,
            'results': results,
            'best_alternative': results[0]['alternative']
        }
    
    def print_results(self, optimization_results: Dict):
        """Виводить результати оптимізації"""
        print("\n" + "=" * 70)
        print("🎯 РЕЗУЛЬТАТИ БАГАТОКРИТЕРІАЛЬНОЇ ОПТИМІЗАЦІЇ (TOPSIS)")
        print("=" * 70)
        
        print("\n📊 Ваги критеріїв:")
        for criterion, weight in self.criteria_weights.items():
            print(f"  {criterion}: {weight:.2f}")
        
        print("\n🏆 Рейтинг альтернатив:")
        print("-" * 70)
        
        for result in optimization_results['results']:
            print(f"\n#{result['rank']} {result['alternative']}")
            print(f"   Оцінка TOPSIS: {result['score']:.4f}")
            print(f"   Критерії:")
            for criterion, value in result['criteria'].items():
                print(f"     - {criterion}: {value}")
        
        print("\n" + "=" * 70)
        print(f"✨ Найкращий варіант: {optimization_results['best_alternative']}")
        print("=" * 70)


def example_usage():
    """Приклад використання"""
    
    # Приклад даних (замініть на реальні дані з тестів)
    alternatives = {
        't3.micro': {
            'performance': 150,      # requests/sec
            'response_time': 0.08,   # секунди
            'cpu_usage': 45,         # відсотки
            'memory_usage': 35,      # відсотки
            'cost': 0.0104,          # $/година
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
    
    # Створення оптимізатора
    optimizer = TOPSISOptimizer()
    
    # Виконання оптимізації
    results = optimizer.optimize(alternatives)
    
    # Вивід результатів
    optimizer.print_results(results)
    
    # Збереження результатів
    with open('optimization_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n💾 Результати збережено у optimization_results.json")


if __name__ == "__main__":
    example_usage()
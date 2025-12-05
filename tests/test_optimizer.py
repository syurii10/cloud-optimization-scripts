#!/usr/bin/env python3
"""
Unit Tests для TOPSIS Optimizer
"""

import pytest
import numpy as np
import sys
import os

# Додаємо scripts до PATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from optimizer import TOPSISOptimizer


class TestTOPSISOptimizer:
    """Тести для TOPSISOptimizer"""

    def test_initialization_default_weights(self):
        """Тест ініціалізації з дефолтними вагами"""
        optimizer = TOPSISOptimizer()
        assert optimizer.criteria_weights is not None
        assert len(optimizer.criteria_weights) == 5
        assert sum(optimizer.criteria_weights.values()) == pytest.approx(1.0, rel=0.01)

    def test_initialization_custom_weights(self):
        """Тест ініціалізації з кастомними вагами"""
        custom_weights = {
            'performance': 0.4,
            'response_time': 0.3,
            'cpu_usage': 0.1,
            'memory_usage': 0.1,
            'cost': 0.1,
        }
        optimizer = TOPSISOptimizer(criteria_weights=custom_weights)
        assert optimizer.criteria_weights == custom_weights

    def test_initialization_invalid_weights(self):
        """Тест ініціалізації з невалідними вагами"""
        invalid_weights = {
            'performance': 0.5,
            'response_time': 0.3,
            'cpu_usage': 0.1,
            'memory_usage': 0.1,
            'cost': 0.2,  # Сума = 1.2
        }
        with pytest.raises(ValueError, match="Сума ваг має дорівнювати 1.0"):
            TOPSISOptimizer(criteria_weights=invalid_weights)

    def test_normalize_matrix(self):
        """Тест нормалізації матриці"""
        optimizer = TOPSISOptimizer()
        matrix = np.array([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ])
        normalized = optimizer.normalize_matrix(matrix)

        # Перевірка що нормалізована матриця має правильну форму
        assert normalized.shape == matrix.shape

        # Перевірка що сума квадратів кожного стовпця = 1
        col_sums = np.sqrt(np.sum(normalized ** 2, axis=0))
        np.testing.assert_array_almost_equal(col_sums, np.ones(3))

    def test_normalize_matrix_with_zeros(self):
        """Тест нормалізації матриці з нулями (захист від division by zero)"""
        optimizer = TOPSISOptimizer()
        matrix = np.array([
            [0, 2, 3],
            [0, 5, 6],
            [0, 8, 9]
        ])
        normalized = optimizer.normalize_matrix(matrix)

        # Перевірка що не виникло nan або inf
        assert not np.isnan(normalized).any()
        assert not np.isinf(normalized).any()

    def test_calculate_weighted_matrix(self):
        """Тест обчислення зваженої матриці"""
        optimizer = TOPSISOptimizer()
        normalized = np.array([
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ])
        weights = np.array([0.5, 0.3, 0.2])

        weighted = optimizer.calculate_weighted_matrix(normalized, weights)

        # Перевірка форми
        assert weighted.shape == normalized.shape

        # Перевірка що ваги застосовані правильно
        expected = normalized * weights
        np.testing.assert_array_almost_equal(weighted, expected)

    def test_find_ideal_solutions(self):
        """Тест знаходження ідеальних рішень"""
        optimizer = TOPSISOptimizer()
        weighted_matrix = np.array([
            [0.5, 0.2, 0.8],
            [0.3, 0.6, 0.4],
            [0.7, 0.4, 0.6],
        ])
        benefit_criteria = [True, False, True]

        ideal, anti_ideal = optimizer.find_ideal_solutions(weighted_matrix, benefit_criteria)

        # Для benefit критеріїв: ideal = max, anti_ideal = min
        assert ideal[0] == 0.7  # max для 1-го стовпця (benefit)
        assert anti_ideal[0] == 0.3  # min для 1-го стовпця

        # Для cost критеріїв: ideal = min, anti_ideal = max
        assert ideal[1] == 0.2  # min для 2-го стовпця (cost)
        assert anti_ideal[1] == 0.6  # max для 2-го стовпця

    def test_optimize_simple_case(self):
        """Тест оптимізації на простому прикладі"""
        optimizer = TOPSISOptimizer()

        alternatives = {
            'option_a': {
                'performance': 100,
                'response_time': 0.05,
                'cpu_usage': 20,
                'memory_usage': 30,
                'cost': 0.01,
            },
            'option_b': {
                'performance': 200,
                'response_time': 0.03,
                'cpu_usage': 15,
                'memory_usage': 25,
                'cost': 0.02,
            },
            'option_c': {
                'performance': 150,
                'response_time': 0.04,
                'cpu_usage': 18,
                'memory_usage': 28,
                'cost': 0.015,
            },
        }

        results = optimizer.optimize(alternatives)

        # Перевірка структури результатів
        assert 'method' in results
        assert results['method'] == 'TOPSIS'
        assert 'results' in results
        assert len(results['results']) == 3
        assert 'best_alternative' in results

        # Перевірка що є рейтинги
        for result in results['results']:
            assert 'alternative' in result
            assert 'score' in result
            assert 'rank' in result
            assert 0 <= result['score'] <= 1
            assert 1 <= result['rank'] <= 3

        # Перевірка що найкращий варіант має ранг 1
        best = results['best_alternative']
        best_result = next(r for r in results['results'] if r['alternative'] == best)
        assert best_result['rank'] == 1

    def test_optimize_empty_alternatives(self):
        """Тест оптимізації з порожнім списком альтернатив"""
        optimizer = TOPSISOptimizer()
        alternatives = {}

        with pytest.raises((ValueError, IndexError, KeyError)):
            optimizer.optimize(alternatives)

    def test_optimize_single_alternative(self):
        """Тест оптимізації з однією альтернативою"""
        optimizer = TOPSISOptimizer()
        alternatives = {
            'only_option': {
                'performance': 100,
                'response_time': 0.05,
                'cpu_usage': 20,
                'memory_usage': 30,
                'cost': 0.01,
            },
        }

        results = optimizer.optimize(alternatives)

        assert len(results['results']) == 1
        assert results['best_alternative'] == 'only_option'
        assert results['results'][0]['rank'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

#!/usr/bin/env python3
"""
Cost Prediction для AWS EC2 інстансів
Прогнозування вартості на основі historical data та usage patterns
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np


class AWSCostPredictor:
    """Прогнозування вартості AWS інфраструктури"""

    # Ціни EC2 instances (USD per hour) - eu-central-1
    INSTANCE_PRICES = {
        't3.micro': 0.0104,
        't3.small': 0.0208,
        't3.medium': 0.0416,
        't3.large': 0.0832,
        't3.xlarge': 0.1664,
        't3.2xlarge': 0.3328,
    }

    # Data transfer ціни (USD per GB)
    DATA_TRANSFER_OUT = 0.09  # Перші 10TB/month
    DATA_TRANSFER_IN = 0.0    # Завжди безкоштовно

    # EBS Storage (USD per GB-month)
    EBS_STORAGE_GP3 = 0.088

    def __init__(self):
        self.instance_prices = self.INSTANCE_PRICES.copy()

    def calculate_test_cost(self, instance_type: str, duration_seconds: int,
                           data_transfer_gb: float = 0) -> Dict:
        """
        Обчислює вартість одного тесту

        Args:
            instance_type: Тип EC2 інстансу
            duration_seconds: Тривалість тесту в секундах
            data_transfer_gb: Об'єм переданих даних (GB)

        Returns:
            Деталізована вартість
        """
        # Вартість compute
        hourly_rate = self.instance_prices.get(instance_type, 0)
        duration_hours = duration_seconds / 3600
        compute_cost = hourly_rate * duration_hours

        # Вартість data transfer
        transfer_cost = data_transfer_gb * self.DATA_TRANSFER_OUT

        # Загальна вартість
        total_cost = compute_cost + transfer_cost

        return {
            'instance_type': instance_type,
            'duration': {
                'seconds': duration_seconds,
                'hours': round(duration_hours, 4)
            },
            'costs': {
                'compute': round(compute_cost, 6),
                'data_transfer': round(transfer_cost, 6),
                'total': round(total_cost, 6)
            },
            'pricing': {
                'hourly_rate': hourly_rate,
                'data_transfer_rate': self.DATA_TRANSFER_OUT
            }
        }

    def estimate_full_test_suite_cost(self, config: Dict) -> Dict:
        """
        Оцінює вартість повного набору тестів

        Args:
            config: Конфігурація тестів
                {
                    'instances': ['t3.micro', 't3.small'],
                    'rps_levels': [500, 2000],
                    'test_duration': 60,
                    'data_transfer_per_test_gb': 0.5
                }

        Returns:
            Деталізована оцінка вартості
        """
        instances = config.get('instances', [])
        rps_levels = config.get('rps_levels', [])
        test_duration = config.get('test_duration', 60)
        data_per_test = config.get('data_transfer_per_test_gb', 0.5)

        # Кількість тестів
        num_tests = len(instances) * len(rps_levels)

        # Вартість кожного тесту
        test_costs = []
        total_compute = 0
        total_transfer = 0

        for instance in instances:
            for rps in rps_levels:
                cost = self.calculate_test_cost(
                    instance, test_duration, data_per_test
                )
                test_costs.append(cost)
                total_compute += cost['costs']['compute']
                total_transfer += cost['costs']['data_transfer']

        # Додаткові витрати
        # Client servers (завжди t3.micro)
        client_overhead = self.INSTANCE_PRICES['t3.micro'] * (test_duration / 3600) * num_tests

        # Infrastructure overhead (approximate 5 minutes setup/teardown per run)
        setup_time_hours = (5 * 60) / 3600
        setup_cost = sum(self.instance_prices.get(inst, 0) for inst in instances) * setup_time_hours

        # Загальна вартість
        total_cost = total_compute + total_transfer + client_overhead + setup_cost

        return {
            'configuration': config,
            'test_count': num_tests,
            'costs': {
                'compute': round(total_compute, 4),
                'data_transfer': round(total_transfer, 4),
                'client_overhead': round(client_overhead, 4),
                'setup_teardown': round(setup_cost, 4),
                'total': round(total_cost, 4)
            },
            'per_test': test_costs,
            'budget_impact': self._calculate_budget_impact(total_cost)
        }

    def _calculate_budget_impact(self, cost: float, total_budget: float = 120) -> Dict:
        """Обчислює вплив на бюджет"""
        percentage = (cost / total_budget) * 100
        remaining = total_budget - cost

        return {
            'total_budget': total_budget,
            'estimated_cost': round(cost, 4),
            'percentage_used': round(percentage, 2),
            'remaining': round(remaining, 4),
            'status': 'safe' if percentage < 50 else 'warning' if percentage < 80 else 'critical'
        }

    def predict_monthly_cost(self, daily_usage_hours: Dict[str, float]) -> Dict:
        """
        Прогнозує місячну вартість на основі щоденного використання

        Args:
            daily_usage_hours: {'t3.micro': 2.5, 't3.small': 1.0}

        Returns:
            Прогноз на місяць
        """
        monthly_costs = {}
        total_monthly = 0

        for instance_type, hours_per_day in daily_usage_hours.items():
            hourly_rate = self.instance_prices.get(instance_type, 0)
            daily_cost = hours_per_day * hourly_rate
            monthly_cost = daily_cost * 30

            monthly_costs[instance_type] = {
                'hours_per_day': hours_per_day,
                'hourly_rate': hourly_rate,
                'daily_cost': round(daily_cost, 4),
                'monthly_cost': round(monthly_cost, 4)
            }

            total_monthly += monthly_cost

        return {
            'period': '30 days',
            'instances': monthly_costs,
            'total_monthly_cost': round(total_monthly, 2),
            'daily_average': round(total_monthly / 30, 2)
        }

    def find_optimal_by_budget(self, budget: float, test_duration: int,
                               required_performance: int) -> List[Dict]:
        """
        Знаходить оптимальні інстанси в межах бюджету

        Args:
            budget: Доступний бюджет (USD)
            test_duration: Тривалість одного тесту (секунди)
            required_performance: Мінімальна потрібна продуктивність (RPS)

        Returns:
            Список підходящих інстансів
        """
        # Approximate performance metrics
        performance_map = {
            't3.micro': 200,
            't3.small': 400,
            't3.medium': 800,
            't3.large': 1600,
            't3.xlarge': 3200,
        }

        suitable_instances = []

        for instance_type, perf in performance_map.items():
            if perf < required_performance:
                continue

            cost = self.calculate_test_cost(instance_type, test_duration)

            if cost['costs']['total'] <= budget:
                suitable_instances.append({
                    'instance_type': instance_type,
                    'estimated_performance': perf,
                    'cost': cost['costs']['total'],
                    'efficiency': perf / cost['costs']['total'],  # RPS per dollar
                    'fits_budget': True
                })

        # Сортуємо за ефективністю
        suitable_instances.sort(key=lambda x: x['efficiency'], reverse=True)

        return suitable_instances

    def save_cost_estimate(self, config: Dict, output_file: str = "results/cost_estimate.json"):
        """Зберігає оцінку вартості"""
        from pathlib import Path

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        estimate = self.estimate_full_test_suite_cost(config)

        # Додаємо timestamp
        estimate['timestamp'] = datetime.now().isoformat()

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(estimate, f, indent=2, ensure_ascii=False)

        # Виводимо звіт
        self._print_cost_report(estimate)

        return estimate

    def _print_cost_report(self, estimate: Dict):
        """Виводить звіт про вартість"""
        print("\n" + "=" * 70)
        print("ОЦІНКА ВАРТОСТІ ТЕСТУВАННЯ")
        print("=" * 70)

        print(f"\nКонфігурація:")
        print(f"  Інстанси: {', '.join(estimate['configuration']['instances'])}")
        print(f"  RPS рівні: {', '.join(map(str, estimate['configuration']['rps_levels']))}")
        print(f"  Тривалість тесту: {estimate['configuration']['test_duration']}s")
        print(f"  Загальна кількість тестів: {estimate['test_count']}")

        costs = estimate['costs']
        print(f"\nВартість:")
        print(f"  Compute: ${costs['compute']:.4f}")
        print(f"  Data Transfer: ${costs['data_transfer']:.4f}")
        print(f"  Client Overhead: ${costs['client_overhead']:.4f}")
        print(f"  Setup/Teardown: ${costs['setup_teardown']:.4f}")
        print(f"  {'='*20}")
        print(f"  ЗАГАЛЬНА: ${costs['total']:.4f}")

        budget = estimate['budget_impact']
        print(f"\nВплив на бюджет:")
        print(f"  Бюджет: ${budget['total_budget']:.2f}")
        print(f"  Використано: {budget['percentage_used']:.2f}%")
        print(f"  Залишок: ${budget['remaining']:.2f}")
        print(f"  Статус: {budget['status'].upper()}")


def example_usage():
    """Приклад використання"""

    predictor = AWSCostPredictor()

    # Конфігурація тестів
    config = {
        'instances': ['t3.micro', 't3.small', 't3.medium'],
        'rps_levels': [500, 2000, 5000],
        'test_duration': 60,
        'data_transfer_per_test_gb': 0.1
    }

    # Оцінка вартості
    predictor.save_cost_estimate(config)

    # Пошук оптимального інстансу
    print("\n" + "=" * 70)
    print("ПОШУК ОПТИМАЛЬНОГО ІНСТАНСУ")
    print("=" * 70)

    suitable = predictor.find_optimal_by_budget(
        budget=0.01,
        test_duration=60,
        required_performance=500
    )

    print(f"\nБюджет: $0.01, Потрібна продуктивність: 500 RPS\n")
    for inst in suitable:
        print(f"{inst['instance_type']:<12} "
              f"Perf: {inst['estimated_performance']:>4} RPS  "
              f"Cost: ${inst['cost']:.6f}  "
              f"Ефективність: {inst['efficiency']:.0f} RPS/$")


if __name__ == "__main__":
    example_usage()

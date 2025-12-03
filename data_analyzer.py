#!/usr/bin/env python3
"""
Data Analyzer
Аналізує зібрані дані та створює звіт
"""

import json
import sys
import logging
import os
from typing import Dict

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json(filename: str) -> Dict:
    """
    Завантажує JSON файл з валідацією

    Args:
        filename: Шлях до JSON файлу

    Returns:
        Завантажені дані

    Raises:
        FileNotFoundError: Якщо файл не знайдено
        json.JSONDecodeError: Якщо JSON невалідний
    """
    if not os.path.exists(filename):
        logger.error(f"Файл не знайдено: {filename}")
        raise FileNotFoundError(f"Файл {filename} не існує")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"Успішно завантажено: {filename}")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Помилка парсингу JSON в {filename}: {e}")
        raise
    except Exception as e:
        logger.error(f"Помилка читання файлу {filename}: {e}")
        raise

def analyze_test_results(data: Dict) -> Dict:
    """Аналізує результати тестування"""
    return {
        'total_requests': data['total_requests'],
        'successful_requests': data['successful_requests'],
        'failed_requests': data['failed_requests'],
        'success_rate': (data['successful_requests'] / data['total_requests'] * 100) if data['total_requests'] > 0 else 0,
        'avg_response_time_ms': data['avg_response_time'] * 1000,
        'min_response_time_ms': data['min_response_time'] * 1000,
        'max_response_time_ms': data['max_response_time'] * 1000,
        'rps': data['rps'],
        'duration': data['duration']
    }

def analyze_metrics(data: Dict) -> Dict:
    """Аналізує метрики сервера"""
    metrics = data['metrics']
    
    cpu_values = [m['cpu']['percent'] for m in metrics]
    mem_values = [m['memory']['percent'] for m in metrics]
    
    return {
        'cpu': {
            'avg': sum(cpu_values) / len(cpu_values),
            'min': min(cpu_values),
            'max': max(cpu_values),
        },
        'memory': {
            'avg': sum(mem_values) / len(mem_values),
            'min': min(mem_values),
            'max': max(mem_values),
        },
        'samples': len(metrics)
    }

def create_instance_profile(test_results: Dict, metrics: Dict, instance_type: str, cost_per_hour: float) -> Dict:
    """Створює профіль інстансу для оптимізації"""
    return {
        'instance_type': instance_type,
        'performance': test_results['rps'],  # requests/sec
        'response_time': test_results['avg_response_time_ms'],  # ms
        'cpu_usage': metrics['cpu']['avg'],  # %
        'memory_usage': metrics['memory']['avg'],  # %
        'cost': cost_per_hour,  # $/hour
        'success_rate': test_results['success_rate'],  # %
    }

def print_report(test_results: Dict, metrics: Dict, instance_profile: Dict):
    """Друкує детальний звіт"""
    print("\n" + "=" * 70)
    print("📊 ЗВІТ ПРО ТЕСТУВАННЯ")
    print("=" * 70)
    
    print(f"\n🖥️  Тип інстансу: {instance_profile['instance_type']}")
    print(f"💰 Вартість: ${instance_profile['cost']:.4f}/година")
    
    print("\n📈 ПРОДУКТИВНІСТЬ:")
    print(f"  Всього запитів: {test_results['total_requests']}")
    print(f"  ✅ Успішних: {test_results['successful_requests']}")
    print(f"  ❌ Невдалих: {test_results['failed_requests']}")
    print(f"  Успішність: {test_results['success_rate']:.2f}%")
    print(f"  RPS (запитів/сек): {test_results['rps']}")
    
    print("\n⏱️  ЧАС ВІДГУКУ:")
    print(f"  Середній: {test_results['avg_response_time_ms']:.2f} мс")
    print(f"  Мінімум: {test_results['min_response_time_ms']:.2f} мс")
    print(f"  Максимум: {test_results['max_response_time_ms']:.2f} мс")
    
    print("\n💻 ВИКОРИСТАННЯ РЕСУРСІВ:")
    print(f"  CPU:")
    print(f"    Середнє: {metrics['cpu']['avg']:.2f}%")
    print(f"    Мінімум: {metrics['cpu']['min']:.2f}%")
    print(f"    Максимум: {metrics['cpu']['max']:.2f}%")
    print(f"  RAM:")
    print(f"    Середнє: {metrics['memory']['avg']:.2f}%")
    print(f"    Мінімум: {metrics['memory']['min']:.2f}%")
    print(f"    Максимум: {metrics['memory']['max']:.2f}%")
    
    print("\n💡 ВИСНОВКИ:")
    if metrics['cpu']['avg'] < 20:
        print("  ⚠️  CPU недовантажений - можна використати менший інстанс")
    elif metrics['cpu']['avg'] > 80:
        print("  ⚠️  CPU перевантажений - потрібен більший інстанс")
    else:
        print("  ✅ CPU використовується оптимально")
    
    if metrics['memory']['avg'] < 30:
        print("  ⚠️  RAM недовантажена - можна використати менший інстанс")
    elif metrics['memory']['avg'] > 80:
        print("  ⚠️  RAM перевантажена - потрібен більший інстанс")
    else:
        print("  ✅ RAM використовується оптимально")
    
    print("=" * 70)

def main():
    """Головна функція"""
    if len(sys.argv) < 3:
        print("Використання: python data_analyzer.py <test_results.json> <metrics.json> [instance_type] [cost_per_hour]")
        print("Приклад: python data_analyzer.py test_results_client.json metrics_target.json t3.small 0.0208")
        sys.exit(1)
    
    test_file = sys.argv[1]
    metrics_file = sys.argv[2]
    instance_type = sys.argv[3] if len(sys.argv) > 3 else "t3.small"
    cost = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0208
    
    # Завантаження даних
    print("📂 Завантаження даних...")
    test_data = load_json(test_file)
    metrics_data = load_json(metrics_file)
    
    # Аналіз
    print("🔍 Аналіз даних...")
    test_results = analyze_test_results(test_data)
    metrics = analyze_metrics(metrics_data)
    instance_profile = create_instance_profile(test_results, metrics, instance_type, cost)
    
    # Звіт
    print_report(test_results, metrics, instance_profile)
    
    # Збереження профілю для оптимізації
    output_file = f'instance_profile_{instance_type}.json'
    with open(output_file, 'w') as f:
        json.dump({
            'test_results': test_results,
            'metrics': metrics,
            'instance_profile': instance_profile
        }, f, indent=2)
    
    print(f"\n💾 Профіль збережено: {output_file}")

if __name__ == "__main__":
    main()
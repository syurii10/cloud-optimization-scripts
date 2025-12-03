#!/usr/bin/env python3
"""
System Metrics Collector
Збирає метрики CPU, RAM та Network під час навантажувального тестування
"""

import psutil
import json
import time
import sys
import logging
from datetime import datetime
from typing import Dict, List

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self, interval: int = 1, duration: int = 90, streaming_file: str = None):
        """
        Ініціалізація збирача метрик

        Args:
            interval: Інтервал між збором метрик (секунди) - за замовчуванням 1 сек для деталізації
            duration: Загальна тривалість збору (секунди)
            streaming_file: Файл для Real-Time streaming (current_test.json)
        """
        self.interval = interval
        self.duration = duration
        self.streaming_file = streaming_file
        self.metrics = []

        # Для відстеження пікових значень (WOW-ефект!)
        self.peak_cpu = 0.0
        self.peak_memory = 0.0
        self.critical_moments = []  # Моменти коли CPU > 90% або Memory > 90%

    def collect_current_metrics(self) -> Dict:
        """Збирає поточні метрики системи з високою деталізацією"""
        try:
            # CPU метрики - загальний та per-core
            cpu_percent = psutil.cpu_percent(interval=0.1)  # Швидший збір
            cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)

            # Memory метрики
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk метрики
            disk = psutil.disk_usage('/')

            # Network метрики
            net_io = psutil.net_io_counters()

            # Load average (для Linux)
            try:
                load_avg = psutil.getloadavg()
            except (AttributeError, OSError):
                load_avg = (0, 0, 0)  # Windows не підтримує

            # Оновлення пікових значень
            if cpu_percent > self.peak_cpu:
                self.peak_cpu = cpu_percent
            if memory.percent > self.peak_memory:
                self.peak_memory = memory.percent

            # Позначаємо критичний момент
            is_critical = cpu_percent > 90 or memory.percent > 90

            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'per_core': cpu_per_core,
                    'count': psutil.cpu_count(),
                    'count_logical': psutil.cpu_count(logical=True),
                    'load_avg_1m': load_avg[0],
                    'load_avg_5m': load_avg[1],
                    'load_avg_15m': load_avg[2]
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free,
                    'swap_total': swap.total,
                    'swap_used': swap.used,
                    'swap_percent': swap.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv,
                    'errors_in': net_io.errin,
                    'errors_out': net_io.errout,
                    'drops_in': net_io.dropin,
                    'drops_out': net_io.dropout
                },
                'is_critical': is_critical
            }

            # Зберігаємо критичні моменти
            if is_critical:
                self.critical_moments.append({
                    'timestamp': metrics['timestamp'],
                    'cpu': cpu_percent,
                    'memory': memory.percent
                })

            return metrics
        except Exception as e:
            logger.error(f"Помилка збору метрик: {e}")
            return None

    def update_streaming_file(self, current_metrics: Dict, test_info: Dict = None):
        """
        Оновлює файл для Real-Time streaming (WOW-ефект для dashboard!)

        Args:
            current_metrics: Поточні метрики
            test_info: Інформація про тест (instance_type, rps, тощо)
        """
        if not self.streaming_file:
            return

        try:
            cpu_values = [m['cpu']['percent'] for m in self.metrics] if self.metrics else []
            mem_values = [m['memory']['percent'] for m in self.metrics] if self.metrics else []

            streaming_data = {
                'status': 'testing',
                'timestamp': current_metrics['timestamp'],
                'test_info': test_info or {},
                'current': {
                    'cpu': current_metrics['cpu']['percent'],
                    'memory': current_metrics['memory']['percent'],
                    'is_critical': current_metrics['is_critical']
                },
                'statistics': {
                    'cpu_avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                    'cpu_peak': self.peak_cpu,
                    'memory_avg': sum(mem_values) / len(mem_values) if mem_values else 0,
                    'memory_peak': self.peak_memory,
                    'samples_count': len(self.metrics),
                    'critical_moments_count': len(self.critical_moments)
                },
                'timeline': self.metrics[-50:] if len(self.metrics) > 50 else self.metrics  # Останні 50 точок для графіка
            }

            with open(self.streaming_file, 'w') as f:
                json.dump(streaming_data, f, indent=2)

        except Exception as e:
            logger.error(f"Помилка оновлення streaming файлу: {e}")

    def collect(self) -> List[Dict]:
        """
        Збирає метрики протягом заданого часу

        Returns:
            Список зібраних метрик
        """
        logger.info(f"Початок збору метрик")
        logger.info(f"Інтервал: {self.interval}с, Тривалість: {self.duration}с")

        start_time = time.time()
        end_time = start_time + self.duration
        sample_count = 0

        while time.time() < end_time:
            metrics = self.collect_current_metrics()

            if metrics:
                self.metrics.append(metrics)
                sample_count += 1

                # Real-Time streaming для dashboard WOW-ефекту!
                self.update_streaming_file(metrics)

                remaining = int(end_time - time.time())

                logger.info(
                    f"Зразок #{sample_count} | "
                    f"CPU: {metrics['cpu']['percent']:.1f}% | "
                    f"RAM: {metrics['memory']['percent']:.1f}% | "
                    f"Залишилось: {remaining}с"
                )

            time.sleep(self.interval)

        logger.info(f"Збір завершено. Всього зразків: {len(self.metrics)}")
        return self.metrics

    def calculate_percentiles(self, values: List[float]) -> Dict:
        """Розраховує percentiles для наочності (p50, p95, p99)"""
        if not values:
            return {'p50': 0, 'p95': 0, 'p99': 0}

        sorted_values = sorted(values)
        length = len(sorted_values)

        def percentile(p):
            index = int(length * p / 100)
            return sorted_values[min(index, length - 1)]

        return {
            'p50': percentile(50),  # Median
            'p95': percentile(95),  # 95th percentile
            'p99': percentile(99)   # 99th percentile (worst case)
        }

    def save_to_file(self, filename: str = 'metrics.json'):
        """Зберігає метрики у файл з аналітикою"""
        try:
            # Розрахунок статистики
            cpu_values = [m['cpu']['percent'] for m in self.metrics]
            mem_values = [m['memory']['percent'] for m in self.metrics]

            cpu_percentiles = self.calculate_percentiles(cpu_values)
            mem_percentiles = self.calculate_percentiles(mem_values)

            output = {
                'collection_info': {
                    'interval': self.interval,
                    'duration': self.duration,
                    'samples_count': len(self.metrics),
                    'start_time': self.metrics[0]['timestamp'] if self.metrics else None,
                    'end_time': self.metrics[-1]['timestamp'] if self.metrics else None
                },
                'summary': {
                    'cpu': {
                        'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                        'min': min(cpu_values) if cpu_values else 0,
                        'max': max(cpu_values) if cpu_values else 0,
                        'peak': self.peak_cpu,
                        'percentiles': cpu_percentiles
                    },
                    'memory': {
                        'avg': sum(mem_values) / len(mem_values) if mem_values else 0,
                        'min': min(mem_values) if mem_values else 0,
                        'max': max(mem_values) if mem_values else 0,
                        'peak': self.peak_memory,
                        'percentiles': mem_percentiles
                    },
                    'critical_moments_count': len(self.critical_moments),
                    'critical_moments': self.critical_moments
                },
                'metrics': self.metrics
            }

            with open(filename, 'w') as f:
                json.dump(output, f, indent=2)

            logger.info(f"Метрики збережено у файл: {filename}")
            return True
        except Exception as e:
            logger.error(f"Помилка збереження метрик: {e}")
            return False

    def print_summary(self):
        """Виводить розширену підсумкову статистику з WOW-ефектом"""
        if not self.metrics:
            logger.warning("Немає зібраних метрик для відображення")
            return

        cpu_values = [m['cpu']['percent'] for m in self.metrics]
        mem_values = [m['memory']['percent'] for m in self.metrics]

        cpu_percentiles = self.calculate_percentiles(cpu_values)
        mem_percentiles = self.calculate_percentiles(mem_values)

        print("\n" + "=" * 70)
        print("📊 РОЗШИРЕНИЙ ПІДСУМОК МЕТРИК (для магістерської роботи)")
        print("=" * 70)
        print(f"⏱️  Всього зразків: {len(self.metrics)} (інтервал: {self.interval}с)")
        print(f"🔥 Критичних моментів (CPU/RAM > 90%): {len(self.critical_moments)}")

        print(f"\n💻 CPU НАВАНТАЖЕННЯ:")
        print(f"  ├─ Середнє:  {sum(cpu_values) / len(cpu_values):.2f}%")
        print(f"  ├─ Мінімум:  {min(cpu_values):.2f}%")
        print(f"  ├─ Максимум: {max(cpu_values):.2f}% {'🔥 КРИТИЧНО!' if max(cpu_values) > 90 else ''}")
        print(f"  ├─ p50 (median): {cpu_percentiles['p50']:.2f}%")
        print(f"  ├─ p95: {cpu_percentiles['p95']:.2f}%")
        print(f"  └─ p99 (worst): {cpu_percentiles['p99']:.2f}%")

        print(f"\n🧠 MEMORY (RAM) ВИКОРИСТАННЯ:")
        print(f"  ├─ Середнє:  {sum(mem_values) / len(mem_values):.2f}%")
        print(f"  ├─ Мінімум:  {min(mem_values):.2f}%")
        print(f"  ├─ Максимум: {max(mem_values):.2f}% {'🔥 КРИТИЧНО!' if max(mem_values) > 90 else ''}")
        print(f"  ├─ p50 (median): {mem_percentiles['p50']:.2f}%")
        print(f"  ├─ p95: {mem_percentiles['p95']:.2f}%")
        print(f"  └─ p99 (worst): {mem_percentiles['p99']:.2f}%")

        if self.critical_moments:
            print(f"\n⚠️  КРИТИЧНІ МОМЕНТИ:")
            for i, moment in enumerate(self.critical_moments[:5], 1):  # Показуємо перші 5
                print(f"  {i}. {moment['timestamp']} - CPU: {moment['cpu']:.1f}%, RAM: {moment['memory']:.1f}%")
            if len(self.critical_moments) > 5:
                print(f"  ... та ще {len(self.critical_moments) - 5} моментів")

        print("=" * 70)


def main():
    """Основна функція"""
    if len(sys.argv) < 3:
        print("Використання: python3 metrics_collector.py <INTERVAL> <DURATION> [OUTPUT_FILE] [STREAMING_FILE]")
        print("Приклад: python3 metrics_collector.py 1 90 metrics_target.json current_test.json")
        sys.exit(1)

    try:
        interval = int(sys.argv[1])
        duration = int(sys.argv[2])
        output_file = sys.argv[3] if len(sys.argv) > 3 else 'metrics.json'
        streaming_file = sys.argv[4] if len(sys.argv) > 4 else None

        if interval <= 0 or duration <= 0:
            raise ValueError("Інтервал та тривалість мають бути додатними числами")

        collector = MetricsCollector(interval, duration, streaming_file)

        # Збір метрик
        collector.collect()

        # Підсумок
        collector.print_summary()

        # Збереження
        collector.save_to_file(output_file)

    except KeyboardInterrupt:
        logger.info("\n⚠️ Збір метрик перервано користувачем")
        if collector.metrics:
            collector.print_summary()
            collector.save_to_file(output_file)
    except ValueError as e:
        logger.error(f"Помилка параметрів: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Неочікувана помилка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

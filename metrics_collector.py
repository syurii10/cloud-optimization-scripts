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
    def __init__(self, interval: int = 5, duration: int = 90):
        """
        Ініціалізація збирача метрик

        Args:
            interval: Інтервал між збором метрик (секунди)
            duration: Загальна тривалість збору (секунди)
        """
        self.interval = interval
        self.duration = duration
        self.metrics = []

    def collect_current_metrics(self) -> Dict:
        """Збирає поточні метрики системи"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Network метрики (опціонально)
            net_io = psutil.net_io_counters()

            return {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
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
                    'packets_recv': net_io.packets_recv
                }
            }
        except Exception as e:
            logger.error(f"Помилка збору метрик: {e}")
            return None

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

    def save_to_file(self, filename: str = 'metrics.json'):
        """Зберігає метрики у файл"""
        try:
            output = {
                'collection_info': {
                    'interval': self.interval,
                    'duration': self.duration,
                    'samples_count': len(self.metrics),
                    'start_time': self.metrics[0]['timestamp'] if self.metrics else None,
                    'end_time': self.metrics[-1]['timestamp'] if self.metrics else None
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
        """Виводить підсумкову статистику"""
        if not self.metrics:
            logger.warning("Немає зібраних метрик для відображення")
            return

        cpu_values = [m['cpu']['percent'] for m in self.metrics]
        mem_values = [m['memory']['percent'] for m in self.metrics]

        print("\n" + "=" * 60)
        print("📊 ПІДСУМОК МЕТРИК")
        print("=" * 60)
        print(f"Всього зразків: {len(self.metrics)}")
        print(f"\n💻 CPU:")
        print(f"  Середнє: {sum(cpu_values) / len(cpu_values):.2f}%")
        print(f"  Мінімум: {min(cpu_values):.2f}%")
        print(f"  Максимум: {max(cpu_values):.2f}%")
        print(f"\n🧠 RAM:")
        print(f"  Середнє: {sum(mem_values) / len(mem_values):.2f}%")
        print(f"  Мінімум: {min(mem_values):.2f}%")
        print(f"  Максимум: {max(mem_values):.2f}%")
        print("=" * 60)


def main():
    """Основна функція"""
    if len(sys.argv) < 3:
        print("Використання: python3 metrics_collector.py <INTERVAL> <DURATION> [OUTPUT_FILE]")
        print("Приклад: python3 metrics_collector.py 5 90 metrics_target.json")
        sys.exit(1)

    try:
        interval = int(sys.argv[1])
        duration = int(sys.argv[2])
        output_file = sys.argv[3] if len(sys.argv) > 3 else 'metrics.json'

        if interval <= 0 or duration <= 0:
            raise ValueError("Інтервал та тривалість мають бути додатними числами")

        collector = MetricsCollector(interval, duration)

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

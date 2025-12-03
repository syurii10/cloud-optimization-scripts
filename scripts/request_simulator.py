#!/usr/bin/env python3
"""
HTTP Request Simulator
Симулює HTTP запити до цільового сервера
"""

import asyncio
import aiohttp
import time
import json
import sys
import logging
from datetime import datetime
from typing import Dict, List
from urllib.parse import urlparse

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RequestSimulator:
    MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10MB максимальний розмір відповіді
    MAX_CONCURRENT_REQUESTS = 1000  # Максимальна кількість паралельних запитів

    def __init__(self, target_url: str, requests_per_second: int = 100, duration: int = 60):
        """
        Ініціалізація симулятора запитів

        Args:
            target_url: URL цільового сервера
            requests_per_second: Кількість запитів на секунду
            duration: Тривалість тесту в секундах

        Raises:
            ValueError: Якщо параметри невалідні
        """
        # Валідація URL
        parsed = urlparse(target_url)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError(f"Невалідний URL: {target_url}")

        # Валідація параметрів
        if requests_per_second <= 0 or requests_per_second > self.MAX_CONCURRENT_REQUESTS:
            raise ValueError(f"RPS має бути між 1 та {self.MAX_CONCURRENT_REQUESTS}")

        if duration <= 0 or duration > 3600:
            raise ValueError("Тривалість має бути між 1 та 3600 секунд")

        self.target_url = target_url
        self.rps = requests_per_second
        self.duration = duration
        self.results = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'errors': []
        }

        logger.info(f"Ініціалізовано RequestSimulator: {target_url}, RPS={requests_per_second}, Duration={duration}s")
    
    async def send_request(self, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore) -> Dict:
        """
        Відправляє один HTTP запит з обмеженням розміру відповіді

        Args:
            session: aiohttp клієнтська сесія
            semaphore: Семафор для контролю паралелізму

        Returns:
            Словник з результатами запиту
        """
        start_time = time.time()
        async with semaphore:
            try:
                async with session.get(
                    self.target_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    # Читаємо відповідь з обмеженням розміру
                    content_length = response.headers.get('Content-Length')
                    if content_length and int(content_length) > self.MAX_RESPONSE_SIZE:
                        logger.warning(f"Відповідь занадто велика: {content_length} bytes")
                        return {
                            'success': False,
                            'error': 'Response too large',
                            'response_time': time.time() - start_time
                        }

                    await response.text()
                    response_time = time.time() - start_time

                    return {
                        'success': response.status == 200,
                        'status_code': response.status,
                        'response_time': response_time
                    }

            except asyncio.TimeoutError:
                logger.debug(f"Timeout для запиту до {self.target_url}")
                return {
                    'success': False,
                    'error': 'Timeout',
                    'response_time': time.time() - start_time
                }
            except aiohttp.ClientError as e:
                logger.debug(f"Client error: {e}")
                return {
                    'success': False,
                    'error': f'ClientError: {str(e)}',
                    'response_time': time.time() - start_time
                }
            except Exception as e:
                logger.error(f"Неочікувана помилка: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': str(e),
                    'response_time': time.time() - start_time
                }
    
    async def run_simulation(self):
        """Запускає симуляцію HTTP запитів"""
        logger.info(f"🚀 Початок симуляції запитів")
        logger.info(f"📊 Цільовий сервер: {self.target_url}")
        logger.info(f"⚡ Запитів/сек: {self.rps}")
        logger.info(f"⏱️ Тривалість: {self.duration}с")
        print("-" * 50)

        end_time = time.time() + self.duration

        # Семафор для контролю паралелізму
        semaphore = asyncio.Semaphore(min(self.rps, 500))

        connector = aiohttp.TCPConnector(limit=500, limit_per_host=500)
        async with aiohttp.ClientSession(connector=connector) as session:
            while time.time() < end_time:
                batch_start = time.time()

                # Відправляємо запити пачками з семафором
                tasks = [self.send_request(session, semaphore) for _ in range(self.rps)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Обробка результатів
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Exception в gather: {result}", exc_info=result)
                        self.results['total_requests'] += 1
                        self.results['failed_requests'] += 1
                        self.results['errors'].append(str(result))
                    elif isinstance(result, dict):
                        self.results['total_requests'] += 1

                        if result['success']:
                            self.results['successful_requests'] += 1
                            self.results['response_times'].append(result['response_time'])
                        else:
                            self.results['failed_requests'] += 1
                            if 'error' in result:
                                self.results['errors'].append(result['error'])

                # Виводимо прогрес
                elapsed = int(time.time() - (end_time - self.duration))
                if elapsed % 10 == 0:
                    success_rate = (self.results['successful_requests'] / max(self.results['total_requests'], 1)) * 100
                    avg_response = sum(self.results['response_times']) / max(len(self.results['response_times']), 1) if self.results['response_times'] else 0
                    logger.info(f"⏳ {elapsed}с | Успішних: {self.results['successful_requests']} | "
                          f"Успішність: {success_rate:.1f}% | Avg Response: {avg_response:.3f}с")

                # Чекаємо до наступної пачки
                batch_time = time.time() - batch_start
                if batch_time < 1.0:
                    await asyncio.sleep(1.0 - batch_time)
    
    def print_summary(self):
        """Виводить підсумкову статистику"""
        print("\n" + "=" * 50)
        print("📊 РЕЗУЛЬТАТИ ТЕСТУВАННЯ")
        print("=" * 50)
        
        print(f"Всього запитів: {self.results['total_requests']}")
        print(f"✅ Успішних: {self.results['successful_requests']}")
        print(f"❌ Невдалих: {self.results['failed_requests']}")
        
        if self.results['response_times']:
            avg_time = sum(self.results['response_times']) / len(self.results['response_times'])
            min_time = min(self.results['response_times'])
            max_time = max(self.results['response_times'])
            
            # Обчислення перцентилів
            sorted_times = sorted(self.results['response_times'])
            p50 = sorted_times[len(sorted_times) // 2]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
            
            print(f"\n⏱️  Час відгуку:")
            print(f"  Середній: {avg_time:.3f}с")
            print(f"  Мін: {min_time:.3f}с")
            print(f"  Макс: {max_time:.3f}с")
            print(f"  P50: {p50:.3f}с")
            print(f"  P95: {p95:.3f}с")
            print(f"  P99: {p99:.3f}с")
        
        success_rate = (self.results['successful_requests'] / max(self.results['total_requests'], 1)) * 100
        print(f"\n✨ Успішність: {success_rate:.2f}%")
        print("=" * 50)
    
    def save_results(self, filename: str = 'test_results.json'):
        """Зберігає результати у файл"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'target_url': self.target_url,
            'rps': self.rps,
            'duration': self.duration,
            'total_requests': self.results['total_requests'],
            'successful_requests': self.results['successful_requests'],
            'failed_requests': self.results['failed_requests'],
            'avg_response_time': sum(self.results['response_times']) / max(len(self.results['response_times']), 1) if self.results['response_times'] else 0,
            'min_response_time': min(self.results['response_times']) if self.results['response_times'] else 0,
            'max_response_time': max(self.results['response_times']) if self.results['response_times'] else 0,
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Результати збережено: {filename}")


async def main():
    """Основна функція"""
    if len(sys.argv) < 2:
        print("Використання: python request_simulator.py <TARGET_URL> [RPS] [DURATION]")
        print("Приклад: python request_simulator.py http://18.159.112.169 100 60")
        sys.exit(1)
    
    target_url = sys.argv[1]
    rps = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    duration = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    
    simulator = RequestSimulator(target_url, rps, duration)
    
    try:
        await simulator.run_simulation()
        simulator.print_summary()
        simulator.save_results()
    except KeyboardInterrupt:
        print("\n\n⚠️  Тест перервано користувачем")
        simulator.print_summary()
        simulator.save_results()


if __name__ == "__main__":
    asyncio.run(main())
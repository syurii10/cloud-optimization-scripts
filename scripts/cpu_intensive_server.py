#!/usr/bin/env python3
"""
CPU-Intensive HTTP Server для навантажувальних тестів
Виконує обчислювальні задачі при кожному запиті для генерації CPU навантаження
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import hashlib
import json
import time
import socket
from urllib.parse import urlparse, parse_qs

class CPUIntensiveHandler(BaseHTTPRequestHandler):
    """HTTP обробник з CPU-intensive операціями"""

    def do_GET(self):
        """Обробка GET запитів"""
        # Парсимо URL для отримання параметрів
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)

        # Отримуємо складність обчислень (за замовчуванням 10000)
        complexity = int(query_params.get('complexity', [10000])[0])

        # CPU-intensive обчислення: хешування
        start_time = time.time()
        result = self.perform_cpu_intensive_task(complexity)
        processing_time = time.time() - start_time

        # Формуємо відповідь
        response_data = {
            'status': 'success',
            'server': socket.gethostname(),
            'complexity': complexity,
            'result': result,
            'processing_time_ms': round(processing_time * 1000, 2),
            'timestamp': time.time()
        }

        # Відправляємо відповідь
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())

    def do_POST(self):
        """Обробка POST запитів"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length)

        # Виконуємо обчислення
        result = self.perform_cpu_intensive_task(15000)

        response_data = {
            'status': 'success',
            'method': 'POST',
            'result': result
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())

    def perform_cpu_intensive_task(self, iterations):
        """
        Виконує CPU-intensive обчислення

        Args:
            iterations: Кількість ітерацій хешування

        Returns:
            Результуючий хеш
        """
        # Серія SHA256 хешувань
        data = b"cloud-optimization-test-data"

        for i in range(iterations):
            hasher = hashlib.sha256()
            hasher.update(data + str(i).encode())
            data = hasher.digest()

        # Додаткове обчислення: сума квадратів
        sum_squares = sum(i**2 for i in range(1000))

        return {
            'hash': data.hex()[:16],
            'iterations': iterations,
            'sum_squares': sum_squares
        }

    def log_message(self, format, *args):
        """Логування запитів"""
        # Виводимо логи у стандартний формат
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(port=8080):
    """
    Запускає HTTP сервер

    Args:
        port: Порт для прослуховування
    """
    server_address = ('', port)
    httpd = HTTPServer(server_address, CPUIntensiveHandler)

    print("=" * 60)
    print(f"CPU-Intensive HTTP Server запущено")
    print(f"Порт: {port}")
    print(f"Hostname: {socket.gethostname()}")
    print("=" * 60)
    print()
    print("Приклади запитів:")
    print(f"  curl http://localhost:{port}/")
    print(f"  curl http://localhost:{port}/?complexity=5000")
    print(f"  curl http://localhost:{port}/?complexity=20000")
    print()
    print("Натисніть Ctrl+C для зупинки")
    print()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[STOPPED] Сервер зупинено")
        httpd.shutdown()


if __name__ == "__main__":
    import sys

    # Читаємо порт з аргументів командного рядка
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

    run_server(port)

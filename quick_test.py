#!/usr/bin/env python3
"""
Швидкий тест для перевірки змін
Тестує тільки t3.micro @ 500 RPS
"""

import subprocess
import time
import json
import os
from datetime import datetime
from pathlib import Path
import boto3

class QuickTest:
    def __init__(self):
        self.terraform_dir = Path("terraform")
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)

        self.instance_type = 't3.micro'
        self.rps = 500
        self.test_duration = 60

        try:
            self.ec2_client = boto3.client('ec2', region_name='eu-central-1')
        except Exception as e:
            print(f"[WARN] Не вдалося створити EC2 клієнт: {e}")
            self.ec2_client = None

    def log(self, message, level="INFO"):
        """Логування"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {
            "INFO": "[INFO]",
            "SUCCESS": "[OK]",
            "ERROR": "[ERROR]",
            "WARN": "[WARN]",
            "PROGRESS": "[...]"
        }
        try:
            print(f"[{timestamp}] {symbols.get(level, '[INFO]')} {message}")
        except UnicodeEncodeError:
            safe_message = message.encode('ascii', 'replace').decode('ascii')
            print(f"[{timestamp}] {symbols.get(level, '[INFO]')} {safe_message}")

    def run_command(self, command, cwd=None):
        """Виконання команди"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timeout"
        except Exception as e:
            return False, "", str(e)

    def terraform_init(self):
        """Ініціалізація Terraform"""
        self.log("Ініціалізація Terraform...")
        success, stdout, stderr = self.run_command("terraform init", cwd=self.terraform_dir)
        if success:
            self.log("Terraform ініціалізовано", "SUCCESS")
        else:
            self.log(f"Помилка: {stderr}", "ERROR")
            raise Exception("Terraform init failed")

    def deploy_infrastructure(self):
        """Розгортання інфраструктури"""
        self.log(f"Розгортання {self.instance_type}...", "PROGRESS")

        success, stdout, stderr = self.run_command(
            f'terraform apply -auto-approve -var="target_server_instance_type={self.instance_type}"',
            cwd=self.terraform_dir
        )

        if not success:
            self.log(f"Помилка: {stderr}", "ERROR")
            return None

        success, stdout, stderr = self.run_command("terraform output -json", cwd=self.terraform_dir)

        if success:
            outputs = json.loads(stdout)
            self.log(f"Інфраструктура розгорнута", "SUCCESS")
            return outputs
        else:
            self.log("Не вдалося отримати outputs", "ERROR")
            return None

    def wait_for_server_ready(self, ip_address):
        """Очікування готовності сервера"""
        self.log(f"Очікування готовності {ip_address}...", "PROGRESS")

        # Перевірка SSH
        for attempt in range(40):
            try:
                success, stdout, _ = self.run_command(
                    f'ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes ubuntu@{ip_address} "echo ready"'
                )

                if success and "ready" in stdout:
                    self.log(f"SSH працює!", "SUCCESS")
                    break
            except Exception as e:
                pass

            if attempt < 39:
                time.sleep(15)
        else:
            self.log(f"Сервер не відповідає", "ERROR")
            return False

        # Очікування user_data
        self.log("Очікування ініціалізації (60 сек)...", "PROGRESS")
        time.sleep(60)

        self.log(f"Сервер готовий!", "SUCCESS")
        return True

    def run_test(self, target_ip, client_ip, target_private_ip):
        """Запуск тесту"""
        self.log(f"Тест: {self.instance_type} @ {self.rps} RPS", "PROGRESS")

        # Запуск metrics_collector
        self.log("Запуск збору метрик...", "INFO")
        # ВИПРАВЛЕНО: передаємо metrics.json як 3-й аргумент
        ssh_command = (
            f'ssh -o StrictHostKeyChecking=no -f ubuntu@{target_ip} '
            f'"bash -c \'cd /home/ubuntu/scripts && python3 metrics_collector.py 1 90 metrics.json > metrics.log 2>&1 &\'"'
        )
        self.run_command(ssh_command)
        time.sleep(5)

        # Запуск request_simulator
        self.log(f"Запуск навантаження {self.rps} RPS...", "INFO")
        ssh_command = (
            f'ssh -o StrictHostKeyChecking=no ubuntu@{client_ip} '
            f'"cd /home/ubuntu/scripts && python3 request_simulator.py http://{target_private_ip} {self.rps} {self.test_duration}"'
        )
        success, stdout, stderr = self.run_command(ssh_command)

        if not success:
            self.log(f"Помилка: {stderr}", "ERROR")
            return None

        self.log("Навантаження завершено", "SUCCESS")
        time.sleep(10)

        # Завантаження результатів
        self.log("Завантаження результатів...", "PROGRESS")

        test_file = self.results_dir / f"test_{self.instance_type}_{self.rps}rps.json"
        metrics_file = self.results_dir / f"metrics_{self.instance_type}_{self.rps}rps.json"

        self.run_command(
            f"scp -o StrictHostKeyChecking=no ubuntu@{client_ip}:/home/ubuntu/scripts/test_results.json {test_file}"
        )
        self.run_command(
            f"scp -o StrictHostKeyChecking=no ubuntu@{target_ip}:/home/ubuntu/scripts/metrics.json {metrics_file}"
        )

        if test_file.exists() and metrics_file.exists():
            self.log("Результати завантажено!", "SUCCESS")
            return test_file, metrics_file
        else:
            self.log("Не вдалося завантажити результати", "ERROR")
            return None

    def destroy_infrastructure(self):
        """Знищення інфраструктури"""
        self.log("Знищення інфраструктури...", "PROGRESS")
        success, stdout, stderr = self.run_command("terraform destroy -auto-approve", cwd=self.terraform_dir)

        if success:
            self.log("Інфраструктура знищена", "SUCCESS")
        else:
            self.log(f"Помилка: {stderr}", "WARN")

    def show_results(self, test_file, metrics_file):
        """Показати результати"""
        self.log("=" * 70)
        self.log("РЕЗУЛЬТАТИ ШВИДКОГО ТЕСТУ")
        self.log("=" * 70)

        try:
            with open(test_file) as f:
                test_data = json.load(f)
            with open(metrics_file) as f:
                metrics_data = json.load(f)

            # Test results
            print(f"\n🧪 ТЕСТ НАВАНТАЖЕННЯ:")
            print(f"  ├─ Всього запитів: {test_data.get('total_requests', 0)}")
            print(f"  ├─ Успішних: {test_data.get('successful_requests', 0)}")
            print(f"  ├─ Помилок: {test_data.get('failed_requests', 0)}")
            print(f"  ├─ Success rate: {test_data.get('successful_requests', 0) / test_data.get('total_requests', 1) * 100:.1f}%")
            print(f"  └─ Avg response time: {test_data.get('avg_response_time', 0)*1000:.1f}ms")

            # Metrics summary
            summary = metrics_data.get('summary', {})
            cpu = summary.get('cpu', {})
            mem = summary.get('memory', {})

            print(f"\n💻 CPU МЕТРИКИ:")
            print(f"  ├─ Середнє: {cpu.get('avg', 0):.1f}%")
            print(f"  ├─ Максимум: {cpu.get('max', 0):.1f}% {'🔥' if cpu.get('max', 0) > 90 else ''}")
            print(f"  ├─ p50: {cpu.get('percentiles', {}).get('p50', 0):.1f}%")
            print(f"  ├─ p95: {cpu.get('percentiles', {}).get('p95', 0):.1f}%")
            print(f"  └─ p99: {cpu.get('percentiles', {}).get('p99', 0):.1f}%")

            print(f"\n🧠 MEMORY МЕТРИКИ:")
            print(f"  ├─ Середнє: {mem.get('avg', 0):.1f}%")
            print(f"  ├─ Максимум: {mem.get('max', 0):.1f}% {'🔥' if mem.get('max', 0) > 90 else ''}")
            print(f"  ├─ p50: {mem.get('percentiles', {}).get('p50', 0):.1f}%")
            print(f"  ├─ p95: {mem.get('percentiles', {}).get('p95', 0):.1f}%")
            print(f"  └─ p99: {mem.get('percentiles', {}).get('p99', 0):.1f}%")

            critical = summary.get('critical_moments_count', 0)
            print(f"\n⚠️  Критичних моментів (CPU/RAM > 90%): {critical}")

            samples = metrics_data.get('collection_info', {}).get('samples_count', 0)
            interval = metrics_data.get('collection_info', {}).get('interval', 0)
            print(f"📊 Зібрано зразків: {samples} (інтервал: {interval}с)")

        except Exception as e:
            self.log(f"Помилка відображення результатів: {e}", "ERROR")

    def run(self):
        """Запуск швидкого тесту"""
        print("""
    ========================================================
       ШВИДКИЙ ТЕСТ - t3.micro @ 500 RPS
       Перевірка нових метрик та RPS рівнів
    ========================================================
        """)

        start_time = time.time()

        try:
            # Ініціалізація
            self.terraform_init()

            # Розгортання
            outputs = self.deploy_infrastructure()
            if not outputs:
                raise Exception("Не вдалося розгорнути інфраструктуру")

            target_public_ip = outputs['target_server_public_ip']['value']
            target_private_ip = outputs['target_server_private_ip']['value']
            client_ip = outputs['client_servers_public_ips']['value'][0]

            self.log(f"Target Public IP: {target_public_ip}", "INFO")
            self.log(f"Target Private IP: {target_private_ip}", "INFO")
            self.log(f"Client IP: {client_ip}", "INFO")

            # Очікування серверів
            if not self.wait_for_server_ready(target_public_ip):
                raise Exception("Target сервер не готовий")
            if not self.wait_for_server_ready(client_ip):
                raise Exception("Client сервер не готовий")

            # Запуск тесту
            result = self.run_test(target_public_ip, client_ip, target_private_ip)

            if result:
                test_file, metrics_file = result
                self.show_results(test_file, metrics_file)

            # Знищення
            self.destroy_infrastructure()

            elapsed = time.time() - start_time
            self.log("=" * 70)
            self.log(f"ШВИДКИЙ ТЕСТ ЗАВЕРШЕНО ЗА {elapsed/60:.1f} ХВИЛИН", "SUCCESS")
            self.log("=" * 70)

        except KeyboardInterrupt:
            self.log("\nПерервано користувачем", "WARN")
            self.destroy_infrastructure()
        except Exception as e:
            self.log(f"Критична помилка: {e}", "ERROR")
            self.destroy_infrastructure()


if __name__ == "__main__":
    test = QuickTest()
    test.run()

#!/usr/bin/env python3
"""
Master Orchestrator
Автоматизація повного циклу тестування AWS інфраструктури
"""

import subprocess
import time
import json
import os
from datetime import datetime
from pathlib import Path
import boto3

class CloudOrchestrator:
    def __init__(self, config_file=None):
        self.terraform_dir = Path("terraform")
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)

        # Завантаження конфігурації з файлу або використання default
        if config_file and Path(config_file).exists():
            self.log(f"Завантаження конфігурації з {config_file}...", "INFO")
            config = self.load_config(config_file)
            self.instance_types = config.get('instances', ['t3.micro', 't3.small', 't3.medium'])
            self.rps_levels = config.get('rps_levels', [500, 2000, 5000])
            self.test_duration = config.get('test_duration', 60)
            self.test_mode = config.get('mode', 'full')
        else:
            # Default конфігурація для магістерської роботи
            self.instance_types = ['t3.micro', 't3.small', 't3.medium']
            self.rps_levels = [500, 2000, 5000]
            self.test_duration = 60
            self.test_mode = 'full'

        self.results = []

        # AWS EC2 клієнт для перевірки статусу інстансів
        try:
            self.ec2_client = boto3.client('ec2', region_name='eu-central-1')
        except Exception as e:
            self.log(f"Не вдалося створити EC2 клієнт: {e}", "WARN")
            self.ec2_client = None
        
    def log(self, message, level="INFO"):
        """Логування з часовими мітками"""
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
            # Замінюємо невалідні символи для Windows консолі
            safe_message = message.encode('ascii', 'replace').decode('ascii')
            print(f"[{timestamp}] {symbols.get(level, '[INFO]')} {safe_message}")

    def load_config(self, config_file):
        """Завантаження конфігурації з JSON файлу"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            self.log(f"Конфігурація завантажена:", "SUCCESS")
            self.log(f"  Instances: {config.get('instances', [])}", "INFO")
            self.log(f"  RPS Levels: {config.get('rps_levels', [])}", "INFO")
            self.log(f"  Duration: {config.get('test_duration', 60)}s", "INFO")
            self.log(f"  Mode: {config.get('mode', 'full')}", "INFO")

            return config
        except Exception as e:
            self.log(f"Помилка завантаження конфігурації: {e}", "ERROR")
            return {}
    
    def run_command(self, command, cwd=None):
        """Виконання shell команди"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',  # Замінює невалідні UTF-8 символи на '?'
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
        success, stdout, stderr = self.run_command(
            "terraform init",
            cwd=self.terraform_dir
        )
        if success:
            self.log("Terraform ініціалізовано", "SUCCESS")
        else:
            self.log(f"Помилка ініціалізації: {stderr}", "ERROR")
            raise Exception("Terraform init failed")
    
    def deploy_infrastructure(self, instance_type):
        """Розгортання інфраструктури для конкретного типу інстансу"""
        self.log(f"Розгортання інфраструктури для {instance_type}...", "PROGRESS")
        
        # Оновлюємо variables.tf або передаємо через -var
        success, stdout, stderr = self.run_command(
            f'terraform apply -auto-approve -var="target_server_instance_type={instance_type}"',
            cwd=self.terraform_dir
        )
        
        if not success:
            self.log(f"Помилка розгортання: {stderr}", "ERROR")
            return None
        
        # Отримуємо outputs
        success, stdout, stderr = self.run_command(
            "terraform output -json",
            cwd=self.terraform_dir
            
        )
        
        
        if success:
            outputs = json.loads(stdout)
            self.log(f"Інфраструктура {instance_type} розгорнута", "SUCCESS")
            return outputs
        else:
            self.log("Не вдалося отримати outputs", "ERROR")
            return None
    
    def get_instance_id_by_ip(self, ip_address):
        """Знаходить instance ID по публічній IP адресі"""
        if not self.ec2_client:
            return None

        try:
            response = self.ec2_client.describe_instances(
                Filters=[
                    {'Name': 'ip-address', 'Values': [ip_address]},
                    {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )

            if response['Reservations']:
                instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
                return instance_id
        except Exception as e:
            self.log(f"Помилка пошуку інстансу: {e}", "WARN")

        return None

    def wait_for_instance_status_ok(self, instance_id, max_wait=300):
        """Чекає поки EC2 інстанс пройде status checks"""
        if not self.ec2_client or not instance_id:
            return False

        self.log(f"Очікування status checks для {instance_id}...", "PROGRESS")
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = self.ec2_client.describe_instance_status(InstanceIds=[instance_id])

                if response['InstanceStatuses']:
                    status = response['InstanceStatuses'][0]
                    instance_status = status['InstanceStatus']['Status']
                    system_status = status['SystemStatus']['Status']

                    self.log(f"Instance: {instance_status}, System: {system_status}", "PROGRESS")

                    if instance_status == 'ok' and system_status == 'ok':
                        self.log(f"Інстанс {instance_id} готовий!", "SUCCESS")
                        return True

            except Exception as e:
                self.log(f"Помилка перевірки статусу: {e}", "WARN")

            time.sleep(15)

        return False

    def wait_for_server_ready(self, ip_address, max_attempts=40):
        """Чекає поки сервер буде готовий (комбінований підхід)"""
        self.log(f"Очікування готовності сервера {ip_address}...", "PROGRESS")

        # Крок 1: Знайти instance ID
        instance_id = self.get_instance_id_by_ip(ip_address)
        if instance_id:
            self.log(f"Знайдено інстанс: {instance_id}", "INFO")

            # Крок 2: Чекаємо AWS status checks (надійніше)
            if not self.wait_for_instance_status_ok(instance_id, max_wait=300):
                self.log("Status checks не пройшли, але продовжуємо перевірку SSH...", "WARN")
        else:
            self.log("Не вдалося знайти instance ID, використовуємо тільки SSH перевірку", "WARN")

        # Крок 3: Перевірка SSH доступу
        self.log("Перевірка SSH доступу...", "PROGRESS")

        for attempt in range(max_attempts):
            try:
                self.log(f"SSH спроба #{attempt + 1}/{max_attempts}...", "PROGRESS")

                success, stdout, _ = self.run_command(
                    f'ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes ubuntu@{ip_address} "echo ready"'
                )

                if success and "ready" in stdout:
                    self.log(f"SSH до {ip_address} працює!", "SUCCESS")
                    break

            except Exception as e:
                self.log(f"SSH помилка: {e}", "WARN")

            if attempt < max_attempts - 1:
                time.sleep(15)
        else:
            self.log(f"Сервер {ip_address} не відповідає після {max_attempts} спроб", "ERROR")
            return False

        # Крок 4: Очікування завершення user_data (клонування репозиторію)
        # user_data зазвичай займає 30-60 секунд після того як SSH працює
        self.log("Очікування завершення ініціалізації скриптів (60 сек)...", "PROGRESS")
        time.sleep(60)

        self.log(f"Сервер {ip_address} готовий!", "SUCCESS")

        # КРИТИЧНО: Оновлюємо код з GitHub на сервері!
        self.log(f"Оновлення коду з GitHub на {ip_address}...", "INFO")
        update_cmd = (
            f'ssh -o StrictHostKeyChecking=no ubuntu@{ip_address} '
            f'"cd /home/ubuntu/scripts && git pull origin master"'
        )
        success, stdout, stderr = self.run_command(update_cmd)
        if success:
            self.log(f"Код оновлено на {ip_address}", "SUCCESS")
        else:
            self.log(f"Не вдалося оновити код: {stderr}", "WARN")

        return True

    def monitor_test_realtime(self, target_ip, instance_type, rps, duration):
        """Real-Time моніторинг тесту з оновленням dashboard (WOW-ефект!)"""
        # ВИПРАВЛЕНО: правильні шляхи до results/data/
        streaming_file = Path("results/data/current_test.json")
        start_time = time.time()
        end_time = start_time + duration

        self.log(f"📊 Real-Time streaming в {streaming_file}...", "INFO")

        while time.time() < end_time:
            try:
                # Завантажуємо поточні метрики з target сервера
                temp_metrics = Path("results/data/temp_metrics.json")
                success, _, _ = self.run_command(
                    f"scp -o StrictHostKeyChecking=no ubuntu@{target_ip}:/home/ubuntu/scripts/metrics.json {temp_metrics}"
                )

                if success and temp_metrics.exists():
                    with open(temp_metrics) as f:
                        metrics_data = json.load(f)

                    # Отримуємо останні метрики
                    metrics_list = metrics_data.get('metrics', [])
                    if metrics_list:
                        latest = metrics_list[-1]
                        summary = metrics_data.get('summary', {})

                        # Створюємо streaming data для dashboard
                        streaming_data = {
                            'status': 'testing',
                            'timestamp': latest.get('timestamp'),
                            'test_info': {
                                'instance_type': instance_type,
                                'rps': rps,
                                'total_requests': rps * int(time.time() - start_time)
                            },
                            'current': {
                                'cpu': latest['cpu']['percent'],
                                'memory': latest['memory']['percent'],
                                'is_critical': latest['cpu']['percent'] > 90 or latest['memory']['percent'] > 90
                            },
                            'statistics': {
                                'cpu_avg': summary.get('cpu', {}).get('avg', 0),
                                'cpu_peak': summary.get('cpu', {}).get('peak', 0),
                                'memory_avg': summary.get('memory', {}).get('avg', 0),
                                'memory_peak': summary.get('memory', {}).get('peak', 0),
                                'samples_count': len(metrics_list),
                                'critical_moments_count': summary.get('critical_moments_count', 0)
                            },
                            'timeline': metrics_list[-50:] if len(metrics_list) > 50 else metrics_list
                        }

                        # Записуємо в локальний файл для dashboard
                        with open(streaming_file, 'w') as f:
                            json.dump(streaming_data, f, indent=2)

                        elapsed = int(time.time() - start_time)
                        self.log(
                            f"📊 {elapsed}s: CPU={latest['cpu']['percent']:.1f}% | "
                            f"RAM={latest['memory']['percent']:.1f}% | "
                            f"Samples={len(metrics_list)}",
                            "PROGRESS"
                        )

                    # Видаляємо тимчасовий файл
                    temp_metrics.unlink()

            except Exception as e:
                self.log(f"Real-Time моніторинг: {e}", "WARN")

            # Оновлюємо кожні 2 секунди
            time.sleep(2)

        # Після завершення тесту змінюємо статус
        if streaming_file.exists():
            with open(streaming_file) as f:
                final_data = json.load(f)
            final_data['status'] = 'completed'
            with open(streaming_file, 'w') as f:
                json.dump(final_data, f, indent=2)

        self.log("✅ Real-Time моніторинг завершено", "SUCCESS")

    def run_test(self, instance_type, rps, target_ip, client_ip, target_http_ip=None):
        """Запуск одного тесту

        Args:
            target_ip: Public IP для SSH доступу до target
            client_ip: Public IP для SSH доступу до client
            target_http_ip: IP для HTTP запитів (private IP якщо в одній VPC)
        """
        # Якщо не вказано окремий HTTP IP, використовуємо target_ip
        if target_http_ip is None:
            target_http_ip = target_ip

        self.log(f"Тест: {instance_type} @ {rps} RPS", "PROGRESS")

        # 1. Запуск metrics_collector на target сервері (в фоні через bash -c)
        self.log(f"Запуск збору метрик на target сервері ({target_ip})...", "INFO")

        # Використовуємо bash -c з правильним background запуском
        # ОНОВЛЕНО: інтервал 1 секунда для детальних метрик!
        # ВИПРАВЛЕНО: передаємо metrics.json як 3-й аргумент для коректного збереження
        ssh_command = (
            f'ssh -o StrictHostKeyChecking=no -f ubuntu@{target_ip} '
            f'"bash -c \'cd /home/ubuntu/scripts && python3 metrics_collector.py 1 90 metrics.json > metrics.log 2>&1 &\'"'
        )
        success, _, stderr = self.run_command(ssh_command)

        if not success:
            self.log(f"Попередження при запуску metrics_collector: {stderr}", "WARN")
        else:
            self.log("metrics_collector запущено", "SUCCESS")

        # Чекаємо трохи щоб metrics_collector запустився
        self.log("Очікування ініціалізації (5 сек)...", "PROGRESS")
        time.sleep(5)

        # 2. Запуск request_simulator на client сервері в фоні
        self.log(f"Запуск генерації навантаження {rps} RPS на client ({client_ip})...", "INFO")
        self.log(f"Target HTTP URL: http://{target_http_ip}", "INFO")
        self.log(f"Тривалість тесту: {self.test_duration} сек", "INFO")

        # Запускаємо request_simulator в фоновому режимі
        ssh_command = (
            f'ssh -o StrictHostKeyChecking=no -f ubuntu@{client_ip} '
            f'"bash -c \'cd /home/ubuntu/scripts && python3 request_simulator.py http://{target_http_ip} {rps} {self.test_duration} > test.log 2>&1 &\'"'
        )
        success, stdout, stderr = self.run_command(ssh_command)

        if not success:
            self.log(f"Помилка запуску тестування: {stderr}", "ERROR")
            return None

        self.log("Генерація навантаження запущена", "SUCCESS")

        # Real-Time моніторинг під час виконання тесту (WOW-ефект!)
        self.log("🔥 Real-Time моніторинг активовано!", "INFO")
        self.monitor_test_realtime(target_ip, instance_type, rps, self.test_duration)

        self.log("Генерація навантаження завершена", "SUCCESS")
        
        # Чекаємо завершення metrics_collector
        self.log("Очікування завершення збору метрик (10 сек)...", "PROGRESS")
        time.sleep(10)

        # 3. Завантаження результатів
        self.log("Завантаження результатів з серверів...", "PROGRESS")

        # ВИПРАВЛЕНО: зберігаємо в results/data/ для чіткої структури
        data_dir = self.results_dir / "data"
        data_dir.mkdir(exist_ok=True)
        test_results_file = data_dir / f"test_{instance_type}_{rps}rps.json"
        metrics_file = data_dir / f"metrics_{instance_type}_{rps}rps.json"

        # Завантажуємо test_results.json з client
        self.log(f"Завантаження test_results.json з client ({client_ip})...", "INFO")
        success, _, stderr = self.run_command(
            f"scp -o StrictHostKeyChecking=no ubuntu@{client_ip}:/home/ubuntu/scripts/test_results.json {test_results_file}"
        )

        if not success:
            self.log(f"Помилка завантаження test_results.json: {stderr}", "WARN")

        # Завантажуємо metrics.json з target
        self.log(f"Завантаження metrics.json з target ({target_ip})...", "INFO")
        success, _, stderr = self.run_command(
            f"scp -o StrictHostKeyChecking=no ubuntu@{target_ip}:/home/ubuntu/scripts/metrics.json {metrics_file}"
        )

        if not success:
            self.log(f"Помилка завантаження metrics.json: {stderr}", "WARN")
        
        # 4. Парсинг результатів
        if test_results_file.exists() and metrics_file.exists():
            with open(test_results_file) as f:
                test_data = json.load(f)
            with open(metrics_file) as f:
                metrics_data = json.load(f)
            
            result = {
                'instance_type': instance_type,
                'rps': rps,
                'timestamp': datetime.now().isoformat(),
                'test_results': test_data,
                'metrics': metrics_data
            }
            
            self.log(f"Тест завершено: {instance_type} @ {rps} RPS", "SUCCESS")
            return result
        else:
            self.log("Не вдалося завантажити результати", "ERROR")
            return None
    
    def destroy_infrastructure(self):
        """Знищення інфраструктури"""
        self.log("Знищення інфраструктури...", "PROGRESS")
        success, stdout, stderr = self.run_command(
            "terraform destroy -auto-approve",
            cwd=self.terraform_dir
        )
        
        if success:
            self.log("Інфраструктура знищена", "SUCCESS")
        else:
            self.log(f"Помилка знищення: {stderr}", "WARN")
    
    def run_full_test_suite(self):
        """Запуск повного набору тестів"""
        self.log("=" * 60)
        self.log("ПОЧАТОК ПОВНОГО ЦИКЛУ ТЕСТУВАННЯ")
        self.log("=" * 60)
        
        start_time = time.time()
        
        # Ініціалізація Terraform
        self.terraform_init()
        
        # Цикл по всіх інстансах
        for instance_type in self.instance_types:
            self.log("=" * 60)
            self.log(f"ТЕСТУВАННЯ {instance_type.upper()}")
            self.log("=" * 60)
            
            # Розгортання інфраструктури
            outputs = self.deploy_infrastructure(instance_type)
            
            if not outputs:
                self.log(f"Пропуск {instance_type} через помилку розгортання", "WARN")
                continue
            
            # Отримання IP адрес
            target_public_ip = outputs['target_server_public_ip']['value']
            target_private_ip = outputs['target_server_private_ip']['value']
            client_ip = outputs['client_servers_public_ips']['value'][0]

            self.log(f"Target Public IP: {target_public_ip}", "INFO")
            self.log(f"Target Private IP: {target_private_ip}", "INFO")
            self.log(f"Client IP: {client_ip}", "INFO")

            # Очікування готовності серверів
            if not self.wait_for_server_ready(target_public_ip):
                self.log(f"Target сервер не готовий, пропуск {instance_type}", "WARN")
                self.destroy_infrastructure()
                continue

            if not self.wait_for_server_ready(client_ip):
                self.log(f"Client сервер не готовий, пропуск {instance_type}", "WARN")
                self.destroy_infrastructure()
                continue

            # Цикл по всіх RPS
            for rps in self.rps_levels:
                # Використовуємо публічний IP для SSH, приватний для HTTP
                result = self.run_test(instance_type, rps, target_public_ip, client_ip, target_private_ip)
                
                if result:
                    self.results.append(result)
                
                # Пауза між тестами
                if rps != self.rps_levels[-1]:
                    self.log("Пауза 30 секунд між тестами...")
                    time.sleep(30)
            
            # Знищення інфраструктури після тестів інстансу
            self.destroy_infrastructure()
            
            # Пауза між інстансами
            if instance_type != self.instance_types[-1]:
                self.log("Пауза 60 секунд перед наступним інстансом...")
                time.sleep(60)
        
        # Збереження всіх результатів
        self.save_results()

        elapsed = time.time() - start_time
        self.log("=" * 60)
        self.log(f"ТЕСТУВАННЯ ЗАВЕРШЕНО ЗА {elapsed/60:.1f} ХВИЛИН", "SUCCESS")
        self.log(f"Всього тестів: {len(self.results)}/9")
        self.log("=" * 60)

        # Автоматичний запуск TOPSIS оптимізації
        self.log("=" * 60)
        self.log("ЗАПУСК TOPSIS ОПТИМІЗАЦІЇ")
        self.log("=" * 60)
        self.run_optimization()

    def run_optimization(self):
        """Запуск TOPSIS оптимізації"""
        try:
            self.log("Виконання TOPSIS аналізу...", "PROGRESS")
            success, stdout, stderr = self.run_command("python scripts/optimizer.py")

            if success:
                self.log("TOPSIS оптимізація завершена!", "SUCCESS")
                self.log(f"Результати збережено: optimization_results.json", "SUCCESS")

                # Копіюємо результати для веб-сервера
                self.prepare_web_data()
            else:
                self.log(f"Помилка при оптимізації: {stderr}", "ERROR")
        except Exception as e:
            self.log(f"Помилка при запуску оптимізації: {e}", "ERROR")

    def prepare_web_data(self):
        """Підготовка даних для веб-сервера"""
        try:
            self.log("Підготовка даних для веб-дашборду...", "PROGRESS")

            # Копіюємо найкращі результати для відображення
            import shutil

            # Вибираємо один репрезентативний тест для кожного інстансу
            # ОНОВЛЕНО: використовуємо 500 RPS як базовий рівень
            test_files = [
                ("results/test_t3.micro_500rps.json", "test_t3_micro.json"),
                ("results/test_t3.small_500rps.json", "test_t3_small.json"),
                ("results/test_t3.medium_500rps.json", "test_t3_medium.json"),
            ]

            metrics_files = [
                ("results/metrics_t3.micro_500rps.json", "metrics_t3_micro.json"),
                ("results/metrics_t3.small_500rps.json", "metrics_t3_small.json"),
                ("results/metrics_t3.medium_500rps.json", "metrics_t3_medium.json"),
            ]

            for src, dst in test_files:
                src_path = Path(src)
                if src_path.exists():
                    shutil.copy(src_path, dst)
                    self.log(f"Скопійовано: {dst}", "SUCCESS")

            for src, dst in metrics_files:
                src_path = Path(src)
                if src_path.exists():
                    shutil.copy(src_path, dst)
                    self.log(f"Скопійовано: {dst}", "SUCCESS")

            self.log("Дані для веб-дашборду готові!", "SUCCESS")

        except Exception as e:
            self.log(f"Помилка при підготовці даних: {e}", "WARN")

    def save_results(self):
        """Збереження агрегованих результатів"""
        summary_file = self.results_dir / "summary.json"
        
        with open(summary_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_tests': len(self.results),
                'results': self.results
            }, f, indent=2)
        
        self.log(f"Результати збережено: {summary_file}", "SUCCESS")


def main():
    """Головна функція"""
    print("""
    ========================================================
       CLOUD OPTIMIZATION ORCHESTRATOR
       Автоматизоване тестування AWS інфраструктури
    ========================================================
    """)

    # Перевірка чи є конфігураційний файл від Control Panel
    config_file = "test_config.json"
    orchestrator = CloudOrchestrator(config_file if Path(config_file).exists() else None)

    try:
        orchestrator.run_full_test_suite()
    except KeyboardInterrupt:
        print("\n\n[WARN] Перервано користувачем")
        orchestrator.destroy_infrastructure()
    except Exception as e:
        print(f"\n\n[ERROR] Критична помилка: {e}")
        orchestrator.destroy_infrastructure()


if __name__ == "__main__":
    main()
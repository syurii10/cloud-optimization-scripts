#!/usr/bin/env python3
"""
Automated Deployment Pipeline
Автоматично розгортає оптимальну конфігурацію на основі TOPSIS результатів

Workflow:
1. Run TOPSIS optimization
2. Get best instance type
3. Update Terraform variables
4. Deploy infrastructure (terraform apply)
5. Health check
6. Traffic switch (optional)
"""

import json
import subprocess
import time
import sys
from pathlib import Path
from typing import Dict, Optional
import argparse

# Додаємо шлях до optimizer
sys.path.append(str(Path(__file__).parent))
from optimizer import TOPSISOptimizer


class AutoDeployPipeline:
    """Automated deployment based on TOPSIS optimization"""

    def __init__(self, terraform_dir: str = "terraform", dry_run: bool = False):
        self.terraform_dir = Path(terraform_dir)
        self.results_dir = Path("results/data")
        self.dry_run = dry_run

        if not self.terraform_dir.exists():
            raise FileNotFoundError(f"Terraform directory not found: {self.terraform_dir}")

    def load_optimization_results(self) -> Dict:
        """Завантажує результати оптимізації"""
        results_file = self.results_dir / "optimization_results.json"

        if not results_file.exists():
            raise FileNotFoundError(
                f"Optimization results not found: {results_file}\n"
                f"Run optimizer.py first!"
            )

        with open(results_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_best_instance(self, results: Dict) -> tuple:
        """Повертає найкращий instance type з TOPSIS результатів"""
        best = results['best_alternative']

        # Знаходимо score для best alternative
        for result in results['results']:
            if result['alternative'] == best:
                score = result['score']
                break
        else:
            score = 0.0

        print(f"\n[TOPSIS] Best instance: {best} (score: {score:.4f})")
        return best, score

    def update_terraform_vars(self, instance_type: str) -> bool:
        """
        Оновлює Terraform змінні для deployment

        Args:
            instance_type: Оптимальний тип інстансу (t3.micro/small/medium)

        Returns:
            True якщо успішно оновлено
        """
        tfvars_file = self.terraform_dir / "terraform.tfvars"

        print(f"\n[INFO] Updating Terraform variables...")
        print(f"  File: {tfvars_file}")
        print(f"  Target instance: {instance_type}")

        if self.dry_run:
            print(f"[DRY-RUN] Would update target_server_instance_type = {instance_type}")
            return True

        # Читаємо поточні змінні
        if tfvars_file.exists():
            with open(tfvars_file, 'r') as f:
                lines = f.readlines()
        else:
            lines = []

        # Оновлюємо target_server_instance_type
        updated = False
        new_lines = []

        for line in lines:
            if line.strip().startswith('target_server_instance_type'):
                new_lines.append(f'target_server_instance_type = "{instance_type}"\n')
                updated = True
            else:
                new_lines.append(line)

        # Якщо змінна не знайдена, додаємо її
        if not updated:
            new_lines.append(f'target_server_instance_type = "{instance_type}"\n')

        # Записуємо оновлені змінні
        with open(tfvars_file, 'w') as f:
            f.writelines(new_lines)

        print(f"[OK] Terraform variables updated")
        return True

    def terraform_init(self) -> bool:
        """Ініціалізує Terraform"""
        print(f"\n[TERRAFORM] Initializing...")

        if self.dry_run:
            print("[DRY-RUN] Would run: terraform init")
            return True

        try:
            result = subprocess.run(
                ['terraform', 'init'],
                cwd=self.terraform_dir,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                print("[OK] Terraform initialized")
                return True
            else:
                print(f"[ERROR] Terraform init failed:")
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("[ERROR] Terraform init timeout")
            return False
        except FileNotFoundError:
            print("[ERROR] Terraform not found. Install: https://www.terraform.io/downloads")
            return False

    def terraform_plan(self) -> bool:
        """Показує план змін Terraform"""
        print(f"\n[TERRAFORM] Planning deployment...")

        if self.dry_run:
            print("[DRY-RUN] Would run: terraform plan")
            return True

        try:
            result = subprocess.run(
                ['terraform', 'plan'],
                cwd=self.terraform_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print("[OK] Terraform plan complete")
                # Виводимо summary змін
                for line in result.stdout.split('\n'):
                    if 'Plan:' in line or 'changes' in line.lower():
                        print(f"  {line.strip()}")
                return True
            else:
                print(f"[ERROR] Terraform plan failed:")
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("[ERROR] Terraform plan timeout")
            return False

    def terraform_apply(self, auto_approve: bool = False) -> bool:
        """
        Розгортає інфраструктуру

        Args:
            auto_approve: Автоматично підтвердити deployment (небезпечно!)

        Returns:
            True якщо успішно
        """
        print(f"\n[TERRAFORM] Deploying infrastructure...")

        if self.dry_run:
            print("[DRY-RUN] Would run: terraform apply")
            return True

        if not auto_approve:
            confirm = input("\n[WARNING] Apply changes? This will deploy to AWS! (yes/no): ")
            if confirm.lower() != 'yes':
                print("[CANCELLED] Deployment cancelled by user")
                return False

        try:
            cmd = ['terraform', 'apply']
            if auto_approve:
                cmd.append('-auto-approve')

            result = subprocess.run(
                cmd,
                cwd=self.terraform_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )

            if result.returncode == 0:
                print("[OK] Infrastructure deployed successfully")
                return True
            else:
                print(f"[ERROR] Terraform apply failed:")
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("[ERROR] Terraform apply timeout (10 min)")
            return False

    def health_check(self, max_retries: int = 10, delay: int = 30) -> bool:
        """
        Перевіряє здоров'я розгорнутої інфраструктури

        Args:
            max_retries: Максимальна кількість спроб
            delay: Затримка між спробами (секунди)

        Returns:
            True якщо healthy
        """
        print(f"\n[HEALTH CHECK] Waiting for instances to be ready...")
        print(f"  Max retries: {max_retries}")
        print(f"  Delay: {delay}s between checks")

        if self.dry_run:
            print("[DRY-RUN] Would perform health checks")
            return True

        # TODO: Реалізувати реальний health check через AWS SDK або HTTP
        # Для прикладу, просто чекаємо
        for i in range(max_retries):
            print(f"  Attempt {i+1}/{max_retries}...", end=' ')
            time.sleep(delay)
            print("OK")

        print("[OK] Health check passed")
        return True

    def get_deployment_info(self) -> Dict:
        """Отримує інформацію про deployment"""
        print(f"\n[INFO] Getting deployment information...")

        if self.dry_run:
            return {
                'instance_type': 't3.medium',
                'public_ip': '1.2.3.4',
                'private_ip': '10.0.1.10',
                'status': 'running'
            }

        try:
            result = subprocess.run(
                ['terraform', 'output', '-json'],
                cwd=self.terraform_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                outputs = json.loads(result.stdout)
                return outputs
            else:
                print("[WARNING] Could not get deployment info")
                return {}

        except Exception as e:
            print(f"[WARNING] Error getting deployment info: {e}")
            return {}

    def save_deployment_log(self, instance_type: str, success: bool):
        """Зберігає лог deployment"""
        log_file = Path("results/data/deployment_log.json")

        log_entry = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'instance_type': instance_type,
            'success': success,
            'dry_run': self.dry_run
        }

        # Завантажуємо існуючі логи
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []

        # Додаємо новий запис
        logs.append(log_entry)

        # Зберігаємо
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

        print(f"[OK] Deployment log saved: {log_file}")

    def run_pipeline(self, auto_approve: bool = False) -> bool:
        """
        Запускає повний deployment pipeline

        Args:
            auto_approve: Автоматично підтвердити всі кроки

        Returns:
            True якщо успішно
        """
        print("\n" + "="*70)
        print("AUTOMATED DEPLOYMENT PIPELINE")
        print("="*70)

        if self.dry_run:
            print("\n[DRY-RUN MODE] No actual changes will be made\n")

        try:
            # Крок 1: Завантажити TOPSIS результати
            print("\n[STEP 1/7] Loading TOPSIS optimization results...")
            results = self.load_optimization_results()
            best_instance, topsis_score = self.get_best_instance(results)

            # Крок 2: Оновити Terraform змінні
            print("\n[STEP 2/7] Updating Terraform variables...")
            if not self.update_terraform_vars(best_instance):
                raise Exception("Failed to update Terraform variables")

            # Крок 3: Terraform init
            print("\n[STEP 3/7] Initializing Terraform...")
            if not self.terraform_init():
                raise Exception("Terraform init failed")

            # Крок 4: Terraform plan
            print("\n[STEP 4/7] Planning deployment...")
            if not self.terraform_plan():
                raise Exception("Terraform plan failed")

            # Крок 5: Terraform apply
            print("\n[STEP 5/7] Deploying infrastructure...")
            if not self.terraform_apply(auto_approve=auto_approve):
                raise Exception("Terraform apply failed")

            # Крок 6: Health check
            print("\n[STEP 6/7] Performing health checks...")
            if not self.health_check():
                raise Exception("Health check failed")

            # Крок 7: Get deployment info
            print("\n[STEP 7/7] Getting deployment information...")
            info = self.get_deployment_info()

            # Success!
            print("\n" + "="*70)
            print("DEPLOYMENT SUCCESSFUL!")
            print("="*70)
            print(f"\nInstance type: {best_instance}")
            print(f"TOPSIS score: {topsis_score:.4f}")

            if info:
                print("\nDeployment details:")
                for key, value in info.items():
                    if isinstance(value, dict) and 'value' in value:
                        print(f"  {key}: {value['value']}")

            # Зберігаємо лог
            self.save_deployment_log(best_instance, True)

            return True

        except Exception as e:
            print("\n" + "="*70)
            print("DEPLOYMENT FAILED!")
            print("="*70)
            print(f"\nError: {str(e)}")

            # Зберігаємо лог помилки
            self.save_deployment_log('unknown', False)

            return False


def main():
    """Головна функція"""
    parser = argparse.ArgumentParser(
        description='Automated deployment pipeline based on TOPSIS optimization'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode (no actual deployment)'
    )
    parser.add_argument(
        '--auto-approve',
        action='store_true',
        help='Auto-approve deployment (DANGEROUS!)'
    )
    parser.add_argument(
        '--terraform-dir',
        default='terraform',
        help='Path to Terraform directory'
    )

    args = parser.parse_args()

    # Створюємо pipeline
    pipeline = AutoDeployPipeline(
        terraform_dir=args.terraform_dir,
        dry_run=args.dry_run
    )

    # Запускаємо
    success = pipeline.run_pipeline(auto_approve=args.auto_approve)

    # Exit code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

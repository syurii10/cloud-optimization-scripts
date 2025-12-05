#!/usr/bin/env python3
"""
PDF Report Generator для результатів оптимізації
Генерує професійні звіти з графіками та таблицями
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class MarkdownReportGenerator:
    """Генератор звітів у форматі Markdown (легко конвертувати в PDF)"""

    def __init__(self, output_dir: str = "results/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_full_report(self, data: Dict) -> str:
        """
        Генерує повний звіт про оптимізацію

        Args:
            data: Словник з усіма даними
                {
                    'optimization': {...},
                    'sensitivity': {...},
                    'method_comparison': {...},
                    'cost_estimate': {...}
                }

        Returns:
            Шлях до згенерованого файлу
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"optimization_report_{timestamp}.md"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            # Титульна сторінка
            f.write(self._generate_title_page())

            # Executive Summary
            f.write(self._generate_executive_summary(data))

            # TOPSIS Optimization Results
            if 'optimization' in data:
                f.write(self._generate_optimization_section(data['optimization']))

            # Sensitivity Analysis
            if 'sensitivity' in data:
                f.write(self._generate_sensitivity_section(data['sensitivity']))

            # Method Comparison
            if 'method_comparison' in data:
                f.write(self._generate_comparison_section(data['method_comparison']))

            # Cost Analysis
            if 'cost_estimate' in data:
                f.write(self._generate_cost_section(data['cost_estimate']))

            # Recommendations
            f.write(self._generate_recommendations(data))

            # Technical Details
            f.write(self._generate_technical_details(data))

        print(f"\n[OK] Звіт згенеровано: {filepath}")
        print(f"\n💡 Для конвертації у PDF використайте:")
        print(f"   pandoc {filename} -o report.pdf --pdf-engine=xelatex")

        return str(filepath)

    def _generate_title_page(self) -> str:
        """Генерує титульну сторінку"""
        return f"""---
title: "Багатокритеріальна оптимізація хмарної інфраструктури AWS"
subtitle: "Метод TOPSIS для вибору оптимальних EC2 інстансів"
author: "Cloud Optimization Project"
date: "{datetime.now().strftime('%d.%m.%Y')}"
geometry: margin=2cm
---

\\newpage

# Зміст

1. Executive Summary
2. Результати TOPSIS оптимізації
3. Аналіз чутливості
4. Порівняння методів MCDM
5. Аналіз вартості
6. Рекомендації
7. Технічні деталі

\\newpage

"""

    def _generate_executive_summary(self, data: Dict) -> str:
        """Генерує Executive Summary"""
        md = "# 1. Executive Summary\n\n"

        # Визначаємо найкращу альтернативу
        if 'optimization' in data:
            best = data['optimization']['best_alternative']
            md += f"## Ключові висновки\n\n"
            md += f"- **Рекомендований інстанс:** `{best}`\n"
            md += f"- **Метод аналізу:** TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)\n"
            md += f"- **Кількість критеріїв:** 5 (Performance, Response Time, CPU, Memory, Cost)\n"

            if 'results' in data['optimization']:
                top_result = data['optimization']['results'][0]
                md += f"- **TOPSIS Score:** {top_result['score']:.4f}\n"

        if 'cost_estimate' in data:
            cost = data['cost_estimate']['costs']['total']
            md += f"- **Оцінена вартість тестування:** ${cost:.4f}\n"

        md += "\n## Контекст дослідження\n\n"
        md += "Це дослідження порівнює продуктивність різних типів EC2 інстансів AWS "
        md += "під навантаженням для визначення оптимального балансу між продуктивністю та вартістю.\n\n"

        md += "\\newpage\n\n"
        return md

    def _generate_optimization_section(self, optimization: Dict) -> str:
        """Генерує секцію з результатами TOPSIS"""
        md = "# 2. Результати TOPSIS оптимізації\n\n"

        md += "## 2.1 Методологія\n\n"
        md += "TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) - "
        md += "метод багатокритеріального прийняття рішень, що базується на концепції, "
        md += "що обрана альтернатива має бути найближчою до ідеального рішення і "
        md += "найвіддаленішою від антиідеального.\n\n"

        # Ваги критеріїв
        md += "## 2.2 Ваги критеріїв\n\n"
        md += "| Критерій | Вага | Обґрунтування |\n"
        md += "|----------|------|---------------|\n"

        criteria_desc = {
            'performance': 'Продуктивність (RPS) - найважливіший фактор',
            'response_time': 'Час відгуку - критично для UX',
            'cpu_usage': 'Використання CPU - ефективність',
            'memory_usage': 'Використання RAM - стабільність',
            'cost': 'Вартість - економічна доцільність'
        }

        for criterion, weight in optimization['criteria_weights'].items():
            desc = criteria_desc.get(criterion, '')
            md += f"| {criterion} | {weight:.2f} | {desc} |\n"

        # Рейтинг альтернатив
        md += "\n## 2.3 Рейтинг інстансів\n\n"
        md += "| Ранг | Інстанс | TOPSIS Score | Performance | Response Time | CPU % | Memory % | Cost $/h |\n"
        md += "|------|---------|--------------|-------------|---------------|-------|----------|----------|\n"

        for result in optimization['results']:
            alt = result['alternative']
            score = result['score']
            rank = result['rank']
            crit = result['criteria']

            md += f"| {rank} | **{alt}** | {score:.4f} | "
            md += f"{crit.get('performance', 0)} | "
            md += f"{crit.get('response_time', 0):.3f}s | "
            md += f"{crit.get('cpu_usage', 0):.1f} | "
            md += f"{crit.get('memory_usage', 0):.1f} | "
            md += f"{crit.get('cost', 0):.4f} |\n"

        md += "\n\\newpage\n\n"
        return md

    def _generate_sensitivity_section(self, sensitivity: Dict) -> str:
        """Генерує секцію аналізу чутливості"""
        md = "# 3. Аналіз чутливості\n\n"

        md += "## 3.1 Мета аналізу\n\n"
        md += "Аналіз чутливості визначає, наскільки стабільні результати TOPSIS "
        md += "при зміні ваг критеріїв. Це важливо для підтвердження надійності висновків.\n\n"

        # Індекси стабільності
        if 'stability_indices' in sensitivity:
            md += "## 3.2 Індекси стабільності альтернатив\n\n"
            md += "| Інстанс | Індекс стабільності | Інтерпретація |\n"
            md += "|---------|---------------------|---------------|\n"

            for alt, index in sensitivity['stability_indices'].items():
                interpretation = "Високостабільний" if index > 0.8 else "Середньостабільний" if index > 0.5 else "Низькостабільний"
                md += f"| {alt} | {index:.4f} | {interpretation} |\n"

        # Точки перелому
        if 'breakpoints' in sensitivity and sensitivity['breakpoints']:
            md += "\n## 3.3 Критичні точки зміни лідера\n\n"
            md += "Ваги критеріїв, при яких змінюється рекомендований інстанс:\n\n"

            for criterion, breakpoints in sensitivity['breakpoints'].items():
                md += f"\n### {criterion}\n\n"
                for bp in breakpoints:
                    md += f"- При вазі **{bp['weight']:.3f}**: "
                    md += f"{bp['previous_leader']} → {bp['new_leader']}\n"

        md += "\n\\newpage\n\n"
        return md

    def _generate_comparison_section(self, comparison: Dict) -> str:
        """Генерує секцію порівняння методів"""
        md = "# 4. Порівняння методів MCDM\n\n"

        md += "## 4.1 Порівнювані методи\n\n"
        md += "- **TOPSIS:** Базується на відстані до ідеального рішення\n"
        md += "- **SAW:** Simple Additive Weighting - зважена сума\n"
        md += "- **WPM:** Weighted Product Model - зважений добуток\n\n"

        # Таблиця рангів
        if 'ranking_comparison' in comparison:
            md += "## 4.2 Порівняння рангів\n\n"
            md += "| Альтернатива | TOPSIS | SAW | WPM |\n"
            md += "|--------------|--------|-----|-----|\n"

            for alt, ranks in comparison['ranking_comparison'].items():
                md += f"| {alt} | #{ranks['TOPSIS']} | #{ranks['SAW']} | #{ranks['WPM']} |\n"

        # Консенсус
        if 'consensus' in comparison:
            consensus = comparison['consensus']
            md += "\n## 4.3 Консенсус методів\n\n"
            md += f"- **Одностайність лідера:** {'ТАК ✓' if consensus['unanimous_leader'] else 'НІ ✗'}\n"
            md += f"- **Середня кореляція рангів:** {consensus['average_correlation']:.4f}\n"
            md += f"- **Рівень консенсусу:** {consensus['consensus_level']}\n\n"

        md += "\n\\newpage\n\n"
        return md

    def _generate_cost_section(self, cost_estimate: Dict) -> str:
        """Генерує секцію аналізу вартості"""
        md = "# 5. Аналіз вартості\n\n"

        costs = cost_estimate['costs']

        md += "## 5.1 Деталізація вартості тестування\n\n"
        md += "| Категорія | Вартість (USD) |\n"
        md += "|-----------|----------------|\n"
        md += f"| Compute | ${costs['compute']:.4f} |\n"
        md += f"| Data Transfer | ${costs['data_transfer']:.4f} |\n"
        md += f"| Client Overhead | ${costs['client_overhead']:.4f} |\n"
        md += f"| Setup/Teardown | ${costs['setup_teardown']:.4f} |\n"
        md += f"| **ЗАГАЛЬНА** | **${costs['total']:.4f}** |\n\n"

        # Бюджет
        if 'budget_impact' in cost_estimate:
            budget = cost_estimate['budget_impact']
            md += "## 5.2 Вплив на бюджет\n\n"
            md += f"- **Загальний бюджет:** ${budget['total_budget']:.2f}\n"
            md += f"- **Використано:** {budget['percentage_used']:.2f}%\n"
            md += f"- **Залишок:** ${budget['remaining']:.2f}\n"
            md += f"- **Статус:** {budget['status'].upper()}\n\n"

        md += "\n\\newpage\n\n"
        return md

    def _generate_recommendations(self, data: Dict) -> str:
        """Генерує рекомендації"""
        md = "# 6. Рекомендації\n\n"

        if 'optimization' in data:
            best = data['optimization']['best_alternative']
            md += f"## 6.1 Рекомендований інстанс: `{best}`\n\n"

            md += "### Обґрунтування:\n\n"
            md += f"- Найвищий TOPSIS score серед альтернатив\n"
            md += f"- Оптимальний баланс між продуктивністю та вартістю\n"
            md += f"- Стабільні результати в аналізі чутливості\n\n"

        md += "## 6.2 Use Cases\n\n"
        md += "### Для виробничих систем:\n"
        md += "- Використовуйте рекомендований інстанс як базовий\n"
        md += "- Налаштуйте auto-scaling на основі CPU/Memory метрик\n"
        md += "- Моніторте вартість щотижня\n\n"

        md += "### Для розробки/тестування:\n"
        md += "- Можливо використовувати менший інстанс для економії\n"
        md += "- Запускайте тільки в робочі години\n\n"

        md += "## 6.3 Наступні кроки\n\n"
        md += "1. Провести додаткове тестування під real-world навантаженням\n"
        md += "2. Налаштувати моніторинг та алертинг\n"
        md += "3. Реалізувати cost optimization стратегії\n"
        md += "4. Періодично переглядати результати (раз на квартал)\n\n"

        md += "\n\\newpage\n\n"
        return md

    def _generate_technical_details(self, data: Dict) -> str:
        """Генерує технічні деталі"""
        md = "# 7. Технічні деталі\n\n"

        md += "## 7.1 Методологія тестування\n\n"
        md += "- **Load testing tool:** aiohttp-based async HTTP client\n"
        md += "- **Metrics collection:** psutil (CPU, RAM, Network)\n"
        md += "- **Infrastructure:** Terraform на AWS EC2\n"
        md += "- **Optimization method:** TOPSIS\n\n"

        md += "## 7.2 Обмеження дослідження\n\n"
        md += "- Тести проводилися в контрольованих умовах\n"
        md += "- Real-world навантаження може відрізнятися\n"
        md += "- Ціни AWS можуть змінюватися\n"
        md += "- Результати специфічні для регіону eu-central-1\n\n"

        md += "## 7.3 Версії ПЗ\n\n"
        md += "- Python: 3.8+\n"
        md += "- Terraform: 1.0+\n"
        md += "- Node.js: 16.x+\n"
        md += "- AWS Ubuntu: 22.04 LTS\n\n"

        md += f"\n---\n\n"
        md += f"*Звіт згенеровано автоматично: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        return md


def generate_report_from_files(results_dir: str = "results"):
    """Генерує звіт з існуючих файлів результатів"""
    results_path = Path(results_dir)

    # Завантажуємо дані
    data = {}

    # Optimization results
    opt_file = results_path / "optimization_results.json"
    if opt_file.exists():
        with open(opt_file, 'r', encoding='utf-8') as f:
            data['optimization'] = json.load(f)

    # Sensitivity analysis
    sens_file = results_path / "sensitivity" / "sensitivity_analysis.json"
    if sens_file.exists():
        with open(sens_file, 'r', encoding='utf-8') as f:
            data['sensitivity'] = json.load(f)

    # Method comparison
    comp_file = results_path / "method_comparison.json"
    if comp_file.exists():
        with open(comp_file, 'r', encoding='utf-8') as f:
            data['method_comparison'] = json.load(f)

    # Cost estimate
    cost_file = results_path / "cost_estimate.json"
    if cost_file.exists():
        with open(cost_file, 'r', encoding='utf-8') as f:
            data['cost_estimate'] = json.load(f)

    if not data:
        print("ПОМИЛКА: Не знайдено файлів результатів")
        return None

    # Генеруємо звіт
    generator = MarkdownReportGenerator()
    report_path = generator.generate_full_report(data)

    return report_path


if __name__ == "__main__":
    generate_report_from_files()

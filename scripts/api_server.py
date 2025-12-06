#!/usr/bin/env python3
"""
REST API для TOPSIS Cloud Optimization System
Надає HTTP endpoints для інтеграції з іншими системами
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import sys
from pathlib import Path
from typing import Dict, List
import logging

# Додаємо шлях до optimizer
sys.path.append(str(Path(__file__).parent))
from optimizer import TOPSISOptimizer
# Note: Other imports not needed for API, data loaded from JSON files

# Налаштування
app = Flask(__name__)
CORS(app)  # Enable CORS для frontend

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
RESULTS_DIR = Path("results")
DATA_DIR = RESULTS_DIR / "data"
CHARTS_DIR = RESULTS_DIR / "charts"


# ==================== UTILITY FUNCTIONS ====================

def load_optimization_results() -> Dict:
    """Завантажує останні результати оптимізації"""
    results_file = DATA_DIR / "optimization_results.json"
    if not results_file.exists():
        return None

    with open(results_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_optimization_results(results: Dict):
    """Зберігає результати оптимізації"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    results_file = DATA_DIR / "optimization_results.json"

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


# ==================== API ENDPOINTS ====================

@app.route('/')
def index():
    """API Documentation"""
    return jsonify({
        "name": "TOPSIS Cloud Optimization API",
        "version": "1.0.0",
        "description": "REST API for multi-criteria cloud instance optimization using TOPSIS method",
        "endpoints": {
            "GET /": "This documentation",
            "GET /api/health": "Health check",
            "GET /api/results": "Get latest optimization results",
            "POST /api/optimize": "Run TOPSIS optimization",
            "POST /api/optimize/custom-weights": "Run optimization with custom criteria weights",
            "GET /api/sensitivity": "Get sensitivity analysis results",
            "GET /api/methods": "Get method comparison results (TOPSIS/SAW/WPM)",
            "GET /api/monte-carlo": "Get Monte Carlo validation results",
            "GET /api/cost": "Get cost prediction results",
            "GET /api/charts/<chart_name>": "Get visualization chart"
        },
        "military_use_cases": [
            "Delta - Artillery Calculation System",
            "Aeneas - Intelligence Image Processing",
            "Cyber Defense - DDoS Resilience",
            "Logistix - Supply Chain Management"
        ],
        "repository": "https://github.com/syurii10/cloud-optimization-project"
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "TOPSIS Optimization API",
        "version": "1.0.0"
    }), 200


@app.route('/api/results', methods=['GET'])
def get_results():
    """
    Повертає останні результати оптимізації

    Returns:
        JSON з TOPSIS scores та rankings
    """
    logger.info("GET /api/results")

    results = load_optimization_results()

    if not results:
        return jsonify({
            "error": "No optimization results found",
            "message": "Run optimization first using POST /api/optimize"
        }), 404

    return jsonify(results), 200


@app.route('/api/optimize', methods=['POST'])
def run_optimization():
    """
    Запускає TOPSIS оптимізацію з даними альтернатив

    Request Body:
    {
        "alternatives": {
            "t3.micro": {
                "performance": 100,
                "response_time": 0.05,
                "cpu_usage": 40,
                "memory_usage": 30,
                "cost": 0.0104
            },
            ...
        }
    }

    Returns:
        JSON з результатами оптимізації
    """
    logger.info("POST /api/optimize")

    try:
        data = request.get_json()

        if not data or 'alternatives' not in data:
            return jsonify({
                "error": "Missing 'alternatives' in request body"
            }), 400

        alternatives = data['alternatives']

        if len(alternatives) < 2:
            return jsonify({
                "error": "At least 2 alternatives required"
            }), 400

        # Валідація структури даних
        required_criteria = ['performance', 'response_time', 'cpu_usage', 'memory_usage', 'cost']
        for alt_name, criteria in alternatives.items():
            for criterion in required_criteria:
                if criterion not in criteria:
                    return jsonify({
                        "error": f"Missing criterion '{criterion}' for alternative '{alt_name}'"
                    }), 400

        # Запускаємо TOPSIS
        optimizer = TOPSISOptimizer()
        results = optimizer.optimize(alternatives)

        # Зберігаємо результати
        save_optimization_results(results)

        logger.info(f"Optimization complete. Winner: {results['recommendation']['best_alternative']}")

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Optimization error: {str(e)}")
        return jsonify({
            "error": "Optimization failed",
            "message": str(e)
        }), 500


@app.route('/api/optimize/custom-weights', methods=['POST'])
def run_optimization_custom_weights():
    """
    Запускає TOPSIS з кастомними вагами критеріїв

    Request Body:
    {
        "alternatives": { ... },
        "weights": {
            "performance": 0.40,
            "response_time": 0.30,
            "cpu_usage": 0.10,
            "memory_usage": 0.10,
            "cost": 0.10
        }
    }

    Returns:
        JSON з результатами
    """
    logger.info("POST /api/optimize/custom-weights")

    try:
        data = request.get_json()

        if not data or 'alternatives' not in data or 'weights' not in data:
            return jsonify({
                "error": "Missing 'alternatives' or 'weights' in request body"
            }), 400

        alternatives = data['alternatives']
        weights = data['weights']

        # Валідація ваг
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            return jsonify({
                "error": f"Weights must sum to 1.0, got {total_weight}"
            }), 400

        # Запускаємо TOPSIS з кастомними вагами
        optimizer = TOPSISOptimizer(criteria_weights=weights)
        results = optimizer.optimize(alternatives)

        # Додаємо інформацію про кастомні ваги
        results['custom_weights'] = weights

        # Зберігаємо
        save_optimization_results(results)

        logger.info(f"Custom optimization complete. Winner: {results['recommendation']['best_alternative']}")

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Custom optimization error: {str(e)}")
        return jsonify({
            "error": "Optimization failed",
            "message": str(e)
        }), 500


@app.route('/api/sensitivity', methods=['GET'])
def get_sensitivity():
    """Повертає результати sensitivity analysis"""
    logger.info("GET /api/sensitivity")

    sensitivity_file = DATA_DIR / "sensitivity_analysis.json"

    if not sensitivity_file.exists():
        return jsonify({
            "error": "Sensitivity analysis not found",
            "message": "Run sensitivity_analysis.py first"
        }), 404

    with open(sensitivity_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    return jsonify(results), 200


@app.route('/api/methods', methods=['GET'])
def get_method_comparison():
    """Повертає порівняння TOPSIS vs SAW vs WPM"""
    logger.info("GET /api/methods")

    methods_file = DATA_DIR / "method_comparison.json"

    if not methods_file.exists():
        return jsonify({
            "error": "Method comparison not found",
            "message": "Run method_comparison.py first"
        }), 404

    with open(methods_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    return jsonify(results), 200


@app.route('/api/monte-carlo', methods=['GET'])
def get_monte_carlo():
    """Повертає результати Monte Carlo validation"""
    logger.info("GET /api/monte-carlo")

    mc_file = DATA_DIR / "monte_carlo_results.json"

    if not mc_file.exists():
        return jsonify({
            "error": "Monte Carlo results not found",
            "message": "Run monte_carlo_validation.py first"
        }), 404

    with open(mc_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    return jsonify(results), 200


@app.route('/api/cost', methods=['GET'])
def get_cost_prediction():
    """Повертає прогноз вартості"""
    logger.info("GET /api/cost")

    cost_file = DATA_DIR / "cost_estimate.json"

    if not cost_file.exists():
        return jsonify({
            "error": "Cost prediction not found",
            "message": "Run cost_predictor.py first"
        }), 404

    with open(cost_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    return jsonify(results), 200


@app.route('/api/charts/<chart_name>', methods=['GET'])
def get_chart(chart_name):
    """
    Повертає PNG графік

    Args:
        chart_name: Назва файлу (наприклад, 'topsis_comparison.png')

    Returns:
        PNG image
    """
    logger.info(f"GET /api/charts/{chart_name}")

    chart_path = CHARTS_DIR / chart_name

    if not chart_path.exists():
        return jsonify({
            "error": "Chart not found",
            "available_charts": [f.name for f in CHARTS_DIR.glob("*.png")]
        }), 404

    return send_from_directory(CHARTS_DIR, chart_name)


@app.route('/api/status', methods=['GET'])
def get_status():
    """Повертає status всіх доступних результатів"""
    logger.info("GET /api/status")

    status = {
        "optimization_results": (DATA_DIR / "optimization_results.json").exists(),
        "sensitivity_analysis": (DATA_DIR / "sensitivity_analysis.json").exists(),
        "method_comparison": (DATA_DIR / "method_comparison.json").exists(),
        "monte_carlo_validation": (DATA_DIR / "monte_carlo_results.json").exists(),
        "cost_prediction": (DATA_DIR / "cost_estimate.json").exists(),
        "charts": {
            "topsis_comparison": (CHARTS_DIR / "topsis_comparison.png").exists(),
            "sensitivity_analysis": (CHARTS_DIR / "sensitivity_analysis.png").exists(),
            "method_comparison": (CHARTS_DIR / "method_comparison.png").exists(),
            "cost_breakdown": (CHARTS_DIR / "cost_breakdown.png").exists(),
            "stability_indices": (CHARTS_DIR / "stability_indices.png").exists(),
            "correlation_heatmap": (CHARTS_DIR / "correlation_heatmap.png").exists(),
            "monte_carlo_analysis": (CHARTS_DIR / "monte_carlo_analysis.png").exists(),
        }
    }

    all_ready = all([
        status['optimization_results'],
        status['sensitivity_analysis'],
        status['method_comparison']
    ])

    status['overall_status'] = 'ready' if all_ready else 'incomplete'

    return jsonify(status), 200


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "message": "See GET / for API documentation"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": str(error)
    }), 500


# ==================== MAIN ====================

def main():
    """Запускає API server"""
    print("\n" + "="*70)
    print("TOPSIS CLOUD OPTIMIZATION API")
    print("="*70 + "\n")
    print("Starting Flask server...")
    print("API Documentation: http://localhost:5000/")
    print("Health Check: http://localhost:5000/api/health")
    print("\nPress CTRL+C to stop\n")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False  # Production mode
    )


if __name__ == "__main__":
    main()

const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 8080;

// Middleware для статичних файлів
app.use(express.static(__dirname));

// API endpoint для отримання всіх даних
app.get('/api/data', (req, res) => {
    try {
        const data = {
            success: true,
            instances: {}
        };

        // Завантаження результатів TOPSIS оптимізації
        if (fs.existsSync('optimization_results.json')) {
            data.optimization = JSON.parse(fs.readFileSync('optimization_results.json', 'utf8'));
        }

        // Завантаження даних для кожного інстансу
        const instanceTypes = ['t3.micro', 't3.small', 't3.medium'];

        instanceTypes.forEach(instance => {
            const testFile = `test_${instance.replace('.', '_')}.json`;
            const metricsFile = `metrics_${instance.replace('.', '_')}.json`;

            if (fs.existsSync(testFile) && fs.existsSync(metricsFile)) {
                data.instances[instance] = {
                    test: JSON.parse(fs.readFileSync(testFile, 'utf8')),
                    metrics: JSON.parse(fs.readFileSync(metricsFile, 'utf8'))
                };
            }
        });

        // Завантаження зведених результатів
        if (fs.existsSync('results/summary.json')) {
            data.summary = JSON.parse(fs.readFileSync('results/summary.json', 'utf8'));
        }

        res.json(data);
    } catch (error) {
        console.error('Помилка читання даних:', error.message);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Головна сторінка
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Запуск сервера
app.listen(PORT, () => {
    console.log('╔════════════════════════════════════════╗');
    console.log('║   Cloud Optimization Dashboard Server ║');
    console.log('╚════════════════════════════════════════╝');
    console.log('');
    console.log(`🚀 Сервер запущено на http://localhost:${PORT}`);
    console.log('');
    console.log('📊 Доступні маршрути:');
    console.log(`   • Головна:     http://localhost:${PORT}`);
    console.log(`   • API дані:    http://localhost:${PORT}/api/data`);
    console.log('');
    console.log('💡 Натисни Ctrl+C для зупинки сервера');
    console.log('');
});

// Обробка помилок
process.on('uncaughtException', (error) => {
    console.error('❌ Помилка сервера:', error.message);
});
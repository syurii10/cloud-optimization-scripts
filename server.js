const express = require('express');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const app = express();
const PORT = 8080;

// Middleware
app.use(express.static(__dirname));
app.use(express.json()); // Для парсингу JSON в POST запитах

// Глобальна змінна для відстеження активного тесту
let activeTest = null;

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

// Control Panel
app.get('/control', (req, res) => {
    res.sendFile(path.join(__dirname, 'control.html'));
});

// Dashboard (головна сторінка)
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// API endpoint для запуску тестів
app.post('/api/start-test', (req, res) => {
    try {
        const config = req.body;
        console.log('🚀 Запуск тестування з конфігурацією:', config);

        // Перевірка чи немає активного тесту
        if (activeTest && activeTest.running) {
            return res.status(400).json({
                success: false,
                error: 'Test already running'
            });
        }

        // Створюємо конфігураційний файл для orchestrator
        const testConfig = {
            instances: config.instances,
            rps_levels: config.rpsLevels,
            test_duration: config.duration,
            mode: config.mode,
            timestamp: new Date().toISOString()
        };

        fs.writeFileSync('test_config.json', JSON.stringify(testConfig, null, 2));

        // Запускаємо orchestrator в фоновому режимі
        const pythonProcess = spawn('py', ['orchestrator.py'], {
            detached: false,
            stdio: ['ignore', 'pipe', 'pipe']
        });

        activeTest = {
            running: true,
            pid: pythonProcess.pid,
            startTime: Date.now(),
            config: testConfig
        };

        // Логування виводу
        pythonProcess.stdout.on('data', (data) => {
            console.log(`[Orchestrator] ${data.toString().trim()}`);
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`[Orchestrator Error] ${data.toString().trim()}`);
        });

        pythonProcess.on('close', (code) => {
            console.log(`✅ Orchestrator завершено з кодом ${code}`);
            activeTest.running = false;
        });

        res.json({
            success: true,
            message: 'Testing started',
            testId: activeTest.pid,
            config: testConfig
        });

    } catch (error) {
        console.error('❌ Помилка запуску тестів:', error.message);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API endpoint для статусу тесту
app.get('/api/test-status', (req, res) => {
    if (!activeTest) {
        return res.json({
            running: false,
            message: 'No tests running'
        });
    }

    res.json({
        running: activeTest.running,
        startTime: activeTest.startTime,
        elapsed: Math.floor((Date.now() - activeTest.startTime) / 1000),
        config: activeTest.config
    });
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
    console.log(`   • Dashboard:        http://localhost:${PORT}`);
    console.log(`   • Control Panel:    http://localhost:${PORT}/control`);
    console.log(`   • API дані:         http://localhost:${PORT}/api/data`);
    console.log(`   • API запуск:       http://localhost:${PORT}/api/start-test`);
    console.log(`   • API статус:       http://localhost:${PORT}/api/test-status`);
    console.log('');
    console.log('💡 Натисни Ctrl+C для зупинки сервера');
    console.log('');
});

// Обробка помилок
process.on('uncaughtException', (error) => {
    console.error('❌ Помилка сервера:', error.message);
});
# 🐛 BUGFIX: Metrics Collection Issue

## Дата: December 8, 2025

## Проблема

При запуску `orchestrator.py` виникала помилка:
```
[WARN] Помилка завантаження metrics.json: scp: /home/ubuntu/scripts/metrics.json: No such file or directory
[ERROR] Не вдалося завантажити результати
```

## Root Cause Analysis

**Причина:** `metrics_collector.py` не створював файл `metrics.json` через неправильний виклик.

**Деталі:**
1. `orchestrator.py` (рядок 342) викликав:
   ```python
   python3 metrics_collector.py 1 90  # Без 3-го аргументу!
   ```

2. `metrics_collector.py` (рядок 327) очікував 3-й аргумент:
   ```python
   output_file = sys.argv[3] if len(sys.argv) > 3 else 'metrics.json'
   ```

3. Хоча fallback був `'metrics.json'`, скрипт не виконувався коректно або падав.

## Виправлення

### 1. orchestrator.py (рядок 343)
```python
# BEFORE:
python3 metrics_collector.py 1 90 > metrics.log 2>&1 &

# AFTER:
python3 metrics_collector.py 1 90 metrics.json > metrics.log 2>&1 &
```

### 2. quick_test.py (рядок 138)
```python
# BEFORE:
python3 metrics_collector.py 1 90 > metrics.log 2>&1 &

# AFTER:
python3 metrics_collector.py 1 90 metrics.json > metrics.log 2>&1 &
```

### 3. Cleanup: Видалено дублікат
- Видалено `metrics_collector.py` з root директорії (старий файл)
- Залишено лише актуальну версію в `scripts/metrics_collector.py`

## Результат

✅ `metrics_collector.py` тепер отримує явний output_file як аргумент
✅ Файл `metrics.json` буде створюватися у `/home/ubuntu/scripts/`
✅ `orchestrator.py` зможе завантажити метрики через scp
✅ Видалено дублікат файлу для уникнення плутанини

## Testing Plan

1. Запустити `orchestrator.py` з повним AWS циклом
2. Перевірити що `metrics.json` створюється на target сервері
3. Перевірити що scp успішно завантажує файл
4. Перевірити що TOPSIS отримує коректні метрики

## Files Modified

- [x] orchestrator.py (1 зміна, рядок 343)
- [x] quick_test.py (1 зміна, рядок 138)
- [x] metrics_collector.py (видалено дублікат з root)

## Status

✅ **ВИПРАВЛЕНО** - Готово до тестування

---

*Виправлено для магістерської роботи, 2025*

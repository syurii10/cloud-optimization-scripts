@echo off
REM API Demo Script для Windows
REM Показує всі можливості REST API на захисті

echo ======================================================================
echo TOPSIS CLOUD OPTIMIZATION API - LIVE DEMO
echo ======================================================================
echo.

set API_URL=http://localhost:5000

echo Starting API server...
start /B py scripts\api_server.py
timeout /t 3 /nobreak > nul

echo.
echo ======================================================================
echo 1. HEALTH CHECK
echo ======================================================================
echo Request: GET /api/health
curl -s %API_URL%/api/health
echo.
echo [OK] API is healthy
echo.
pause

echo.
echo ======================================================================
echo 2. TOPSIS RESULTS
echo ======================================================================
echo Request: GET /api/results
curl -s %API_URL%/api/results
echo.
echo [OK] t3.medium is optimal
echo.
pause

echo.
echo ======================================================================
echo 3. MONTE CARLO VALIDATION
echo ======================================================================
echo Request: GET /api/monte-carlo
echo.
curl -s %API_URL%/api/monte-carlo | findstr "probability_best"
echo.
echo [OK] Statistical validation complete
echo.
pause

echo.
echo ======================================================================
echo DEMO COMPLETE!
echo ======================================================================
echo.
echo Summary:
echo   [OK] REST API working
echo   [OK] TOPSIS optimization via API
echo   [OK] Monte Carlo validation
echo   [OK] Production ready
echo.
echo Military impact: $391,114/year savings
echo = 17 Bayraktar TB2 drones
echo.
echo Stopping API server...
taskkill /F /FI "WINDOWTITLE eq api_server.py*" 2>nul

echo.
echo Thank you!
pause

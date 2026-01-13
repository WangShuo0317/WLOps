@echo off
echo ========================================
echo 启动完整数据优化服务
echo ========================================
echo.
echo 此脚本将启动：
echo 1. Redis 服务器（需要单独安装）
echo 2. FastAPI 服务
echo 3. Celery Worker
echo 4. Flower 监控面板
echo.
echo 请确保已安装 Redis！
echo 下载地址: https://github.com/tporadowski/redis/releases
echo.
pause

REM 检查 Redis 是否运行
echo 检查 Redis 服务...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ Redis 未运行！
    echo 请先启动 Redis 服务器
    echo.
    echo 如果已安装 Redis，运行: redis-server
    echo.
    pause
    exit /b 1
)

echo ✅ Redis 运行正常
echo.

REM 启动 API 服务（新窗口）
echo 启动 FastAPI 服务...
start "Data Optimizer API" cmd /k "call venv\Scripts\activate.bat && python app.py"

REM 等待 API 启动
timeout /t 3 /nobreak >nul

REM 启动 Celery Worker（新窗口）
echo 启动 Celery Worker...
start "Celery Worker" cmd /k "call venv\Scripts\activate.bat && celery -A celery_app worker --loglevel=info --concurrency=4 --pool=solo"

REM 等待 Worker 启动
timeout /t 3 /nobreak >nul

REM 启动 Flower 监控（新窗口）
echo 启动 Flower 监控面板...
start "Flower Monitor" cmd /k "call venv\Scripts\activate.bat && celery -A celery_app flower --port=5555"

echo.
echo ========================================
echo ✅ 所有服务已启动！
echo ========================================
echo.
echo 服务地址：
echo - API 服务: http://localhost:8001
echo - API 文档: http://localhost:8001/docs
echo - Flower 监控: http://localhost:5555
echo.
echo 按任意键关闭此窗口...
pause >nul

@echo off
echo ========================================
echo 启动 Celery Worker
echo ========================================

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 启动 Celery Worker
echo.
echo 启动 Celery Worker...
echo 并发数: 4
echo.
celery -A celery_app worker --loglevel=info --concurrency=4 --pool=solo

pause

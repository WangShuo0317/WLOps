@echo off
echo ========================================
echo 启动 Flower (Celery 监控面板)
echo ========================================

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 启动 Flower
echo.
echo 启动 Flower...
echo 访问地址: http://localhost:5555
echo.
celery -A celery_app flower --port=5555

pause

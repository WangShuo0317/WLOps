@echo off
echo ========================================
echo 启动数据优化服务 API
echo ========================================

REM 检查虚拟环境
if not exist "venv" (
    echo 虚拟环境不存在，正在创建...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖...
pip install -r requirements.txt

REM 启动 API 服务
echo.
echo 启动 FastAPI 服务...
echo 访问地址: http://localhost:8001
echo API 文档: http://localhost:8001/docs
echo.
python app.py

pause

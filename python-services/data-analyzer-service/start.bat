@echo off
REM 数据分析服务启动脚本 (Windows)

echo ==========================================
echo 启动数据分析智能体服务
echo ==========================================

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

echo 激活虚拟环境...
call venv\Scripts\activate.bat

echo 安装依赖...
pip install -r requirements.txt

REM 检查环境变量
if "%OPENAI_API_KEY%"=="" (
    echo 警告: OPENAI_API_KEY未设置，LLM功能将不可用
    echo 请设置环境变量: set OPENAI_API_KEY=your-key
)

echo 启动服务...
python app.py

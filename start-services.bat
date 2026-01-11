@echo off
REM 启动所有Python微服务 (Windows)

echo ==========================================
echo   启动IMTS Python微服务
echo ==========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装
    pause
    exit /b 1
)

REM 检查LLaMA Factory
if not exist "LLaMA-Factory" (
    echo [错误] LLaMA Factory未找到
    echo 请先克隆: git clone https://github.com/hiyouga/LLaMA-Factory.git
    pause
    exit /b 1
)

REM 安装依赖
echo [1/4] 安装Python依赖...
pip install -r python-services\requirements.txt

REM 启动训练服务
echo [2/4] 启动训练服务 (端口8001)...
start "训练服务" cmd /k "cd python-services\training-service && python app.py"
timeout /t 2 /nobreak >nul

REM 启动数据分析服务
echo [3/4] 启动数据分析服务 (端口8002)...
start "数据分析服务" cmd /k "cd python-services\data-analyzer-service && call start.bat"
timeout /t 2 /nobreak >nul

REM 启动评测服务
echo [4/4] 启动评测服务 (端口8003)...
start "评测服务" cmd /k "cd python-services\evaluation-service && python app.py"

echo.
echo ==========================================
echo   所有服务已启动
echo ==========================================
echo 训练服务:     http://localhost:8001/docs
echo 数据分析服务: http://localhost:8002/docs
echo 评测服务:     http://localhost:8003/docs
echo.
echo 关闭各个命令窗口即可停止服务
echo.
pause

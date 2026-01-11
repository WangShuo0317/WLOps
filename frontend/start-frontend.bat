@echo off
echo ========================================
echo WLOps 前端启动脚本
echo ========================================
echo.

cd /d %~dp0

if not exist "node_modules" (
    echo 检测到未安装依赖，正在安装...
    call npm install
    if errorlevel 1 (
        echo 依赖安装失败！
        pause
        exit /b 1
    )
)

echo 启动开发服务器...
echo 前端地址: http://localhost:3000
echo 后端代理: http://localhost:8080
echo.
echo 按 Ctrl+C 停止服务器
echo.

call npm run dev

pause

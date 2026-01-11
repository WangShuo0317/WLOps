#!/bin/bash

echo "========================================"
echo "WLOps 前端启动脚本"
echo "========================================"
echo ""

cd "$(dirname "$0")"

if [ ! -d "node_modules" ]; then
    echo "检测到未安装依赖，正在安装..."
    npm install
    if [ $? -ne 0 ]; then
        echo "依赖安装失败！"
        exit 1
    fi
fi

echo "启动开发服务器..."
echo "前端地址: http://localhost:3000"
echo "后端代理: http://localhost:8080"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

npm run dev

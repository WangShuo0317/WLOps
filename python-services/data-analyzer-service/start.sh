#!/bin/bash

# 数据分析服务启动脚本

echo "=========================================="
echo "启动数据分析智能体服务"
echo "=========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

# 检查依赖
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

echo "激活虚拟环境..."
source venv/bin/activate

echo "安装依赖..."
pip install -r requirements.txt

# 检查环境变量
if [ -z "$OPENAI_API_KEY" ]; then
    echo "警告: OPENAI_API_KEY未设置，LLM功能将不可用"
    echo "请设置环境变量: export OPENAI_API_KEY='your-key'"
fi

echo "启动服务..."
python app.py

#!/bin/bash
# 启动所有Python微服务

echo "=========================================="
echo "  启动IMTS Python微服务"
echo "=========================================="
echo ""

# 检查Python
if ! command -v python &> /dev/null; then
    echo "[错误] Python未安装"
    exit 1
fi

# 检查LLaMA Factory
if [ ! -d "LLaMA-Factory" ]; then
    echo "[错误] LLaMA Factory未找到"
    echo "请先克隆: git clone https://github.com/hiyouga/LLaMA-Factory.git"
    exit 1
fi

# 安装依赖
echo "[1/4] 安装Python依赖..."
pip install -r python-services/requirements.txt

# 启动训练服务
echo "[2/4] 启动训练服务 (端口8001)..."
cd python-services/training-service
python app.py &
TRAIN_PID=$!
cd ../..

sleep 2

# 启动数据分析服务
echo "[3/4] 启动数据分析服务 (端口8002)..."
cd python-services/data-analyzer-service
chmod +x start.sh
./start.sh &
ANALYZER_PID=$!
cd ../..

sleep 2

# 启动评测服务
echo "[4/4] 启动评测服务 (端口8003)..."
cd python-services/evaluation-service
python app.py &
EVAL_PID=$!
cd ../..

echo ""
echo "=========================================="
echo "  所有服务已启动"
echo "=========================================="
echo "训练服务:     http://localhost:8001/docs"
echo "数据分析服务: http://localhost:8002/docs"
echo "评测服务:     http://localhost:8003/docs"
echo ""
echo "进程ID:"
echo "  训练服务: $TRAIN_PID"
echo "  数据分析: $ANALYZER_PID"
echo "  评测服务: $EVAL_PID"
echo ""
echo "按Ctrl+C停止所有服务"

# 等待
wait

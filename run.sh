#!/bin/bash
# 桌宠启动脚本

cd "$(dirname "$0")"

# 检查 Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "错误: 未找到 Python"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
$PYTHON -c "import PyQt6" 2>/dev/null || {
    echo "正在安装依赖..."
    $PYTHON -m pip install PyQt6 Pillow --user
}

# 启动桌宠
echo "启动桌宠..."
$PYTHON main.py

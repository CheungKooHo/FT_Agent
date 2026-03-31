#!/bin/bash

# FT-Agent 一键启动脚本

echo "================================"
echo "  FT-Agent 启动脚本"
echo "================================"
echo ""

# 检查是否在正确的目录
if [ ! -d "ft-agent-backend" ] || [ ! -d "ft-agent-frontend" ] || [ ! -d "ft-agent-admin" ]; then
    echo "错误: 请在包含项目的目录下运行此脚本"
    echo "目录结构应该是:"
    echo "  ├── ft-agent-backend/"
    echo "  ├── ft-agent-frontend/"
    echo "  └── ft-agent-admin/"
    exit 1
fi

# 启动后端
echo "步骤 1: 启动后端服务..."
cd ft-agent-backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
if [ ! -f "venv/installed" ]; then
    echo "安装后端依赖..."
    pip install -r requirements.txt
    touch venv/installed
fi

# 初始化数据库
echo "初始化数据库..."
python init_data.py

# 后台启动后端
echo "启动 FastAPI 服务..."
nohup python main.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID)"
echo "访问地址: http://localhost:8000"

cd ..

# 等待后端启动
echo ""
echo "等待后端服务启动..."
sleep 3

# 启动前端
echo ""
echo "步骤 2: 启动用户前端..."
cd ft-agent-frontend

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo "启动 Vite 开发服务器..."
npm run dev &
FRONTEND_PID=$!
echo "用户前端已启动 (PID: $FRONTEND_PID)"
echo "访问地址: http://localhost:3000"

cd ..

# 启动管理后台
echo ""
echo "步骤 3: 启动管理后台..."
cd ft-agent-admin

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo "启动 Vite 开发服务器..."
npm run dev &
ADMIN_PID=$!
echo "管理后台已启动 (PID: $ADMIN_PID)"
echo "访问地址: http://localhost:3001"

cd ..

echo ""
echo "================================"
echo "  所有服务已启动！"
echo "================================"
echo "  用户前端: http://localhost:3000"
echo "  管理后台: http://localhost:3001"
echo "  后端 API: http://localhost:8000"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo "================================"

# 清理函数
cleanup() {
    echo ""
    echo "正在停止服务..."
    kill $BACKEND_PID $FRONTEND_PID $ADMIN_PID 2>/dev/null
    echo "服务已停止"
    exit 0
}

trap cleanup INT TERM

wait

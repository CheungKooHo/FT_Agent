@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ================================
echo   FT-Agent 启动脚本
echo ================================
echo.

:: 检查目录
if not exist "ft-agent-backend" (
    echo 错误: 请在包含项目的目录下运行此脚本
    echo 目录结构应该是:
    echo   ├── ft-agent-backend/
    echo   ├── ft-agent-frontend/
    echo   └── ft-agent-admin/
    pause
    exit /b 1
)

:: 启动后端
echo 步骤 1: 启动后端服务...
cd ft-agent-backend

:: 检查虚拟环境
if not exist "venv" (
    echo 虚拟环境不存在，正在创建...
    python -m venv venv
)

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 检查依赖
if not exist "venv\installed" (
    echo 安装后端依赖...
    pip install -r requirements.txt
    echo installed > venv\installed
)

:: 初始化数据库
echo 初始化数据库...
python init_data.py

:: 后台启动后端
echo 启动 FastAPI 服务...
start /b python main.py > backend.log 2>&1
echo 后端服务已启动
echo 访问地址: http://localhost:8000

cd ..

:: 等待后端启动
echo.
echo 等待后端服务启动...
timeout /t 3 /nobreak >nul

:: 启动用户前端
echo.
echo 步骤 2: 启动用户前端...
cd ft-agent-frontend

if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
)

echo 启动 Vite 开发服务器...
start /b npm run dev > nul 2>&1
echo 用户前端已启动
echo 访问地址: http://localhost:3000

cd ..

:: 启动管理后台
echo.
echo 步骤 3: 启动管理后台...
cd ft-agent-admin

if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
)

echo 启动 Vite 开发服务器...
start /b npm run dev > nul 2>&1
echo 管理后台已启动
echo 访问地址: http://localhost:3001

cd ..

echo.
echo ================================
echo   所有服务已启动！
echo ================================
echo   用户前端: http://localhost:3000
echo   管理后台: http://localhost:3001
echo   后端 API: http://localhost:8000
echo.
echo   按任意键停止所有服务
echo ================================
pause

:: 清理
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
echo 服务已停止

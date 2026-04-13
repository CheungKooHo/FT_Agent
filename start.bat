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

:: 检测 Python 3 路径
set PYTHON_CMD=python
if exist "C:\Users\KooHo\AppData\Local\Python\bin\python3.exe" (
    set PYTHON_CMD=C:\Users\KooHo\AppData\Local\Python\bin\python3.exe
    echo [INFO] 使用 Python 3: %PYTHON_CMD%
) else (
    :: 尝试从 PATH 查找 Python 3
    for /f "tokens=*" %%v in ('python3 -c "import sys; print(sys.executable)" 2^>nul') do set PYTHON_CMD=%%v
)

:: 测试 Python 版本
for /f "tokens=*" %%v in ('!PYTHON_CMD! -c "import sys; print(sys.version_info.major)" 2^>nul') do set PYTHON_MAJOR=%%v
if not "!PYTHON_MAJOR!"=="3" (
    echo [警告] 检测到 Python !PYTHON_MAJOR!，项目需要 Python 3
    echo 请确保安装了 Python 3.8 或更高版本
    pause
    exit /b 1
)

:: 检查 Docker 是否运行
echo 正在检查 Docker 状态...
docker info >nul 2>&1
if errorlevel 1 (
    echo.
    echo [警告] Docker 未运行或无权限
    echo 如果使用 Docker 方式启动，请先启动 Docker Desktop
    echo.
)

:: 启动 PostgreSQL (如果 Docker 可用)
echo.
echo 步骤 0: 检查数据库服务...
netstat -ano 2>nul | findstr ":5432" >nul
if errorlevel 1 (
    echo PostgreSQL 未运行，尝试启动...
    docker start agent-postgres >nul 2>&1
    if errorlevel 1 (
        echo [警告] 无法启动 PostgreSQL
        echo 请确保 Docker 已运行，或手动启动 PostgreSQL
    ) else (
        echo PostgreSQL 已启动
    )
) else (
    echo PostgreSQL 已运行
)

:: 启动后端
echo.
echo 步骤 1: 启动后端服务...
cd ft-agent-backend

:: 检查虚拟环境
if not exist "venv" (
    echo 虚拟环境不存在，正在创建...
    %PYTHON_CMD% -m venv venv
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
%PYTHON_CMD% init_data.py

:: 终止可能占用 8000 端口的旧进程
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo 终止旧后端进程 %%a ...
    taskkill /f /pid %%a >nul 2>&1
)

:: 后台启动后端
echo 启动 FastAPI 服务...
start /b cmd /c "%PYTHON_CMD% main.py >> backend.log 2>&1"
echo 正在等待后端启动...

:: 等待后端启动 (最多 30 秒)
set backend_started=0
for /l %%i in (1,1,30) do (
    timeout /t 1 /nobreak >nul
    netstat -ano 2>nul | findstr ":8000" | findstr "LISTENING" >nul
    if not errorlevel 1 (
        set backend_started=1
        goto :backend_ready
    )
)

:backend_ready
cd ..

if "!backend_started!"=="1" (
    echo 后端服务已就绪 (http://localhost:8000)
) else (
    echo.
    echo [错误] 后端服务启动失败！
    echo 请检查 ft-agent-backend\backend.log 查看错误信息
    echo.
    set /p choice=是否继续启动前端? (y/n):
    if not "!choice!"=="y" exit /b 1
)

:: 启动用户前端
echo.
echo 步骤 2: 启动用户前端...
cd ft-agent-frontend

:: 终止可能占用 3000 端口的旧进程
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":3000" ^| findstr "LISTENING"') do (
    echo 终止旧前端进程 %%a ...
    taskkill /f /pid %%a >nul 2>&1
)

if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
)

echo 启动 Vite 开发服务器...
start /b cmd /c "npm run dev"
echo 正在等待前端启动...

:: 等待前端启动 (最多 30 秒)
set frontend_started=0
for /l %%i in (1,1,30) do (
    timeout /t 1 /nobreak >nul
    netstat -ano 2>nul | findstr ":3000" | findstr "LISTENING" >nul
    if not errorlevel 1 (
        set frontend_started=1
        goto :frontend_ready
    )
)

:frontend_ready
cd ..

if "!frontend_started!"=="1" (
    echo 用户前端已就绪 (http://localhost:3000)
) else (
    echo [警告] 前端可能未正常启动
)

:: 启动管理后台
echo.
echo 步骤 3: 启动管理后台...
cd ft-agent-admin

:: 终止可能占用 3001 端口的旧进程
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":3001" ^| findstr "LISTENING"') do (
    echo 终止旧管理后台进程 %%a ...
    taskkill /f /pid %%a >nul 2>&1
)

if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
)

echo 启动 Vite 开发服务器...
start /b cmd /c "npm run dev -- --port 3001"
echo 正在等待管理后台启动...

:: 等待管理后台启动 (最多 30 秒)
set admin_started=0
for /l %%i in (1,1,30) do (
    timeout /t 1 /nobreak >nul
    netstat -ano 2>nul | findstr ":3001" | findstr "LISTENING" >nul
    if not errorlevel 1 (
        set admin_started=1
        goto :admin_ready
    )
)

:admin_ready
cd ..

if "!admin_started!"=="1" (
    echo 管理后台已就绪 (http://localhost:3001)
) else (
    echo [警告] 管理后台可能未正常启动
)

echo.
echo ================================
echo   启动检查完成
echo ================================
echo   用户前端: http://localhost:3000
echo   管理后台: http://localhost:3001
echo   后端 API: http://localhost:8000
echo.
echo   按任意键停止所有服务
echo ================================
pause

:: 清理
echo 正在停止服务...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
echo 服务已停止

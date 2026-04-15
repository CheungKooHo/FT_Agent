@echo off
chcp 65001 >nul

echo ================================
echo   FT-Agent 启动脚本
echo ================================
echo.

:: 设置 Python 路径
set PYTHON=C:\Users\KooHo\AppData\Local\Python\bin\python3.exe

:: 1. 启动后端
echo [1/3] 启动后端服务...
cd /d %~dp0ft-agent-backend
del backend.log 2>nul
start "Backend" %PYTHON% main.py
cd %~dp0

:: 2. 启动前端
echo [2/3] 启动用户前端...
cd /d %~dp0ft-agent-frontend
start "Frontend" npm run dev
cd %~dp0

:: 3. 启动管理后台
echo [3/3] 启动管理后台...
cd /d %~dp0ft-agent-admin
start "Admin" npm run dev
cd %~dp0

echo.
echo ================================
echo   服务已启动
echo ================================
echo   前端: http://localhost:3000
echo   管理后台: http://localhost:3001
echo   后端: http://localhost:8000
echo.
echo   管理员: admin / admin123
echo ================================
pause

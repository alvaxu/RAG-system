@echo off
chcp 65001 >nul
echo 🎉 RAG系统V3启动脚本
echo ================================================

echo.
echo 正在检查环境...

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未配置到PATH
    echo 💡 请安装Python 3.8+并配置到系统PATH
    pause
    exit /b 1
)

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装或未配置到PATH
    echo 💡 请安装Node.js 16+并配置到系统PATH
    pause
    exit /b 1
)

REM 检查npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm未安装或未配置到PATH
    echo 💡 请确保Node.js安装完整
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.
echo 请选择启动方式:
echo 1. 启动后端API服务
echo 2. 启动前端界面
echo 3. 启动完整系统（推荐）
echo 4. 运行API接口测试
echo 5. 运行后端功能测试
echo 6. 退出

set /p choice=请输入选择 (1-6): 

if "%choice%"=="1" goto start_backend
if "%choice%"=="2" goto start_frontend
if "%choice%"=="3" goto start_full
if "%choice%"=="4" goto test_api
if "%choice%"=="5" goto test_system
if "%choice%"=="6" goto exit
goto invalid

:start_backend
echo.
echo 🚀 启动后端API服务...
python -m uvicorn rag_system.api.main:app --host 0.0.0.0 --port 8000 --reload
goto end

:start_frontend
echo.
echo 🎨 启动前端界面...
cd frontend

REM 检查package.json是否存在
if not exist package.json (
    echo ❌ 前端目录不存在package.json文件
    echo 💡 请确保在正确的项目目录中运行此脚本
    pause
    goto end
)

REM 检查node_modules是否存在，如果不存在则自动安装
if not exist node_modules (
    echo 📦 检测到缺少依赖，正在自动安装...
    npm install
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        goto end
    )
)

echo 🚀 启动前端开发服务器...
npm run dev
goto end

:start_full
echo.
echo 🚀 启动完整系统...
echo 启动后端API服务...
start "RAG Backend" cmd /k "python -m uvicorn rag_system.api.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul

echo 检查前端依赖...
cd frontend
if not exist node_modules (
    echo 📦 检测到缺少前端依赖，正在自动安装...
    npm install
    if errorlevel 1 (
        echo ❌ 前端依赖安装失败
        cd ..
        pause
        goto end
    )
)
cd ..

echo 启动前端界面...
start "RAG Frontend" cmd /k "cd frontend && npm run dev"
echo.
echo ✅ 系统启动完成！
echo 📍 后端API: http://localhost:8000
echo 📍 前端界面: http://localhost:3000
echo 📖 API文档: http://localhost:8000/docs
echo.
echo 💡 提示：两个服务窗口将分别显示后端和前端日志
echo 💡 关闭服务：在对应的命令窗口中按 Ctrl+C
goto end

:test_api
echo.
echo 🧪 运行API接口测试...
python test_rag_api.py
goto end

:test_system
echo.
echo 🧪 运行后端功能测试...
cd rag_system\tests
python run_backend_tests.py
goto end

:invalid
echo.
echo ❌ 无效选择，请重新运行脚本
goto end

:exit
echo.
echo 👋 再见！
goto end

:end
echo.
pause

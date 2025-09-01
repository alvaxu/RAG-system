@echo off
chcp 65001 >nul
echo 🎉 RAG系统V3启动脚本
echo ================================================

echo.
echo 请选择启动方式:
echo 1. 启动后端API服务
echo 2. 启动前端界面
echo 3. 启动完整系统
echo 4. 运行API测试
echo 5. 运行系统测试
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
npm run dev
goto end

:start_full
echo.
echo 🚀 启动完整系统...
echo 启动后端API服务...
start "RAG Backend" cmd /k "python -m uvicorn rag_system.api.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak >nul
echo 启动前端界面...
start "RAG Frontend" cmd /k "cd frontend && npm run dev"
echo.
echo ✅ 系统启动完成！
echo 📍 后端API: http://localhost:8000
echo 📍 前端界面: http://localhost:3000
echo 📖 API文档: http://localhost:8000/docs
goto end

:test_api
echo.
echo 🧪 运行API测试...
python test_rag_api.py
goto end

:test_system
echo.
echo 🧪 运行系统测试...
cd rag_system\tests
python run_all_tests.py
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

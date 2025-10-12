
@echo off
chcp 65001 >nul 2>&1
echo RAG系统V3启动脚本
echo ================================================

echo.
echo 正在检查环境...

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装或未配置到PATH
    echo [提示] 请安装Python 3.8+并配置到系统PATH
    pause
    exit /b 1
)

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Node.js未安装或未配置到PATH
    echo [提示] 请安装Node.js 16+并配置到系统PATH
    pause
    exit /b 1
)

echo [成功] 环境检查通过
echo.
echo 正在启动RAG系统V3快速启动工具...
echo.

REM 直接调用Python启动脚本
python start_rag_system.py

echo.
echo 脚本执行完成
pause

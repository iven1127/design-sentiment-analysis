@echo off
chcp 65001
cls
echo ====================================
echo  设计舆情分析工具 - 启动器
echo ====================================
echo.

echo [1/2] 检查 Python...
python --version
if errorlevel 1 (
    echo.
    echo ❌ Python 未安装！
    echo.
    echo 请先安装 Python: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo.
echo [2/2] 正在启动 Web 界面...
echo.
echo ====================================
echo  服务启动中，请稍候...
echo ====================================
echo.

cd /d "%~dp0"
python -m streamlit run web/app.py

echo.
echo.
echo ====================================
echo  服务已停止
echo ====================================
pause

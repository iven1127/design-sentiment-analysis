@echo off
chcp 65001
echo ====================================
echo  设计舆情分析工具 - 完整安装
echo ====================================
echo.

echo [1/4] 检查 Python...
python --version
if errorlevel 1 (
    echo.
    echo ❌ Python 未安装或未添加到 PATH！
    echo.
    echo 请前往 https://www.python.org/downloads/ 下载安装 Python
    echo 安装时务必勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo.
echo [2/4] 安装依赖（可能需要几分钟）...
python -m pip install --upgrade pip
python -m pip install streamlit pandas plotly requests fastapi uvicorn sqlalchemy python-dotenv playwright transformers torch pyyaml pytest

if errorlevel 1 (
    echo.
    echo ❌ 依赖安装失败！
    pause
    exit /b 1
)

echo.
echo [3/4] 安装 Playwright 浏览器...
python -m playwright install chromium

echo.
echo [4/4] 初始化数据库...
python cli.py init

echo.
echo ====================================
echo  ✅ 安装完成！
echo ====================================
echo.
echo 按任意键启动 Web 界面...
pause

python -m streamlit run web/app.py

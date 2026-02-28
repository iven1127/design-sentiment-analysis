@echo off
chcp 65001
echo ====================================
echo  设计舆情分析工具 - Web 启动器
echo ====================================
echo.

echo [1/3] 检查依赖...
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo 依赖安装失败！
    pause
    exit /b 1
)

echo [2/3] 初始化数据库...
python cli.py init
if errorlevel 1 (
    echo 数据库初始化失败！
    pause
    exit /b 1
)

echo [3/3] 启动 Web 界面...
echo.
echo ====================================
echo  启动成功！
echo  请在浏览器中打开：
echo  http://localhost:8501
echo ====================================
echo.
python -m streamlit run web/app.py
pause

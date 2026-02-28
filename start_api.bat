@echo off
chcp 65001
echo ====================================
echo  设计舆情分析工具 - API 启动器
echo ====================================
echo.

echo [1/2] 初始化数据库...
python cli.py init

echo [2/2] 启动 API 服务...
echo.
echo ====================================
echo  启动成功！
echo  API 文档：http://localhost:8000/docs
echo ====================================
echo.
python -m uvicorn api.main:app --reload
pause

"""简化启动器"""
import os
import sys
import subprocess

print("=" * 50)
print("  设计舆情分析工具 - 启动器")
print("=" * 50)
print()

# 1. 检查依赖
print("[1/3] 检查依赖...")
try:
    import streamlit
    print("✅ Streamlit 已安装")
except ImportError:
    print("❌ Streamlit 未安装，正在安装...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "pandas", "plotly", "requests"])
    print("✅ 安装完成")

# 2. 初始化数据库
print()
print("[2/3] 初始化数据库...")
try:
    from core.models import init_database
    init_database()
    print("✅ 数据库初始化完成")
except Exception as e:
    print(f"⚠️ 数据库初始化失败: {e}")
    print("   (首次运行可能会有一些警告，可以忽略)")

# 3. 启动 Web 服务
print()
print("[3/3] 启动 Web 界面...")
print()
print("=" * 50)
print("  🚀 服务启动中...")
print("  📱 请在浏览器打开: http://localhost:8501")
print("=" * 50)
print()

# 启动 Streamlit
os.system(f'"{sys.executable}" -m streamlit run web/app.py')

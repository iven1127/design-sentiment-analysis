#!/bin/bash

# 安装Python依赖
pip install -q -r requirements.txt

# 安装Playwright浏览器（用于爬虫）
python -m playwright install chromium --quiet || true

# 启动Streamlit服务
streamlit run sentiment_monitor.py \
  --server.port 8080 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false

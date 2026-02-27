# 小红书舆情分析工具

自动汇总监控关键词/品牌的舆情分析工具，每5小时自动更新，提供Web界面展示。

## 功能特性
- 自动爬取小红书关键词相关帖子
- 情感倾向分析（正面/中性/负面）
- 热度统计分析
- 趋势变化追踪
- 直接链接到原帖子
- Web界面可视化展示

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
playwright install chromium
```

### 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，设置 COOKIE_VALUE、DATABASE_URL 等
```

### 运行Web界面
```bash
streamlit run web/app.py
```

### 启动定时爬虫
```bash
python crawler/main.py
```

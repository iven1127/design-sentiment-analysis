# 设计舆情分析

一个功能强大的设计内容舆情分析工具，支持批量数据采集、AI情感分析和可视化展示。

## 功能特性

- **数据爬取**：基于 Playwright 的自动化爬虫，支持批量爬取小红书帖子
- **情感分析**：基于 transformers 的中文情感分析模型，识别积极/消极/中性情感
- **情感细分**：分析开心、难过、生气、恐惧、惊讶等细分情感
- **数据存储**：使用 SQLite 数据库持久化存储爬取和分析结果
- **REST API**：提供完整的 RESTful API 接口
- **Web 界面**：基于 Streamlit 的可视化 Web 界面
- **CLI 工具**：命令行工具支持快速操作
- **任务管理**：异步任务处理，支持批量操作和进度跟踪

## 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装依赖

```bash
# 创建虚拟环境（可选）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 根据需要编辑 .env 文件
```

### 初始化数据库

```bash
python cli.py init
```

### 运行应用

#### 方式一：使用命令行工具

```bash
# 启动 API 服务
python cli.py api

# 启动 Web 界面（包含 API）
python cli.py web

# 爬取单个帖子
python cli.py scrape "https://www.xiaohongshu.com/explore/xxx" --analyze

# 爬取多个帖子
python cli.py scrape "url1,url2,url3" --analyze

# 分析文本情感
python cli.py analyze --text "这个产品真的很好用！"

# 查看统计信息
python cli.py stats

# 清理数据
python cli.py clean --all
```

#### 方式二：使用 Streamlit

```bash
streamlit run web/app.py
```

访问 http://localhost:8501 使用 Web 界面。

#### 方式三：使用 FastAPI

```bash
uvicorn api.main:app --reload
```

访问 http://localhost:8000 查看 API 文档。

## API 文档

启动 API 服务后，访问 http://localhost:8000/docs 查看完整 API 文档。

### 主要端点

- `GET /` - 根路径
- `GET /health` - 健康检查
- `POST /api/v1/scrape` - 爬取单个帖子
- `POST /api/v1/scrape/batch` - 批量爬取帖子
- `GET /api/v1/task/{task_id}` - 获取任务状态
- `POST /api/v1/analyze` - 分析文本情感
- `POST /api/v1/analyze/batch` - 批量分析文本
- `GET /api/v1/posts` - 获取帖子列表
- `GET /api/v1/posts/{post_id}` - 获取帖子详情
- `GET /api/v1/stats/summary` - 获取情感分析汇总
- `DELETE /api/v1/posts` - 删除所有帖子

## 项目结构

```
xhs-sentiment-analyzer/
├── api/                    # API 模块
│   ├── __init__.py
│   └── main.py            # FastAPI 主应用
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── crawler.py         # 爬虫模块
│   ├── exceptions.py      # 自定义异常
│   ├── logger.py          # 日志配置
│   ├── models.py          # 数据库模型
│   ├── retry.py           # 重试机制
│   └── sentiment.py       # 情感分析
├── tests/                  # 测试模块
│   ├── core/
│   │   ├── test_models.py
│   │   ├── test_retry.py
│   │   └── test_sentiment.py
│   └── __init__.py
├── web/                    # Web 界面
│   └── app.py             # Streamlit 应用
├── .env.example           # 环境变量模板
├── .gitignore             # Git 忽略文件
├── .streamlit/            # Streamlit 配置
│   └── config.toml
├── cli.py                 # 命令行工具
├── requirements.txt       # 依赖列表
└── README.md             # 项目文档
```

## 配置说明

### 环境变量

在 `.env` 文件中配置以下选项：

```env
# 数据库配置
DATABASE_URL=sqlite:///xhs_sentiment.db
DATABASE_ECHO=false

# API配置
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_LOG_LEVEL=info

# Web配置
WEB_PORT=8501
WEB_THEME=light

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=logs

# 爬虫配置
CRAWLER_HEADLESS=true
CRAWLER_MAX_RETRIES=3

# 情感分析配置
SENTIMENT_MODEL=uer/roberta-base-finetuned-dianping-chinese
SENTIMENT_BATCH_SIZE=8

# 任务配置
TASK_MAX_CONCURRENT=5
```

## 开发指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/core/test_sentiment.py

# 显示详细输出
pytest -v
```

### 代码风格

项目遵循 PEP 8 代码风格规范。

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 注意事项

1. **合法使用**：请确保遵守小红书的服务条款和 robots.txt 规定
2. **频率限制**：避免过于频繁的请求，以免被反爬虫机制限制
3. **数据隐私**：爬取的数据请注意用户隐私保护
4. **模型大小**：情感分析模型较大，首次运行需要下载

## 常见问题

### 1. 爬取失败怎么办？

- 检查网络连接
- 确认 URL 格式正确
- 尝试增加重试次数
- 可能需要登录（待实现登录功能）

### 2. 情感分析模型加载慢？

- 首次加载需要下载模型，请耐心等待
- 可以更换更小的模型
- 使用 GPU 加速（需要 CUDA）

### 3. 数据库文件在哪里？

默认在项目根目录的 `xhs_sentiment.db`

### 4. 如何更换模型？

修改 `.env` 文件中的 `SENTIMENT_MODEL` 变量，或在代码中指定模型名称。

## 许可证

本项目仅供学习交流使用。

## 联系方式

如有问题或建议，请提交 Issue。

# 🚀 Streamlit Cloud 部署指南

## 📋 准备工作

所有配置文件已准备完成：
- ✅ `.streamlit/config.toml` - Streamlit配置
- ✅ `packages.txt` - 系统依赖
- ✅ `requirements.txt` - Python依赖
- ✅ `sentiment_monitor.py` - 主应用

---

## 🌐 部署步骤

### 1. 推送代码到 GitHub

如果还没有推送到GitHub，请运行：

```bash
# 初始化git（如果还没有）
git init
git add .
git commit -m "feat: ready for Streamlit Cloud deployment"

# 推送到GitHub
git remote add origin https://github.com/你的用户名/xhs-sentiment-analyzer.git
git branch -M main
git push -u origin main
```

### 2. 部署到 Streamlit Cloud

1. **访问 Streamlit Cloud**
   ```
   https://streamlit.io/cloud
   ```

2. **登录**
   - 使用GitHub账号登录
   - 授权Streamlit访问您的仓库

3. **创建新应用**
   - 点击 "New app"
   - Repository: 选择 `xhs-sentiment-analyzer`
   - Branch: `main`
   - Main file path: `sentiment_monitor.py`

4. **高级设置（可选）**
   - Python version: 3.9 或 3.10
   - 如果需要环境变量，在这里添加

5. **点击 Deploy**
   - 等待3-5分钟
   - 部署完成后会自动打开应用

---

## ⚠️ 重要提示

### 关于依赖包大小

当前 `requirements.txt` 包含了完整功能所需的所有依赖，包括：
- `torch` (约2GB) - AI模型
- `transformers` (约400MB) - NLP库
- `playwright` (约300MB) - 爬虫

**这可能导致：**
- 部署时间较长（10-15分钟）
- 可能超出Streamlit Cloud免费版资源限制

### 解决方案

如果部署失败，使用精简版依赖：

```bash
# 备份完整版
mv requirements.txt requirements-full.txt

# 使用精简版
mv requirements-lite.txt requirements.txt

# 重新部署
```

精简版将禁用：
- ❌ AI情感分析
- ❌ 真实数据爬取
- ✅ 保留数据可视化
- ✅ 保留演示功能

---

## 🔧 部署后配置

### 1. 环境变量（如需要）

在Streamlit Cloud的App设置中添加：

```
ENABLE_CRAWLER=false  # 云端禁用爬虫
ENABLE_AI=false       # 云端禁用AI分析
```

### 2. 资源限制

Streamlit Cloud 免费版限制：
- 内存: 1GB
- CPU: 共享
- 存储: 有限

如果应用经常重启，考虑：
1. 使用精简版依赖
2. 升级到付费计划
3. 使用其他云平台（Heroku, Railway等）

---

## 📱 访问应用

部署成功后，您会获得一个URL：
```
https://你的用户名-xhs-sentiment-analyzer.streamlit.app
```

可以分享这个链接给任何人使用！

---

## 🐛 常见问题

### Q: 部署失败，显示"Resource limit exceeded"
**A:** 使用精简版 requirements-lite.txt

### Q: 应用启动慢
**A:** 首次冷启动需要时间，后续会快很多

### Q: 爬虫功能无法使用
**A:** Streamlit Cloud 限制浏览器自动化，建议使用演示模式或部署到其他平台

### Q: 如何更新应用？
**A:** 推送新代码到GitHub，Streamlit Cloud会自动重新部署

---

## 📞 需要帮助？

- Streamlit文档: https://docs.streamlit.io/streamlit-community-cloud
- 部署问题: https://discuss.streamlit.io

祝您部署顺利！🎉

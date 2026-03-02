"""小红书舆情分析系统 - 完整版"""
import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 页面配置
st.set_page_config(
    page_title="设计舆情分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 标题
st.title("📊 设计舆情分析系统")
st.markdown("基于小红书的舆情监控与情感分析")
st.markdown("---")

# 初始化 session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'analysis_report' not in st.session_state:
    st.session_state.analysis_report = None
if 'is_searching' not in st.session_state:
    st.session_state.is_searching = False

# 侧边栏 - 搜索配置
st.sidebar.header("🔍 搜索配置")
keyword = st.sidebar.text_input("关键词", placeholder="例如：产品设计、UI设计...")
max_count = st.sidebar.slider("爬取数量", min_value=10, max_value=500, value=100, step=10)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ 高级设置")
enable_analysis = st.sidebar.checkbox("启用情感分析", value=True)
headless = st.sidebar.checkbox("无头模式（不显示浏览器）", value=True)

search_button = st.sidebar.button("🚀 开始搜索", type="primary", use_container_width=True, disabled=st.session_state.is_searching)

if search_button:
    if not keyword:
        st.sidebar.error("⚠️ 请输入关键词！")
    else:
        st.session_state.is_searching = True
        st.sidebar.info(f"🔍 正在搜索 {keyword} 相关内容...")

        try:
            # 导入爬虫模块
            from core.crawler import XHSCrawler
            from core.sentiment import SentimentAnalyzer
            from core.logger import setup_logger

            logger = setup_logger("xhs_search")

            # 创建分析器
            analyzer = None
            if enable_analysis:
                with st.spinner("初始化情感分析器..."):
                    try:
                        analyzer = SentimentAnalyzer()
                        st.sidebar.success("✅ 分析器初始化成功")
                    except Exception as e:
                        st.sidebar.warning(f"⚠️ 分析器初始化失败: {e}")
                        st.sidebar.info("💡 将继续爬取但不进行情感分析")

            # 开始爬取
            progress_text = st.empty()
            progress_bar = st.progress(0)
            status_text = st.empty()

            async def run_search():
                results = []

                async with XHSCrawler(headless=headless) as crawler:
                    progress_text.text("📡 正在搜索小红书...")

                    # 搜索获取帖子列表
                    search_results = await crawler.scrape_search_results(
                        keyword=keyword,
                        max_pages=(max_count // 20) + 1,
                        per_page=20
                    )

                    total = min(len(search_results), max_count)
                    progress_text.text(f"找到 {total} 个相关帖子，开始爬取...")

                    # 爬取每个帖子
                    for i, search_result in enumerate(search_results[:max_count]):
                        try:
                            progress = (i + 1) / total
                            progress_bar.progress(progress)
                            status_text.text(f"正在爬取第 {i+1}/{total} 条...")

                            # 爬取帖子详情
                            post = await crawler.scrape_post(search_result['url'])

                            # 情感分析
                            sentiment_result = None
                            if analyzer and post.content:
                                try:
                                    sentiment_result = analyzer.analyze_title_content(
                                        post.title,
                                        post.content
                                    )
                                except Exception as e:
                                    logger.warning(f"情感分析失败: {e}")

                            results.append({
                                'id': post.post_id,
                                'title': post.title,
                                'content': post.content,
                                'author': post.author,
                                'likes': post.likes,
                                'comments': post.comments,
                                'collects': post.collects,
                                'shares': post.shares,
                                'url': post.url,
                                'images': post.images,
                                'tags': post.tags,
                                'sentiment': sentiment_result.label.value if sentiment_result else 'unknown',
                                'sentiment_score': sentiment_result.score if sentiment_result else 0,
                                'sentiment_confidence': sentiment_result.confidence if sentiment_result else 0,
                                'emotions': sentiment_result.emotions if sentiment_result else {},
                            })

                        except Exception as e:
                            logger.error(f"爬取失败: {e}")
                            continue

                return results

            # 运行爬取
            try:
                results = asyncio.run(run_search())
                st.session_state.search_results = results

                progress_bar.empty()
                progress_text.empty()
                status_text.empty()

                if results:
                    st.sidebar.success(f"✅ 成功爬取 {len(results)} 条数据！")
                else:
                    st.sidebar.warning("⚠️ 未获取到数据，请检查关键词或网络")

            except Exception as e:
                st.sidebar.error(f"❌ 爬取失败: {str(e)}")
                st.error(f"详细错误: {e}")

        except ImportError as e:
            st.sidebar.error("❌ 模块导入失败，请确保已安装所有依赖")
            st.error(f"错误详情: {e}")

        finally:
            st.session_state.is_searching = False

# 主界面
if st.session_state.search_results:
    results = st.session_state.search_results

    # 舆情分析报告
    st.header("📈 舆情分析报告")

    # 计算统计数据
    total = len(results)
    positive = sum(1 for r in results if r['sentiment'] == 'positive')
    negative = sum(1 for r in results if r['sentiment'] == 'negative')
    neutral = sum(1 for r in results if r['sentiment'] == 'neutral')
    unknown = sum(1 for r in results if r['sentiment'] == 'unknown')

    avg_likes = sum(r['likes'] for r in results) / total if total > 0 else 0
    avg_comments = sum(r['comments'] for r in results) / total if total > 0 else 0

    # 顶部指标
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总帖子数", f"{total} 条")

    with col2:
        positive_ratio = (positive / total * 100) if total > 0 else 0
        st.metric("积极情感", f"{positive_ratio:.1f}%", delta=f"{positive} 条")

    with col3:
        negative_ratio = (negative / total * 100) if total > 0 else 0
        st.metric("消极情感", f"{negative_ratio:.1f}%", delta=f"{negative} 条", delta_color="inverse")

    with col4:
        neutral_ratio = (neutral / total * 100) if total > 0 else 0
        st.metric("中性情感", f"{neutral_ratio:.1f}%", delta=f"{neutral} 条")

    st.markdown("---")

    # 图表展示
    col1, col2 = st.columns(2)

    with col1:
        # 情感分布饼图
        sentiment_data = pd.DataFrame({
            '情感': ['积极', '消极', '中性', '未知'],
            '数量': [positive, negative, neutral, unknown],
        })
        sentiment_data = sentiment_data[sentiment_data['数量'] > 0]

        fig_pie = px.pie(
            sentiment_data,
            values='数量',
            names='情感',
            title='情感分布',
            color='情感',
            color_discrete_map={
                '积极': '#4CAF50',
                '消极': '#F44336',
                '中性': '#FF9800',
                '未知': '#9E9E9E'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # 情感柱状图
        fig_bar = px.bar(
            sentiment_data,
            x='情感',
            y='数量',
            title='情感数量统计',
            color='情感',
            color_discrete_map={
                '积极': '#4CAF50',
                '消极': '#F44336',
                '中性': '#FF9800',
                '未知': '#9E9E9E'
            }
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # 互动数据分析
    st.subheader("💬 互动数据分析")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("平均点赞数", f"{avg_likes:.0f}")

    with col2:
        st.metric("平均评论数", f"{avg_comments:.0f}")

    with col3:
        total_likes = sum(r['likes'] for r in results)
        st.metric("总点赞数", f"{total_likes:,}")

    with col4:
        total_comments = sum(r['comments'] for r in results)
        st.metric("总评论数", f"{total_comments:,}")

    st.markdown("---")

    # 详细数据表格
    st.header("📋 搜索结果详情")

    # 筛选选项
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        sentiment_filter = st.selectbox(
            "情感筛选",
            ["全部", "积极", "消极", "中性", "未知"]
        )

    with filter_col2:
        sort_option = st.selectbox(
            "排序方式",
            ["点赞数（高到低）", "点赞数（低到高）", "评论数（高到低）", "评论数（低到高）"]
        )

    with filter_col3:
        min_likes = st.number_input("最小点赞数", min_value=0, value=0)

    # 应用筛选
    filtered_results = results

    if sentiment_filter != "全部":
        sentiment_map = {"积极": "positive", "消极": "negative", "中性": "neutral", "未知": "unknown"}
        filtered_results = [r for r in filtered_results if r['sentiment'] == sentiment_map[sentiment_filter]]

    filtered_results = [r for r in filtered_results if r['likes'] >= min_likes]

    # 应用排序
    if "点赞数" in sort_option:
        reverse = "高到低" in sort_option
        filtered_results = sorted(filtered_results, key=lambda x: x['likes'], reverse=reverse)
    elif "评论数" in sort_option:
        reverse = "高到低" in sort_option
        filtered_results = sorted(filtered_results, key=lambda x: x['comments'], reverse=reverse)

    st.write(f"显示 **{len(filtered_results)}** / {total} 条结果")

    # 分页显示
    items_per_page = 10
    total_pages = max(1, (len(filtered_results) - 1) // items_per_page + 1)

    if total_pages > 1:
        page = st.number_input("页码", min_value=1, max_value=total_pages, value=1, step=1)
    else:
        page = 1

    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(filtered_results))

    # 显示结果
    for i, post in enumerate(filtered_results[start_idx:end_idx], start=start_idx + 1):
        with st.expander(f"#{i} {post['title'][:50]}... - @{post['author']}", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write("**内容：**")
                st.write(post['content'][:300] + "..." if len(post['content']) > 300 else post['content'])

                if post['tags']:
                    st.write("**标签：**", " ".join(post['tags'][:5]))

                st.write(f"**原文链接：** {post['url']}")

            with col2:
                st.metric("👍 点赞", f"{post['likes']:,}")
                st.metric("💬 评论", f"{post['comments']:,}")
                st.metric("⭐ 收藏", f"{post['collects']:,}")

                sentiment_emoji = {
                    'positive': '😊 积极',
                    'negative': '😞 消极',
                    'neutral': '😐 中性',
                    'unknown': '❓ 未知'
                }
                st.write("**情感：**")
                st.write(sentiment_emoji.get(post['sentiment'], '❓ 未知'))
                if post['sentiment_score'] > 0:
                    st.write(f"**置信度：** {post['sentiment_confidence']:.2%}")

    st.markdown("---")

    # 导出功能
    st.header("📥 导出数据")

    col1, col2 = st.columns(2)

    with col1:
        # 导出 CSV
        df = pd.DataFrame([{
            'ID': r['id'],
            '标题': r['title'],
            '内容': r['content'],
            '作者': r['author'],
            '点赞': r['likes'],
            '评论': r['comments'],
            '收藏': r['collects'],
            '分享': r['shares'],
            'URL': r['url'],
            '情感': r['sentiment'],
            '情感分数': r['sentiment_score'],
            '置信度': r['sentiment_confidence'],
        } for r in results])

        csv = df.to_csv(index=False, encoding='utf-8-sig')

        st.download_button(
            label="📄 导出 CSV 数据",
            data=csv,
            file_name=f"舆情数据_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        # 导出报告
        report = f"""# 设计舆情分析报告

**关键词：** {keyword}
**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**数据量：** {total} 条

## 一、情感分析

- **积极情感：** {positive} 条（{positive_ratio:.1f}%）
- **消极情感：** {negative} 条（{negative_ratio:.1f}%）
- **中性情感：** {neutral} 条（{neutral_ratio:.1f}%）

## 二、互动数据

- **总点赞数：** {sum(r['likes'] for r in results):,}
- **总评论数：** {sum(r['comments'] for r in results):,}
- **平均点赞数：** {avg_likes:.0f}
- **平均评论数：** {avg_comments:.0f}

## 三、热门内容

### Top 5 点赞最多

{chr(10).join([f"{i+1}. {post['title']} - {post['likes']:,} 点赞" for i, post in enumerate(sorted(results, key=lambda x: x['likes'], reverse=True)[:5])])}

## 四、结论

{'✅ 积极情感占主导，整体舆情良好。' if positive > negative else '⚠️ 消极情感较多，需要关注和改进。' if negative > positive else '➡️ 情感较为中性，舆情平稳。'}

---
*本报告由设计舆情分析系统自动生成*
        """

        st.download_button(
            label="📊 导出分析报告",
            data=report,
            file_name=f"舆情报告_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )

else:
    # 空状态
    st.info("👈 请在左侧输入关键词并点击"开始搜索"")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ## 📖 使用说明

        1. **输入关键词**：在左侧输入框输入想要搜索的关键词
        2. **设置参数**：选择爬取数量（10-500条）
        3. **高级设置**：
           - 启用/禁用情感分析
           - 选择浏览器模式
        4. **开始搜索**：点击"开始搜索"按钮
        5. **查看结果**：等待爬取完成，查看舆情分析报告
        6. **导出数据**：可以导出 CSV 和分析报告
        """)

    with col2:
        st.markdown("""
        ## ✨ 功能特点

        - 📊 **实时数据爬取**：自动爬取小红书相关内容
        - 🤖 **AI 情感分析**：基于深度学习的情感识别
        - 📈 **可视化图表**：直观展示舆情趋势
        - 🔍 **数据筛选**：支持多维度筛选和排序
        - 💬 **互动统计**：点赞、评论、收藏数据分析
        - 📥 **数据导出**：支持 CSV 和 Markdown 格式
        """)

    st.markdown("---")

    st.warning("""
    ⚠️ **注意事项：**
    - 首次使用需要下载情感分析模型（约400MB）
    - 爬取过程可能需要几分钟，请耐心等待
    - 建议使用无头模式以提高爬取效率
    - 遵守小红书服务条款，合理使用工具
    """)

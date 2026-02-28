"""Streamlit Web 应用"""
import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

# 配置页面
st.set_page_config(
    page_title="设计舆情分析工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API 配置
API_BASE_URL = "http://localhost:8000/api/v1"

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #ff2442;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stMetric {
        background-color: #ff2442;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """初始化 session state"""
    if 'posts' not in st.session_state:
        st.session_state.posts = []
    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'current_task_id' not in st.session_state:
        st.session_state.current_task_id = None


def scrape_posts(urls: List[str], analyze: bool = True) -> Dict:
    """爬取帖子"""
    try:
        if len(urls) == 1:
            response = requests.post(
                f"{API_BASE_URL}/scrape",
                json={"url": urls[0], "analyze": analyze},
                timeout=10,
            )
        else:
            response = requests.post(
                f"{API_BASE_URL}/scrape/batch",
                json={"urls": urls, "analyze": analyze},
                timeout=10,
            )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"请求失败: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"爬取失败: {e}")
        return {}


def check_task_status(task_id: str) -> Dict:
    """检查任务状态"""
    try:
        response = requests.get(f"{API_BASE_URL}/task/{task_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception:
        return {}


def get_posts(skip: int = 0, limit: int = 100) -> List[Dict]:
    """获取帖子列表"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/posts",
            params={"skip": skip, "limit": limit},
            timeout=10,
        )
        if response.status_code == 200:
            return response.json().get('posts', [])
        return []
    except Exception:
        return []


def get_summary() -> Dict:
    """获取情感分析汇总"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats/summary", timeout=10)
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception:
        return {}


def analyze_text(title: str, content: str) -> Dict:
    """分析文本情感"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            json={"title": title, "content": content},
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()
        return {}
    except Exception as e:
        st.error(f"分析失败: {e}")
        return {}


def render_header():
    """渲染页面标题"""
    st.markdown('<div class="main-header">📊 设计舆情分析工具</div>', unsafe_allow_html=True)
    st.markdown("---")


def render_sidebar():
    """渲染侧边栏"""
    st.sidebar.title("功能导航")

    page = st.sidebar.radio(
        "选择功能",
        ["数据爬取", "情感分析", "数据查看", "统计分析"],
        label_visibility="collapsed",
    )

    return page


def render_scrape_page():
    """渲染爬取页面"""
    st.header("🕷️ 数据爬取")

    col1, col2 = st.columns([3, 1])

    with col1:
        url_input = st.text_area(
            "输入小红书帖子 URL（每行一个）",
            placeholder="https://www.xiaohongshu.com/explore/xxx",
            height=150,
        )

    with col2:
        analyze = st.checkbox("同时进行情感分析", value=True)
        st.write("")
        st.write("")

    urls = [url.strip() for url in url_input.split('\n') if url.strip()]
    url_count = len(urls)

    st.write(f"共 {url_count} 个 URL 待爬取")

    if st.button("开始爬取", type="primary", disabled=url_count == 0):
        if url_count == 1:
            result = scrape_posts(urls, analyze)
            if result:
                st.session_state.current_task_id = result.get('task_id')
                st.success("爬取任务已提交！")
        else:
            result = scrape_posts(urls, analyze)
            if result:
                st.session_state.current_task_id = result.get('task_id')
                st.success(f"批量爬取任务已提交，共 {url_count} 个帖子！")

    # 显示任务状态
    if st.session_state.current_task_id:
        st.write("---")
        st.subheader("任务状态")

        status = check_task_status(st.session_state.current_task_id)
        if status:
            status_badge = {
                'pending': '⏳ 等待中',
                'running': '🔄 进行中',
                'completed': '✅ 已完成',
                'failed': '❌ 失败',
            }.get(status['status'], status['status'])

            st.write(f"**状态**: {status_badge}")
            st.write(f"**总数**: {status.get('total', 0)}")
            st.write(f"**已完成**: {status.get('completed', 0)}")
            st.write(f"**失败**: {status.get('failed', 0)}")

            if status['status'] == 'completed':
                st.session_state.posts = status.get('result', {}).get('results', [])
                st.success("所有帖子爬取完成！")

            if status.get('error_message'):
                st.error(f"错误: {status['error_message']}")

            if st.button("刷新状态"):
                st.rerun()
        else:
            st.warning("无法获取任务状态")


def render_analyze_page():
    """渲染分析页面"""
    st.header("🔍 情感分析")

    col1, col2 = st.columns(2)

    with col1:
        title_input = st.text_input("标题（可选）", placeholder="输入帖子标题")

    with col2:
        st.write("")

    content_input = st.text_area(
        "内容",
        placeholder="输入需要分析的内容...",
        height=200,
    )

    if st.button("进行分析", type="primary", disabled=not content_input.strip()):
        with st.spinner("分析中..."):
            result = analyze_text(title_input, content_input)

            if result:
                st.success("分析完成!")

                # 显示主要结果
                st.subheader("分析结果")

                col1, col2, col3 = st.columns(3)

                label_map = {
                    'positive': '😊 积极',
                    'negative': '😞 消极',
                    'neutral': '😐 中性',
                }

                with col1:
                    st.metric(
                        "情感倾向",
                        label_map.get(result['label'], result['label']),
                        f"{result['score']:.2%}",
                    )

                with col2:
                    st.metric("置信度", f"{result['confidence']:.2%}")

                with col3:
                    st.metric("情感强度", f"{result['score']:.2f}")

                # 显示情感细分
                st.subheader("情感细分")

                emotions = result.get('emotions', {})

                if emotions:
                    emotion_names = {
                        'happy': '😊 开心',
                        'sad': '😢 难过',
                        'angry': '😠 生气',
                        'fear': '😨 恐惧',
                        'surprise': '😮 惊讶',
                        'neutral': '😐 中性',
                    }

                    emotion_df = pd.DataFrame([
                        {'emotion': emotion_names.get(k, k), 'value': v}
                        for k, v in emotions.items()
                    ]).sort_values('value', ascending=False)

                    fig = px.bar(
                        emotion_df,
                        x='emotion',
                        y='value',
                        title='情感分布',
                        color='value',
                        color_continuous_scale='RdYlGn',
                    )
                    fig.update_layout(
                        xaxis_title="情感",
                        yaxis_title="强度",
                        height=400,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("暂无情感细分数据")


def render_posts_page():
    """渲染帖子列表页面"""
    st.header("📋 数据查看")

    # 加载帖子数据
    posts = get_posts(limit=200)

    if not posts:
        st.info("暂无数据，请先爬取帖子。")
        return

    st.write(f"共 {len(posts)} 条数据")

    # 搜索过滤
    search_term = st.text_input("搜索", placeholder="搜索标题或作者...")

    # 情感过滤
    sentiment_filter = st.selectbox(
        "情感过滤",
        ["全部", "积极", "消极", "中性"],
    )

    # 应用过滤
    filtered_posts = posts

    if search_term:
        filtered_posts = [
            p for p in filtered_posts
            if search_term.lower() in p.get('title', '').lower()
            or search_term.lower() in p.get('author', '').lower()
        ]

    if sentiment_filter != "全部":
        sentiment_map = {"积极": "positive", "消极": "negative", "中性": "neutral"}
        filtered_posts = [
            p for p in filtered_posts
            if p.get('sentiment', {}).get('label') == sentiment_map[sentiment_filter]
        ]

    st.write(f"筛选后: {len(filtered_posts)} 条数据")

    # 显示帖子列表
    for i, post in enumerate(filtered_posts):
        with st.expander(f"{post.get('title', '无标题')} - {post.get('author', '未知')}", expanded=(i == 0)):
            # 基本信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**作者**: {post.get('author', '未知')}")
            with col2:
                st.write(f"**发布时间**: {post.get('published_time', '未知')}")
            with col3:
                st.write(f"[查看原文]({post.get('url', '#')})")

            # 数据统计
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            with stats_col1:
                st.metric("点赞", post.get('likes', 0))
            with stats_col2:
                st.metric("收藏", post.get('collects', 0))
            with stats_col3:
                st.metric("评论", post.get('comments', 0))
            with stats_col4:
                st.metric("分享", post.get('shares', 0))

            # 内容
            st.write("**内容**:")
            st.write(post.get('content', '无内容'))

            # 情感分析
            sentiment = post.get('sentiment', {})
            if sentiment:
                st.write("---")
                label_map = {
                    'positive': '😊 积极',
                    'negative': '😞 消极',
                    'neutral': '😐 中性',
                }
                st.write(f"**情感倾向**: {label_map.get(sentiment['label'], sentiment['label'])}")
                st.write(f"**分数**: {sentiment['score']:.3f}")
                st.write(f"**置信度**: {sentiment['confidence']:.3f}")

                emotions = sentiment.get('emotions', {})
                if emotions:
                    emotion_names = {
                        'happy': '开心',
                        'sad': '难过',
                        'angry': '生气',
                        'fear': '恐惧',
                        'surprise': '惊讶',
                        'neutral': '中性',
                    }
                    st.write("**情感细分**:")
                    for key, value in sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:3]:
                        st.write(f"- {emotion_names.get(key, key)}: {value:.3f}")


def render_stats_page():
    """渲染统计页面"""
    st.header("📈 统计分析")

    # 加载数据
    summary = get_summary()

    if not summary or summary.get('total', 0) == 0:
        st.info("暂无数据，请先爬取和分析帖子。")
        return

    # 顶部指标
    st.subheader("整体概况")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总帖数", summary['total'])

    with col2:
        avg_confidence = summary.get('avg_confidence', 0)
        st.metric("平均置信度", f"{avg_confidence:.2%}")

    with col3:
        positive_ratio = summary.get('positive_ratio', 0)
        st.metric("积极比例", f"{positive_ratio:.1%}")

    with col4:
        negative_ratio = summary.get('negative_ratio', 0)
        st.metric("消极比例", f"{negative_ratio:.1%}")

    # 情感趋势
    st.write("---")
    st.subheader("情感分布")

    sentiment_data = {
        '积极': summary.get('positive', 0),
        '消极': summary.get('negative', 0),
        '中性': summary.get('neutral', 0),
    }

    col1, col2 = st.columns([1, 1])

    with col1:
        # 饼图
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(sentiment_data.keys()),
            values=list(sentiment_data.values()),
            marker=dict(colors=['#4CAF50', '#F44336', '#9E9E9E']),
            textinfo='label+percent',
        )])
        fig_pie.update_layout(
            title="情感比例分布",
            height=400,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # 柱状图
        fig_bar = px.bar(
            x=list(sentiment_data.keys()),
            y=list(sentiment_data.values()),
            title="情感数量统计",
            color=list(sentiment_data.keys()),
            color_discrete_map={
                '积极': '#4CAF50',
                '消极': '#F44336',
                '中性': '#9E9E9E',
            },
        )
        fig_bar.update_layout(
            xaxis_title="情感",
            yaxis_title="数量",
            height=400,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # 情感细分
    st.write("---")
    st.subheader("情感细分")

    emotions = summary.get('emotions', {})

    if emotions:
        emotion_names = ['happy', 'sad', 'angry', 'fear', 'surprise', 'neutral']
        emotion_chinese = {
            'happy': '😊 开心',
            'sad': '😢 难过',
            'angry': '😠 生气',
            'fear': '😨 恐惧',
            'surprise': '😮 惊讶',
            'neutral': '😐 中性',
        }

        emotion_df = pd.DataFrame([
            {
                'emotion': emotion_chinese.get(k, k),
                'value': v,
                'name': k,
            }
            for k in emotion_names
            if k in emotions
        ]).sort_values('value', ascending=False)

        fig_emotion = px.bar(
            emotion_df,
            x='emotion',
            y='value',
            title="情感细分强度分布",
            color='value',
            color_continuous_scale='RdYlGn',
        )
        fig_emotion.update_layout(
            xaxis_title="情感类型",
            yaxis_title="强度",
            height=400,
        )
        st.plotly_chart(fig_emotion, use_container_width=True)

    # 导出数据
    st.write("---")
    st.subheader("数据导出")

    posts = get_posts(limit=1000)

    if posts:
        export_data = []
        for post in posts:
            sentiment = post.get('sentiment', {})
            export_data.append({
                'ID': post.get('id'),
                '帖子ID': post.get('post_id'),
                '标题': post.get('title'),
                '作者': post.get('author'),
                '内容': post.get('content'),
                '点赞数': post.get('likes'),
                '收藏数': post.get('collects'),
                '评论数': post.get('comments'),
                '分享数': post.get('shares'),
                'URL': post.get('url'),
                '情感标签': sentiment.get('label') if sentiment else '',
                '情感分数': sentiment.get('score') if sentiment else '',
                '置信度': sentiment.get('confidence') if sentiment else '',
            })

        df = pd.DataFrame(export_data)

        csv = df.to_csv(index=False, encoding='utf-8-sig')

        st.download_button(
            label="导出 CSV",
            data=csv,
            file_name=f"xhs_sentiment_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )


def main():
    """主函数"""
    render_header()

    init_session_state()

    page = render_sidebar()

    if page == "数据爬取":
        render_scrape_page()
    elif page == "情感分析":
        render_analyze_page()
    elif page == "数据查看":
        render_posts_page()
    elif page == "统计分析":
        render_stats_page()


if __name__ == "__main__":
    main()

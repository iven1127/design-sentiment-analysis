"""CLI 入口模块"""
import argparse
import sys
from pathlib import Path

from core.config import get_config
from core.logger import setup_logger
from core.models import get_db_manager, init_database

logger = setup_logger("xhs_cli")


def cmd_init(args):
    """初始化数据库"""
    logger.info("初始化数据库...")
    db_url = args.database_url if hasattr(args, 'database_url') else None
    manager = init_database(db_url)
    logger.info("数据库初始化完成")
    return 0


def cmd_api(args):
    """启动 API 服务"""
    import uvicorn

    config = get_config()
    logger.info(f"启动 API 服务: {config.api.host}:{config.api.port}")

    uvicorn.run(
        "api.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload,
        log_level=config.api.log_level,
    )
    return 0


def cmd_web(args):
    """启动 Web 界面"""
    import subprocess

    config = get_config()
    logger.info(f"启动 Web 界面: localhost:{config.api.port}")

    # 启动 API 服务（后台）
    logger.info("启动 API 服务...")
    api_process = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "api.main:app",
            "--host", str(config.api.host),
            "--port", str(config.api.port),
            "--log-level", config.api.log_level,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # 启动 Streamlit
    logger.info("启动 Streamlit...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "web/app.py",
            "--server.port", str(config.web.port),
            "--theme.base", config.web.theme,
        ])
    except KeyboardInterrupt:
        logger.info("停止服务...")
    finally:
        api_process.terminate()
        api_process.wait()
        logger.info("服务已停止")

    return 0


def cmd_scrape(args):
    """爬取帖子"""
    import asyncio

    from core.crawler import XHSCrawler, scrape_posts
    from core.sentiment import SentimentAnalyzer
    from core.models import Post, SentimentResultDB
    from core.config import get_config

    config = get_config()

    async def run_scrape():
        urls = [url.strip() for url in args.urls.split(',')]

        # 初始化分析器
        analyzer = None
        if args.analyze:
            logger.info("初始化情感分析器...")
            analyzer = SentimentAnalyzer(
                model_name=config.sentiment.model_name,
                device=config.sentiment.device,
            )

        # 爬取
        logger.info(f"开始爬取 {len(urls)} 个帖子...")
        posts = await scrape_posts(urls, headless=args.no_headless)

        # 保存到数据库
        db_manager = get_db_manager()
        session = db_manager.get_session()

        try:
            for post in posts:
                # 检查是否已存在
                db_post = session.query(Post).filter(Post.post_id == post.post_id).first()
                if db_post:
                    continue

                # 创建新记录
                db_post = Post(
                    post_id=post.post_id,
                    title=post.title,
                    content=post.content,
                    author=post.author,
                    author_id=post.author_id,
                    likes=post.likes,
                    collects=post.collects,
                    comments=post.comments,
                    shares=post.shares,
                    url=post.url,
                    images=post.images,
                    tags=post.tags,
                    published_time=post.published_time,
                )
                session.add(db_post)
                session.flush()

                # 情感分析
                if analyzer:
                    result = analyzer.analyze_title_content(post.title, post.content)

                    db_sentiment = SentimentResultDB(
                        post_id=db_post.id,
                        label=result.label.value,
                        score=result.score,
                        confidence=result.confidence,
                        emotion_happy=result.emotions.get('happy', 0),
                        emotion_sad=result.emotions.get('sad', 0),
                        emotion_angry=result.emotions.get('angry', 0),
                        emotion_fear=result.emotions.get('fear', 0),
                        emotion_surprise=result.emotions.get('surprise', 0),
                        emotion_neutral=result.emotions.get('neutral', 0),
                        model_name=config.sentiment.model_name,
                    )
                    session.add(db_sentiment)

                session.commit()
                logger.info(f"已保存: {post.title[:50]}...")

            logger.info(f"成功处理 {len(posts)} 个帖子")

        except Exception as e:
            session.rollback()
            logger.error(f"保存失败: {e}")
            return 1
        finally:
            session.close()

        return 0

    return asyncio.run(run_scrape())


def cmd_analyze(args):
    """分析文本情感"""
    from core.sentiment import SentimentAnalyzer
    from core.config import get_config

    config = get_config()

    logger.info("初始化情感分析器...")
    analyzer = SentimentAnalyzer(
        model_name=config.sentiment.model_name,
        device=config.sentiment.device,
    )

    # 读取文本
    if args.file:
        text = Path(args.file).read_text(encoding='utf-8')
    elif args.text:
        text = args.text
    else:
        logger.error("请提供 --text 或 --file 参数")
        return 1

    # 分析
    result = analyzer.analyze_text(text)

    # 输出结果
    print("\n" + "="*50)
    print("情感分析结果")
    print("="*50)
    print(f"情感倾向: {result.label.value}")
    print(f"置信度: {result.confidence:.3f}")
    print(f"分数: {result.score:.3f}")
    print("\n情感细分:")
    for name, score in sorted(result.emotions.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {score:.3f}")
    print("="*50)

    return 0


def cmd_stats(args):
    """显示统计信息"""
    from core.models import Post, SentimentResultDB
    from sqlalchemy import func

    db_manager = get_db_manager()
    session = db_manager.get_session()

    try:
        # 总帖子数
        total_posts = session.query(Post).count()
        print(f"\n总帖子数: {total_posts}")

        if total_posts == 0:
            print("暂无数据")
            return 0

        # 已分析的帖子数
        analyzed_posts = session.query(SentimentResultDB).count()
        print(f"已分析帖子数: {analyzed_posts}")

        # 情感统计
        query = session.query(
            SentimentResultDB.label,
            func.count(SentimentResultDB.id),
            func.avg(SentimentResultDB.score).label('avg_score'),
            func.avg(SentimentResultDB.confidence).label('avg_confidence'),
        ).group_by(SentimentResultDB.label)

        print("\n情感分布:")
        total_emotions = 0
        for label, count, avg_score, avg_confidence in query:
            total_emotions += count
            print(f"  {label}: {count} (平均分数: {avg_score:.3f}, 平均置信度: {avg_confidence:.3f})")

        if total_emotions > 0:
            print(f"\n比例分布:")
            for label, count, avg_score, avg_confidence in query:
                ratio = count / total_emotions * 100
                print(f"  {label}: {ratio:.1f}%")

        return 0

    except Exception as e:
        logger.error(f"查询失败: {e}")
        return 1
    finally:
        session.close()


def cmd_clean(args):
    """清理数据"""
    from core.models import Post, SentimentResultDB, Task

    db_manager = get_db_manager()
    session = db_manager.get_session()

    try:
        if args.all:
            # 清空所有数据
            session.query(SentimentResultDB).delete()
            session.query(Post).delete()
            session.query(Task).delete()
            session.commit()
            logger.info("已清空所有数据")
        elif args.posts:
            # 清空帖子数据
            session.query(SentimentResultDB).delete()
            session.query(Post).delete()
            session.commit()
            logger.info("已清空帖子数据")
        elif args.tasks:
            # 清空任务数据
            session.query(Task).delete()
            session.commit()
            logger.info("已清空任务数据")

        return 0

    except Exception as e:
        session.rollback()
        logger.error(f"清理失败: {e}")
        return 1
    finally:
        session.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="设计舆情分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s init                    初始化数据库
  %(prog)s api                      启动 API 服务
  %(prog)s web                      启动 Web 界面
  %(prog)s scrape "url1,url2"       爬取帖子
  %(prog)s scrape "url1" --analyze  爬取并分析
  %(prog)s analyze --text "内容"    分析文本
  %(prog)s stats                    显示统计
  %(prog)s clean --all              清理所有数据
        """,
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # init 命令
    init_parser = subparsers.add_parser('init', help='初始化数据库')
    init_parser.set_defaults(func=cmd_init)

    # api 命令
    api_parser = subparsers.add_parser('api', help='启动 API 服务')
    api_parser.set_defaults(func=cmd_api)

    # web 命令
    web_parser = subparsers.add_parser('web', help='启动 Web 界面')
    web_parser.set_defaults(func=cmd_web)

    # scrape 命令
    scrape_parser = subparsers.add_parser('scrape', help='爬取帖子')
    scrape_parser.add_argument('urls', help='帖子URL（多个用逗号分隔）')
    scrape_parser.add_argument('--analyze', action='store_true', help='同时进行情感分析')
    scrape_parser.add_argument('--no-headless', action='store_true', help='显示浏览器窗口')
    scrape_parser.set_defaults(func=cmd_scrape)

    # analyze 命令
    analyze_parser = subparsers.add_parser('analyze', help='分析文本情感')
    analyze_parser.add_argument('--text', help='直接输入文本')
    analyze_parser.add_argument('--file', help='从文件读取文本')
    analyze_parser.set_defaults(func=cmd_analyze)

    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    stats_parser.set_defaults(func=cmd_stats)

    # clean 命令
    clean_parser = subparsers.add_parser('clean', help='清理数据')
    clean_group = clean_parser.add_mutually_exclusive_group(required=True)
    clean_group.add_argument('--all', action='store_true', help='清空所有数据')
    clean_group.add_argument('--posts', action='store_true', help='清空帖子数据')
    clean_group.add_argument('--tasks', action='store_true', help='清空任务数据')
    clean_parser.set_defaults(func=cmd_clean)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())

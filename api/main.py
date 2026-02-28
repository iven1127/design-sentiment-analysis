"""FastAPI 主应用"""
import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.models import Post, SentimentResultDB, Task, get_db_manager
from core.sentiment import SentimentAnalyzer, SentimentLabel, SentimentResult
from core.crawler import XHSCrawler, XHSPost
from core.exceptions import CrawlerError, AuthError, RateLimitError, AnalysisError
from core.logger import setup_logger

logger = setup_logger("xhs_api")

# 全局变量
analyzer: Optional[SentimentAnalyzer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    global analyzer
    logger.info("初始化情感分析器...")
    try:
        analyzer = SentimentAnalyzer()
        logger.info("情感分析器初始化成功")
    except Exception as e:
        logger.warning(f"情感分析器初始化失败: {e}")

    yield

    # 关闭时清理
    logger.info("应用关闭")


app = FastAPI(
    title="小红书情感分析 API",
    description="小红书内容爬取与情感分析服务",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 数据库依赖
def get_db():
    """获取数据库会话"""
    db_manager = get_db_manager()
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


# Pydantic 模型
class ScrapeRequest(BaseModel):
    """爬取请求"""
    url: str = Field(..., description="帖子URL")
    analyze: bool = Field(True, description="是否进行情感分析")


class BatchScrapeRequest(BaseModel):
    """批量爬取请求"""
    urls: List[str] = Field(..., description="帖子URL列表")
    analyze: bool = Field(True, description="是否进行情感分析")


class SearchRequest(BaseModel):
    """搜索请求"""
    keyword: str = Field(..., description="搜索关键词")
    max_pages: int = Field(3, description="最大爬取页数")
    per_page: int = Field(20, description="每页结果数量")
    analyze: bool = Field(True, description="是否进行情感分析")


class AnalyzeRequest(BaseModel):
    """分析请求"""
    title: str = Field("", description="标题")
    content: str = Field(..., description="内容")


class AnalyzeBatchRequest(BaseModel):
    """批量分析请求"""
    texts: List[Dict[str, str]] = Field(..., description="文本列表，每项包含title和content")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    message: str


class PostResponse(BaseModel):
    """帖子响应"""
    id: int
    post_id: str
    title: str
    content: str
    author: str
    likes: int
    collects: int
    comments: int
    shares: int
    url: str
    images: List[str]
    tags: List[str]
    created_at: str
    sentiment: Optional[Dict[str, Any]] = None


class SentimentResponse(BaseModel):
    """情感分析响应"""
    label: str
    score: float
    confidence: float
    emotions: Dict[str, float]


class SummaryResponse(BaseModel):
    """汇总响应"""
    total: int
    positive: int
    negative: int
    neutral: int
    positive_ratio: float
    negative_ratio: float
    neutral_ratio: float
    avg_confidence: float
    emotions: Dict[str, float]


# 辅助函数
async def run_scraping_task(
    task_id: str,
    urls: List[str],
    analyze: bool,
    db: Session,
):
    """后台任务：爬取和分析"""
    db_manager = get_db_manager()
    session = db_manager.get_session()

    try:
        task = session.query(Task).filter(Task.task_id == task_id).first()
        if task:
            task.status = "running"
            task.started_at = datetime.utcnow()
            session.commit()

        async with XHSCrawler(headless=True) as crawler:
            posts = await crawler.scrape_multiple_posts(urls)

        task.total = len(posts)
        task.completed = 0
        task.failed = 0
        session.commit()

        results = []

        for post in posts:
            try:
                # 保存帖子到数据库
                db_post = session.query(Post).filter(Post.post_id == post.post_id).first()
                if db_post:
                    db_post.title = post.title
                    db_post.content = post.content
                    db_post.author = post.author
                    db_post.likes = post.likes
                    db_post.collects = post.collects
                    db_post.comments = post.comments
                    db_post.shares = post.shares
                    db_post.images = post.images
                    db_post.tags = post.tags
                    db_post.updated_at = datetime.utcnow()
                else:
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
                sentiment_result = None
                if analyze and analyzer:
                    try:
                        result = analyzer.analyze_title_content(post.title, post.content)

                        # 保存情感分析结果
                        db_sentiment = session.query(SentimentResultDB).filter(
                            SentimentResultDB.post_id == db_post.id
                        ).first()

                        if db_sentiment:
                            db_sentiment.label = result.label.value
                            db_sentiment.score = result.score
                            db_sentiment.confidence = result.confidence
                            db_sentiment.emotion_happy = result.emotions.get('happy', 0)
                            db_sentiment.emotion_sad = result.emotions.get('sad', 0)
                            db_sentiment.emotion_angry = result.emotions.get('angry', 0)
                            db_sentiment.emotion_fear = result.emotions.get('fear', 0)
                            db_sentiment.emotion_surprise = result.emotions.get('surprise', 0)
                            db_sentiment.emotion_neutral = result.emotions.get('neutral', 0)
                            db_sentiment.model_name = analyzer.model_name
                        else:
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
                                model_name=analyzer.model_name,
                            )
                            session.add(db_sentiment)

                        sentiment_result = {
                            'label': result.label.value,
                            'score': result.score,
                            'confidence': result.confidence,
                            'emotions': result.emotions,
                        }
                    except Exception as e:
                        logger.warning(f"情感分析失败: {e}")

                results.append({
                    'post_id': post.post_id,
                    'title': post.title,
                    'url': post.url,
                    'sentiment': sentiment_result,
                })

                task.completed += 1
                session.commit()

            except Exception as e:
                logger.error(f"处理帖子失败: {e}")
                task.failed += 1
                session.commit()

        if task:
            task.status = "completed"
            task.finished_at = datetime.utcnow()
            task.result = {
                'total': len(posts),
                'completed': task.completed,
                'failed': task.failed,
                'results': results,
            }
            session.commit()

    except Exception as e:
        logger.error(f"爬取任务失败: {e}")
        if task:
            task.status = "failed"
            task.error_message = str(e)
            task.finished_at = datetime.utcnow()
            session.commit()
    finally:
        session.close()


# API 端点
@app.get("/", tags=["系统"])
async def root():
    """根路径"""
    return {
        "name": "小红书情感分析 API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "analyzer_ready": analyzer is not None,
    }


@app.post("/api/v1/scrape", response_model=TaskResponse, tags=["爬取"])
async def scrape_post(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """爬取单个帖子"""
    task_id = str(uuid.uuid4())

    db_manager = get_db_manager()
    session = db_manager.get_session()

    try:
        task = Task(
            task_id=task_id,
            task_type="scrape_single",
            params={"url": request.url, "analyze": request.analyze},
        )
        session.add(task)
        session.commit()

        background_tasks.add_task(
            run_scraping_task,
            task_id,
            [request.url],
            request.analyze,
            session,
        )

        return TaskResponse(
            task_id=task_id,
            status="pending",
            message="爬取任务已提交",
        )

    finally:
        session.close()


@app.post("/api/v1/scrape/batch", response_model=TaskResponse, tags=["爬取"])
async def scrape_posts(request: BatchScrapeRequest, background_tasks: BackgroundTasks):
    """批量爬取帖子"""
    task_id = str(uuid.uuid4())

    db_manager = get_db_manager()
    session = db_manager.get_session()

    try:
        task = Task(
            task_id=task_id,
            task_type="scrape_batch",
            params={"urls": request.urls, "analyze": request.analyze},
        )
        session.add(task)
        session.commit()

        background_tasks.add_task(
            run_scraping_task,
            task_id,
            request.urls,
            request.analyze,
            session,
        )

        return TaskResponse(
            task_id=task_id,
            status="pending",
            message=f"批量爬取任务已提交，共 {len(request.urls)} 个帖子",
        )

    finally:
        session.close()


@app.get("/api/v1/task/{task_id}", tags=["任务"])
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """获取任务状态"""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "task_id": task.task_id,
        "task_type": task.task_type,
        "status": task.status,
        "total": task.total,
        "completed": task.completed,
        "failed": task.failed,
        "result": task.result,
        "error_message": task.error_message,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "finished_at": task.finished_at.isoformat() if task.finished_at else None,
    }


@app.post("/api/v1/analyze", response_model=SentimentResponse, tags=["分析"])
async def analyze(request: AnalyzeRequest):
    """分析文本情感"""
    if not analyzer:
        raise HTTPException(status_code=503, detail="情感分析器未就绪")

    try:
        result = analyzer.analyze_title_content(request.title, request.content)
        return SentimentResponse(
            label=result.label.value,
            score=result.score,
            confidence=result.confidence,
            emotions=result.emotions,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/api/v1/analyze/batch", tags=["分析"])
async def analyze_batch(request: AnalyzeBatchRequest):
    """批量分析文本情感"""
    if not analyzer:
        raise HTTPException(status_code=503, detail="情感分析器未就绪")

    try:
        texts = [
            analyzer._merge_texts(item['title'], item['content'])
            for item in request.texts
        ]
        results = analyzer.analyze_batch(texts)

        return [
            {
                "label": r.label.value,
                "score": r.score,
                "confidence": r.confidence,
                "emotions": r.emotions,
            }
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量分析失败: {str(e)}")


@app.get("/api/v1/posts", tags=["数据"])
async def list_posts(
    skip: int = 0,
    limit: int = 20,
    sentiment_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取帖子列表"""
    query = db.query(Post)

    if sentiment_filter:
        query = query.join(SentimentResultDB).filter(
            SentimentResultDB.label == sentiment_filter
        )

    posts = query.offset(skip).limit(limit).all()

    results = []
    for post in posts:
        result = post.to_dict()
        if post.sentiment:
            result['sentiment'] = post.sentiment.to_dict()
        results.append(result)

    return {
        "total": len(results),
        "posts": results,
    }


@app.get("/api/v1/posts/{post_id}", tags=["数据"])
async def get_post(post_id: str, db: Session = Depends(get_db)):
    """获取帖子详情"""
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    result = post.to_dict()
    if post.sentiment:
        result['sentiment'] = post.sentiment.to_dict()

    return result


@app.get("/api/v1/stats/summary", response_model=SummaryResponse, tags=["统计"])
async def get_summary(db: Session = Depends(get_db)):
    """获取情感分析汇总"""
    posts = db.query(Post).join(SentimentResultDB).all()

    if not posts:
        return SummaryResponse(
            total=0,
            positive=0,
            negative=0,
            neutral=0,
            positive_ratio=0.0,
            negative_ratio=0.0,
            neutral_ratio=0.0,
            avg_confidence=0.0,
            emotions={},
        )

    total = len(posts)
    positive = sum(1 for p in posts if p.sentiment and p.sentiment.label == 'positive')
    negative = sum(1 for p in posts if p.sentiment and p.sentiment.label == 'negative')
    neutral = total - positive - negative

    avg_confidence = sum(
        p.sentiment.confidence for p in posts if p.sentiment
    ) / sum(1 for p in posts if p.sentiment)

    emotions = {
        'happy': sum(p.sentiment.emotion_happy or 0 for p in posts if p.sentiment),
        'sad': sum(p.sentiment.emotion_sad or 0 for p in posts if p.sentiment),
        'angry': sum(p.sentiment.emotion_angry or 0 for p in posts if p.sentiment),
        'fear': sum(p.sentiment.emotion_fear or 0 for p in posts if p.sentiment),
        'surprise': sum(p.sentiment.emotion_surprise or 0 for p in posts if p.sentiment),
        'neutral': sum(p.sentiment.emotion_neutral or 0 for p in posts if p.sentiment),
    }

    return SummaryResponse(
        total=total,
        positive=positive,
        negative=negative,
        neutral=neutral,
        positive_ratio=positive / total,
        negative_ratio=negative / total,
        neutral_ratio=neutral / total,
        avg_confidence=avg_confidence,
        emotions=emotions,
    )


@app.delete("/api/v1/posts", tags=["数据"])
async def delete_all_posts(db: Session = Depends(get_db)):
    """删除所有帖子"""
    try:
        db.query(SentimentResultDB).delete()
        db.query(Post).delete()
        db.commit()
        return {"message": "所有帖子已删除"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

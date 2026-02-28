"""数据库模型"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    Boolean,
    JSON,
    Index,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Post(Base):
    """帖子数据库模型"""
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False, default='')
    content = Column(Text, nullable=False, default='')
    author = Column(String(100), nullable=False, default='')
    author_id = Column(String(64), nullable=True)
    likes = Column(Integer, nullable=False, default=0)
    collects = Column(Integer, nullable=False, default=0)
    comments = Column(Integer, nullable=False, default=0)
    shares = Column(Integer, nullable=False, default=0)
    url = Column(String(500), nullable=False, unique=True)
    images = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    published_time = Column(String(100), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 与情感分析结果的关系
    sentiment = relationship("SentimentResult", back_populates="post", uselist=False, cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index('idx_author', 'author'),
        Index('idx_created_at', 'created_at'),
        Index('idx_likes', 'likes'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'author_id': self.author_id,
            'likes': self.likes,
            'collects': self.collects,
            'comments': self.comments,
            'shares': self.shares,
            'url': self.url,
            'images': self.images,
            'tags': self.tags,
            'published_time': self.published_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
        }


class SentimentResultDB(Base):
    """情感分析结果数据库模型"""
    __tablename__ = 'sentiment_results'

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), nullable=False, unique=True)

    # 情感标签
    label = Column(String(20), nullable=False, index=True)

    # 分数
    score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)

    # 情感细分
    emotion_happy = Column(Float, default=0.0)
    emotion_sad = Column(Float, default=0.0)
    emotion_angry = Column(Float, default=0.0)
    emotion_fear = Column(Float, default=0.0)
    emotion_surprise = Column(Float, default=0.0)
    emotion_neutral = Column(Float, default=0.0)

    # 元数据
    model_name = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 关系
    post = relationship("Post", back_populates="sentiment")

    # 索引
    __table_args__ = (
        Index('idx_label', 'label'),
        Index('idx_created_at', 'created_at'),
        Index('idx_score', 'score'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'label': self.label,
            'score': self.score,
            'confidence': self.confidence,
            'emotions': {
                'happy': self.emotion_happy,
                'sad': self.emotion_sad,
                'angry': self.emotion_angry,
                'fear': self.emotion_fear,
                'surprise': self.emotion_surprise,
                'neutral': self.emotion_neutral,
            },
            'model_name': self.model_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Task(Base):
    """任务数据库模型"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True, nullable=False, index=True)

    # 任务类型
    task_type = Column(String(50), nullable=False, index=True)

    # 任务状态
    status = Column(String(20), nullable=False, default='pending', index=True)

    # 任务参数
    params = Column(JSON, nullable=True)

    # 任务结果
    result = Column(JSON, nullable=True)

    # 错误信息
    error_message = Column(Text, nullable=True)

    # 进度
    total = Column(Integer, default=0)
    completed = Column(Integer, default=0)
    failed = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # 索引
    __table_args__ = (
        Index('idx_task_type_status', 'task_type', 'status'),
        Index('idx_created_at', 'created_at'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_type': self.task_type,
            'status': self.status,
            'params': self.params,
            'result': self.result,
            'error_message': self.error_message,
            'total': self.total,
            'completed': self.completed,
            'failed': self.failed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
        }


class Comment(Base):
    """评论数据库模型"""
    __tablename__ = 'comments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(String(64), unique=True, nullable=False, index=True)
    post_id = Column(String(64), nullable=False, index=True)

    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=True)
    author_id = Column(String(64), nullable=True)
    likes = Column(Integer, default=0)

    # 情感分析
    sentiment_label = Column(String(20), nullable=True)
    sentiment_score = Column(Float, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index('idx_post_id', 'post_id'),
        Index('idx_sentiment', 'sentiment_label'),
        Index('idx_created_at', 'created_at'),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'comment_id': self.comment_id,
            'post_id': self.post_id,
            'content': self.content,
            'author': self.author,
            'author_id': self.author_id,
            'likes': self.likes,
            'sentiment_label': self.sentiment_label,
            'sentiment_score': self.sentiment_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
        }


# 数据库管理类
class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url: str = "sqlite:///xhs_sentiment.db"):
        """初始化数据库管理器

        Args:
            database_url: 数据库连接URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """删除所有表"""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    def init_db(self):
        """初始化数据库"""
        self.create_tables()


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(database_url: Optional[str] = None) -> DatabaseManager:
    """获取数据库管理器实例

    Args:
        database_url: 数据库连接URL，如果为None则使用默认值

    Returns:
        DatabaseManager实例
    """
    global _db_manager
    if _db_manager is None:
        url = database_url or "sqlite:///xhs_sentiment.db"
        _db_manager = DatabaseManager(url)
        _db_manager.init_db()
    return _db_manager


def init_database(database_url: str = "sqlite:///xhs_sentiment.db"):
    """初始化数据库

    Args:
        database_url: 数据库连接URL
    """
    manager = DatabaseManager(database_url)
    manager.init_db()
    return manager

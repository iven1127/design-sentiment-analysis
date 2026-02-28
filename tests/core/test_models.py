"""测试数据库模型"""
import pytest
from datetime import datetime
from tempfile import NamedTemporaryFile
import os

from core.models import (
    Post,
    SentimentResultDB,
    Task,
    Comment,
    DatabaseManager,
    get_db_manager,
    init_database,
)


class TestPostModel:
    """测试帖子模型"""

    def test_to_dict(self):
        """测试转换为字典"""
        post = Post(
            id=1,
            post_id="test123",
            title="测试标题",
            content="测试内容",
            author="测试作者",
            author_id="author123",
            likes=100,
            collects=50,
            comments=20,
            shares=10,
            url="https://example.com",
            images=["img1.jpg", "img2.jpg"],
            tags=["#test", "#demo"],
            published_time="2024-01-01",
        )

        post.created_at = datetime.utcnow()
        post.updated_at = datetime.utcnow()
        post.scraped_at = datetime.utcnow()

        data = post.to_dict()
        assert data["id"] == 1
        assert data["post_id"] == "test123"
        assert data["title"] == "测试标题"
        assert data["content"] == "测试内容"
        assert data["author"] == "测试作者"
        assert data["likes"] == 100
        assert data["collects"] == 50
        assert data["images"] == ["img1.jpg", "img2.jpg"]
        assert data["tags"] == ["#test", "#demo"]


class TestSentimentResultDBModel:
    """测试情感分析结果模型"""

    def test_to_dict(self):
        """测试转换为字典"""
        result = SentimentResultDB(
            id=1,
            post_id=1,
            label="positive",
            score=0.85,
            confidence=0.9,
            emotion_happy=0.7,
            emotion_sad=0.1,
            emotion_angry=0.05,
            emotion_fear=0.05,
            emotion_surprise=0.05,
            emotion_neutral=0.05,
            model_name="test_model",
            created_at=datetime.utcnow(),
        )

        data = result.to_dict()
        assert data["id"] == 1
        assert data["label"] == "positive"
        assert data["score"] == 0.85
        assert data["confidence"] == 0.9
        assert data["emotions"]["happy"] == 0.7


class TestTaskModel:
    """测试任务模型"""

    def test_to_dict(self):
        """测试转换为字典"""
        task = Task(
            id=1,
            task_id="task123",
            task_type="scrape",
            status="running",
            params={"url": "test"},
            result={"status": "success"},
            total=100,
            completed=50,
            failed=0,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            finished_at=None,
        )

        data = task.to_dict()
        assert data["id"] == 1
        assert data["task_id"] == "task123"
        assert data["task_type"] == "scrape"
        assert data["status"] == "running"
        assert data["total"] == 100
        assert data["completed"] == 50


class TestCommentModel:
    """测试评论模型"""

    def test_to_dict(self):
        """测试转换为字典"""
        comment = Comment(
            id=1,
            comment_id="comment123",
            post_id="post123",
            content="测试评论",
            author="评论者",
            author_id="author123",
            likes=10,
            sentiment_label="positive",
            sentiment_score=0.8,
            created_at=datetime.utcnow(),
            scraped_at=datetime.utcnow(),
        )

        data = comment.to_dict()
        assert data["id"] == 1
        assert data["comment_id"] == "comment123"
        assert data["post_id"] == "post123"
        assert data["content"] == "测试评论"
        assert data["author"] == "评论者"
        assert data["likes"] == 10
        assert data["sentiment_label"] == "positive"


class TestDatabaseManager:
    """测试数据库管理器"""

    def test_create_and_drop_tables(self):
        """测试创建和删除表"""
        with NamedTemporaryFile(delete=False, suffix=".db") as f:
            db_path = f"sqlite:///{f.name}"

        try:
            manager = DatabaseManager(db_path)
            manager.create_tables()
            tables = manager.engine.table_names()
            assert len(tables) > 0
            manager.drop_tables()
            tables = manager.engine.table_names()
            assert len(tables) == 0
        finally:
            db_file = db_path.replace("sqlite:///", "")
            if os.path.exists(db_file):
                os.unlink(db_file)

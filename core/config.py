"""配置管理模块"""
import os
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class CrawlerConfig:
    """爬虫配置"""
    headless: bool = True
    max_retries: int = 3
    timeout: int = 30000
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    request_delay: float = 2.0


@dataclass
class SentimentConfig:
    """情感分析配置"""
    model_name: str = "uer/roberta-base-finetuned-dianping-chinese"
    emotion_model: str = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
    device: Optional[int] = None  # None for auto, 0 for GPU, -1 for CPU
    batch_size: int = 8
    max_length: int = 512


@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str = "sqlite:///xhs_sentiment.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


@dataclass
class APIConfig:
    """API配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 1
    log_level: str = "info"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class WebConfig:
    """Web界面配置"""
    title: str = "小红书情感分析工具"
    port: int = 8501
    theme: str = "light"
    cache_ttl: int = 3600


@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"
    log_dir: str = "logs"
    max_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class TaskConfig:
    """任务配置"""
    max_concurrent_tasks: int = 5
    task_timeout: int = 3600  # 1 hour
    cleanup_interval: int = 3600  # 1 hour
    max_retry: int = 3


class Config:
    """全局配置类"""

    crawler: CrawlerConfig = field(default_factory=CrawlerConfig)
    sentiment: SentimentConfig = field(default_factory=SentimentConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    web: WebConfig = field(default_factory=WebConfig)
    log: LogConfig = field(default_factory=LogConfig)
    task: TaskConfig = field(default_factory=TaskConfig)

    def __post_init__(self):
        """从环境变量加载配置"""
        # 数据库配置
        self.database.url = os.getenv("DATABASE_URL", self.database.url)
        self.database.echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"

        # API配置
        self.api.host = os.getenv("API_HOST", self.api.host)
        self.api.port = int(os.getenv("API_PORT", str(self.api.port)))
        self.api.reload = os.getenv("API_RELOAD", "false").lower() == "true"
        self.api.log_level = os.getenv("API_LOG_LEVEL", self.api.log_level)

        # Web配置
        self.web.port = int(os.getenv("WEB_PORT", str(self.web.port)))
        self.web.theme = os.getenv("WEB_THEME", self.web.theme)

        # 日志配置
        self.log.level = os.getenv("LOG_LEVEL", self.log.level)
        self.log.log_dir = os.getenv("LOG_DIR", self.log.log_dir)

        # 爬虫配置
        self.crawler.headless = os.getenv("CRAWLER_HEADLESS", "true").lower() == "true"
        self.crawler.max_retries = int(os.getenv("CRAWLER_MAX_RETRIES", str(self.crawler.max_retries)))

        # 情感分析配置
        self.sentiment.model_name = os.getenv("SENTIMENT_MODEL", self.sentiment.model_name)
        self.sentiment.batch_size = int(os.getenv("SENTIMENT_BATCH_SIZE", str(self.sentiment.batch_size)))

        # 任务配置
        self.task.max_concurrent_tasks = int(os.getenv("TASK_MAX_CONCURRENT", str(self.task.max_concurrent_tasks)))

        # 确保日志目录存在
        Path(self.log.log_dir).mkdir(parents=True, exist_ok=True)


def get_config() -> Config:
    """获取全局配置实例"""
    return _config


# 全局配置实例
_config = Config()

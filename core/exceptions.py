"""自定义异常类"""


class XHSSentimentAnalyzerError(Exception):
    """基础异常类"""
    pass


class CrawlerError(XHSSentimentAnalyzerError):
    """爬虫异常"""
    pass


class AuthError(XHSSentimentAnalyzerError):
    """认证异常"""
    pass


class RateLimitError(XHSSentimentAnalyzerError):
    """频率限制异常"""
    pass


class AnalysisError(XHSSentimentAnalyzerError):
    """分析异常"""
    pass


class DatabaseError(XHSSentimentAnalyzerError):
    """数据库异常"""
    pass


class TaskError(XHSSentimentAnalyzerError):
    """任务异常"""
    pass
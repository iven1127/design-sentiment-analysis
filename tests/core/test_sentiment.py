"""测试情感分析模块"""
import pytest
from core.sentiment import (
    SentimentAnalyzer,
    SentimentLabel,
    SentimentResult,
    create_analyzer,
)


class TestSentimentLabel:
    """测试情感标签枚举"""

    def test_label_values(self):
        """测试标签值"""
        assert SentimentLabel.POSITIVE.value == "positive"
        assert SentimentLabel.NEGATIVE.value == "negative"
        assert SentimentLabel.NEUTRAL.value == "neutral"


class TestSentimentResult:
    """测试情感结果数据类"""

    def test_creation(self):
        """测试创建"""
        result = SentimentResult(
            label=SentimentLabel.POSITIVE,
            score=0.85,
            confidence=0.9,
            emotions={"happy": 0.7, "sad": 0.1},
        )
        assert result.label == SentimentLabel.POSITIVE
        assert result.score == 0.85
        assert result.confidence == 0.9
        assert result.emotions == {"happy": 0.7, "sad": 0.1}


@pytest.mark.skipif(
    True,
    reason="需要下载模型，跳过集成测试"
)
class TestSentimentAnalyzer:
    """测试情感分析器"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        # 使用小模型进行测试
        return SentimentAnalyzer(
            model_name="uer/roberta-base-finetuned-dianping-chinese",
            device=-1,  # 使用CPU
            batch_size=2,
        )

    def test_analyze_positive_text(self, analyzer):
        """测试分析积极文本"""
        result = analyzer.analyze_text("这个产品真的很好用，强烈推荐给大家！")
        assert isinstance(result, SentimentResult)
        assert isinstance(result.label, SentimentLabel)
        assert 0 <= result.score <= 1

    def test_analyze_negative_text(self, analyzer):
        """测试分析消极文本"""
        result = analyzer.analyze_text("太糟糕了，完全浪费钱，不推荐购买")
        assert isinstance(result, SentimentResult)
        assert isinstance(result.label, SentimentLabel)

    def test_analyze_title_content(self, analyzer):
        """测试分析标题和内容"""
        result = analyzer.analyze_title_content(
            title="超级好用的护肤品推荐",
            content="用了真的很好，皮肤变好了",
        )
        assert isinstance(result, SentimentResult)

    def test_analyze_empty_text(self, analyzer):
        """测试分析空文本"""
        with pytest.raises(Exception):  # 应该抛出异常
            analyzer.analyze_text("")

    def test_analyze_batch(self, analyzer):
        """测试批量分析"""
        texts = [
            "很好用，推荐",
            "一般般吧",
            "太差了，不推荐",
        ]
        results = analyzer.analyze_batch(texts)
        assert len(results) == 3
        assert all(isinstance(r, SentimentResult) for r in results)

    def test_summarize_results(self, analyzer):
        """测试结果汇总"""
        results = [
            SentimentResult(
                label=SentimentLabel.POSITIVE,
                score=0.8,
                confidence=0.9,
                emotions={"happy": 0.7},
            ),
            SentimentResult(
                label=SentimentLabel.POSITIVE,
                score=0.7,
                confidence=0.85,
                emotions={"happy": 0.6},
            ),
            SentimentResult(
                label=SentimentLabel.NEGATIVE,
                score=0.3,
                confidence=0.8,
                emotions={"sad": 0.6},
            ),
        ]

        summary = analyzer.summarize_results(results)
        assert summary["total"] == 3
        assert summary["positive"] == 2
        assert summary["negative"] == 1
        assert summary["neutral"] == 0

    def test_get_emotion_distribution(self, analyzer):
        """测试获取情感分布"""
        results = [
            SentimentResult(
                label=SentimentLabel.POSITIVE,
                score=0.8,
                confidence=0.9,
                emotions={"happy": 0.7, "neutral": 0.3},
            ),
            SentimentResult(
                label=SentimentLabel.NEGATIVE,
                score=0.2,
                confidence=0.8,
                emotions={"sad": 0.6, "neutral": 0.4},
            ),
        ]

        distribution = analyzer.get_emotion_distribution(results)
        assert "happy" in distribution
        assert "sad" in distribution
        assert "neutral" in distribution
        assert sum(distribution.values()) == 1.0

    def test_merge_texts(self, analyzer):
        """测试文本合并"""
        # 短文本
        text = analyzer._merge_texts("标题", "内容")
        assert "标题" in text
        assert "内容" in text

        # 超长文本
        long_title = "A" * 200
        long_content = "B" * 500
        text = analyzer._merge_texts(long_title, long_content, max_length=100)
        assert len(text) <= 100

    def test_normalize_label(self, analyzer):
        """测试标签标准化"""
        assert analyzer._normalize_label("positive") == SentimentLabel.POSITIVE
        assert analyzer._normalize_label("negative") == SentimentLabel.NEGATIVE
        assert analyzer._normalize_label("neutral") == SentimentLabel.NEUTRAL
        assert analyzer._normalize_label("POSITIVE") == SentimentLabel.POSITIVE
        assert analyzer._normalize_label("joy") == SentimentLabel.POSITIVE
        assert analyzer._normalize_label("sad") == SentimentLabel.NEGATIVE

    def test_classify_sentiment_level(self, analyzer):
        """测试情感程度分类"""
        assert analyzer.classify_sentiment_level(0.95) == "非常积极"
        assert analyzer.classify_sentiment_level(0.8) == "积极"
        assert analyzer.classify_sentiment_level(0.6) == "中性偏正"
        assert analyzer.classify_sentiment_level(0.4) == "中性偏负"
        assert analyzer.classify_sentiment_level(0.2) == "消极"


class TestCreateAnalyzer:
    """测试创建分析器快捷函数"""

    @pytest.mark.skipif(
        True,
        reason="需要下载模型，跳过集成测试"
    )
    def test_create(self):
        """测试创建分析器"""
        analyzer = create_analyzer(device=-1)
        assert isinstance(analyzer, SentimentAnalyzer)

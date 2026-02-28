"""情感分析模块"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Tuple
from transformers import pipeline
import torch
from core.exceptions import AnalysisError
from core.logger import setup_logger

logger = setup_logger("xhs_sentiment")


class SentimentLabel(Enum):
    """情感标签"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class SentimentResult:
    """情感分析结果"""
    label: SentimentLabel
    score: float
    confidence: float
    emotions: Dict[str, float]


class SentimentAnalyzer:
    """情感分析器"""

    def __init__(
        self,
        model_name: str = "uer/roberta-base-finetuned-dianping-chinese",
        emotion_model: str = "lxyuan/distilbert-base-multilingual-cased-sentiments-student",
        device: Optional[int] = None,
        batch_size: int = 8,
    ):
        """初始化情感分析器

        Args:
            model_name: 基础情感模型名称
            emotion_model: 情感细分模型名称
            device: 使用的设备，None为自动选择
            batch_size: 批处理大小
        """
        self.model_name = model_name
        self.emotion_model = emotion_model
        self.batch_size = batch_size

        # 自动选择设备
        if device is None:
            self.device = 0 if torch.cuda.is_available() else -1
        else:
            self.device = device

        logger.info(f"使用设备: {'GPU' if self.device >= 0 else 'CPU'}")

        # 初始化模型
        self._init_models()

    def _init_models(self):
        """初始化情感分析模型"""
        try:
            logger.info(f"加载基础情感模型: {self.model_name}")
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                tokenizer=self.model_name,
                device=self.device,
                return_all_scores=False,
            )

            logger.info(f"加载情感细分模型: {self.emotion_model}")
            self.emotion_pipeline = pipeline(
                "sentiment-analysis",
                model=self.emotion_model,
                tokenizer=self.emotion_model,
                device=self.device,
                return_all_scores=True,
            )

            logger.info("情感分析模型加载完成")

        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            raise AnalysisError(f"加载情感分析模型失败: {e}")

    @staticmethod
    def _merge_texts(title: str, content: str, max_length: int = 512) -> str:
        """合并标题和内容，控制长度

        Args:
            title: 标题
            content: 内容
            max_length: 最大长度

        Returns:
            合并后的文本
        """
        if title and not content:
            return title
        if not title and content:
            return content
        if not title and not content:
            return ""

        combined = f"{title}\n{content}"
        if len(combined) <= max_length:
            return combined

        # 截断长文本
        if len(title) > max_length // 3:
            title = title[:max_length // 3] + "..."

        remaining = max_length - len(title) - 1
        if len(content) > remaining:
            content = content[:remaining] + "..."

        return f"{title}\n{content}"

    def _normalize_label(self, label: str) -> SentimentLabel:
        """标准化情感标签

        Args:
            label: 原始标签

        Returns:
            标准化的情感标签
        """
        label_lower = label.lower()

        # 情感标签映射
        positive_labels = ['positive', 'positive', 'pos', 'joy']
        negative_labels = ['negative', 'negative', 'neg', 'sad', 'anger', 'fear']

        if any(l in label_lower for l in positive_labels):
            return SentimentLabel.POSITIVE
        elif any(l in label_lower for l in negative_labels):
            return SentimentLabel.NEGATIVE
        else:
            return SentimentLabel.NEUTRAL

    def _extract_emotions(self, emotion_scores: List[Dict]) -> Dict[str, float]:
        """提取情感细分分数

        Args:
            emotion_scores: 原始情感分数

        Returns:
            标准化的情感分数字典
        """
        emotions = {}
        for item in emotion_scores:
            label = item['label'].lower()
            score = item['score']

            # 标准化情感名称
            if 'pos' in label or 'joy' in label or 'hap' in label:
                emotions['happy'] = max(emotions.get('happy', 0), score)
            elif 'neg' in label or 'sad' in label or 'ang' in label:
                emotions['sad'] = max(emotions.get('sad', 0), score)
            elif 'ang' in label or 'rage' in label:
                emotions['angry'] = max(emotions.get('angry', 0), score)
            elif 'fea' in label or 'fear' in label:
                emotions['fear'] = max(emotions.get('fear', 0), score)
            elif 'sur' in label or 'surprise' in label:
                emotions['surprise'] = max(emotions.get('surprise', 0), score)
            elif 'neu' in label or 'neut' in label:
                emotions['neutral'] = max(emotions.get('neutral', 0), score)

        return emotions

    def analyze_text(
        self,
        text: str,
    ) -> SentimentResult:
        """分析单条文本的情感

        Args:
            text: 待分析文本

        Returns:
            情感分析结果

        Raises:
            AnalysisError: 分析失败
        """
        if not text or not text.strip():
            raise AnalysisError("文本不能为空")

        try:
            # 基础情感分析
            sentiment_result = self.sentiment_pipeline(text)[0]
            label = self._normalize_label(sentiment_result['label'])
            score = sentiment_result['score']

            # 情感细分分析
            emotion_results = self.emotion_pipeline(text)[0]
            emotions = self._extract_emotions(emotion_results)

            # 计算综合置信度
            max_emotion = max(emotions.values()) if emotions else 0.5
            confidence = (score + max_emotion) / 2

            result = SentimentResult(
                label=label,
                score=score,
                confidence=confidence,
                emotions=emotions,
            )

            logger.debug(f"分析结果: {label}, 分数: {score:.3f}, 置信度: {confidence:.3f}")
            return result

        except Exception as e:
            logger.error(f"情感分析失败: {e}")
            raise AnalysisError(f"情感分析失败: {e}")

    def analyze_title_content(
        self,
        title: str,
        content: str,
    ) -> SentimentResult:
        """分析标题和内容的情感

        Args:
            title: 标题
            content: 内容

        Returns:
            情感分析结果
        """
        text = self._merge_texts(title, content)
        return self.analyze_text(text)

    def analyze_batch(
        self,
        texts: List[str],
    ) -> List[SentimentResult]:
        """批量分析文本情感

        Args:
            texts: 文本列表

        Returns:
            情感分析结果列表
        """
        if not texts:
            return []

        results = []
        total = len(texts)

        for i in range(0, total, self.batch_size):
            batch = texts[i:i + self.batch_size]
            logger.info(f"批量分析进度: {min(i + self.batch_size, total)}/{total}")

            try:
                # 批量推理
                sentiment_results = self.sentiment_pipeline(batch)
                emotion_results = self.emotion_pipeline(batch)

                for sentiment, emotions in zip(sentiment_results, emotion_results):
                    label = self._normalize_label(sentiment['label'])
                    score = sentiment['score']
                    emotion_dict = self._extract_emotions(emotions)
                    max_emotion = max(emotion_dict.values()) if emotion_dict else 0.5
                    confidence = (score + max_emotion) / 2

                    results.append(SentimentResult(
                        label=label,
                        score=score,
                        confidence=confidence,
                        emotions=emotion_dict,
                    ))

            except Exception as e:
                logger.error(f"批量分析失败: {e}")
                raise AnalysisError(f"批量分析失败: {e}")

        logger.info(f"批量分析完成，共 {len(results)} 条")
        return results

    @staticmethod
    def summarize_results(results: List[SentimentResult]) -> Dict:
        """汇总分析结果

        Args:
            results: 情感分析结果列表

        Returns:
            汇总统计信息
        """
        if not results:
            return {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0,
                'avg_confidence': 0.0,
            }

        total = len(results)
        positive = sum(1 for r in results if r.label == SentimentLabel.POSITIVE)
        negative = sum(1 for r in results if r.label == SentimentLabel.NEGATIVE)
        neutral = total - positive - negative

        avg_confidence = sum(r.confidence for r in results) / total

        # 汇总情感细分
        emotion_totals = {
            'happy': sum(r.emotions.get('happy', 0) for r in results),
            'sad': sum(r.emotions.get('sad', 0) for r in results),
            'angry': sum(r.emotions.get('angry', 0) for r in results),
            'fear': sum(r.emotions.get('fear', 0) for r in results),
            'surprise': sum(r.emotions.get('surprise', 0) for r in results),
            'neutral': sum(r.emotions.get('neutral', 0) for r in results),
        }

        return {
            'total': total,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'positive_ratio': positive / total,
            'negative_ratio': negative / total,
            'neutral_ratio': neutral / total,
            'avg_confidence': avg_confidence,
            'emotions': emotion_totals,
        }

    def classify_sentiment_level(self, score: float) -> str:
        """根据分数分类情感程度

        Args:
            score: 情感分数

        Returns:
            情感程度（非常积极/积极/中性/消极/非常消极）
        """
        if score >= 0.9:
            return "非常积极"
        elif score >= 0.7:
            return "积极"
        elif score >= 0.5:
            return "中性偏正"
        elif score >= 0.3:
            return "中性偏负"
        else:
            return "消极"

    def get_emotion_distribution(self, results: List[SentimentResult]) -> Dict[str, float]:
        """获取情感分布

        Args:
            results: 情感分析结果列表

        Returns:
            情感分布百分比
        """
        if not results:
            return {}

        distribution = {
            'happy': 0.0,
            'sad': 0.0,
            'angry': 0.0,
            'fear': 0.0,
            'surprise': 0.0,
            'neutral': 0.0,
        }

        total = len(results)
        for result in results:
            max_emotion = max(result.emotions.items(), key=lambda x: x[1]) if result.emotions else ('neutral', 0)
            distribution[max_emotion[0]] += 1

        # 归一化
        return {k: v / total for k, v in distribution.items()}


def create_analyzer(
    model_name: str = "uer/roberta-base-finetuned-dianping-chinese",
    device: Optional[int] = None,
) -> SentimentAnalyzer:
    """创建情感分析器的快捷函数

    Args:
        model_name: 模型名称
        device: 设备编号

    Returns:
        SentimentAnalyzer实例
    """
    return SentimentAnalyzer(model_name=model_name, device=device)

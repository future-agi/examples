"""
Sentiment Analysis Agent for the Multi-Agent AI Trading System
"""
import re
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from src.agents.base_agent import BaseAgent, AnalysisResult, MarketContext
from src.models.trading import AgentType, TradeAction
from src.integrations.openai.client import ModelType
from src.integrations.openai.functions import TradingFunctions, FunctionCategory
from src.utils.logging import get_agent_logger


class SentimentAnalyzer:
    """Sentiment analysis utilities"""
    
    def __init__(self):
        # Positive and negative word lists for basic sentiment analysis
        self.positive_words = {
            'bullish', 'buy', 'strong', 'growth', 'profit', 'gain', 'rise', 'up', 'positive',
            'excellent', 'good', 'great', 'outstanding', 'beat', 'exceed', 'outperform',
            'upgrade', 'rally', 'surge', 'boom', 'momentum', 'optimistic', 'confident'
        }
        
        self.negative_words = {
            'bearish', 'sell', 'weak', 'decline', 'loss', 'fall', 'down', 'negative',
            'poor', 'bad', 'terrible', 'miss', 'underperform', 'downgrade', 'crash',
            'plunge', 'recession', 'pessimistic', 'concerned', 'worried', 'risk'
        }
        
        # Financial keywords that amplify sentiment
        self.financial_amplifiers = {
            'earnings', 'revenue', 'guidance', 'forecast', 'outlook', 'target',
            'analyst', 'recommendation', 'rating', 'price target', 'estimates'
        }
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text using keyword-based approach"""
        if not text:
            return {"score": 0.0, "confidence": 0.0, "positive_count": 0, "negative_count": 0}
        
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        # Check for financial amplifiers
        amplifier_count = sum(1 for word in self.financial_amplifiers if word in text_lower)
        amplifier_factor = 1 + (amplifier_count * 0.2)  # 20% boost per amplifier
        
        # Calculate sentiment score (-1 to 1)
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            score = 0.0
            confidence = 0.0
        else:
            score = (positive_count - negative_count) / total_sentiment_words
            score *= amplifier_factor
            score = max(-1.0, min(1.0, score))  # Clamp to [-1, 1]
            confidence = min(total_sentiment_words / 10.0, 1.0)  # Max confidence at 10+ sentiment words
        
        return {
            "score": score,
            "confidence": confidence,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "amplifier_count": amplifier_count
        }
    
    def aggregate_sentiment(self, sentiment_scores: List[Dict[str, float]], 
                          weights: Optional[List[float]] = None) -> Dict[str, float]:
        """Aggregate multiple sentiment scores"""
        if not sentiment_scores:
            return {"score": 0.0, "confidence": 0.0}
        
        if weights is None:
            weights = [1.0] * len(sentiment_scores)
        
        if len(weights) != len(sentiment_scores):
            weights = [1.0] * len(sentiment_scores)
        
        # Weighted average of scores
        total_weight = sum(weights)
        if total_weight == 0:
            return {"score": 0.0, "confidence": 0.0}
        
        weighted_score = sum(score["score"] * weight for score, weight in zip(sentiment_scores, weights))
        weighted_score /= total_weight
        
        # Average confidence
        avg_confidence = sum(score["confidence"] for score in sentiment_scores) / len(sentiment_scores)
        
        return {
            "score": weighted_score,
            "confidence": avg_confidence
        }
    
    def classify_sentiment(self, score: float) -> str:
        """Classify sentiment score into categories"""
        if score >= 0.6:
            return "very_positive"
        elif score >= 0.2:
            return "positive"
        elif score >= -0.2:
            return "neutral"
        elif score >= -0.6:
            return "negative"
        else:
            return "very_negative"


class NewsAnalyzer:
    """News sentiment analysis utilities"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def analyze_news_articles(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment from news articles"""
        if not articles:
            return {
                "overall_sentiment": 0.0,
                "confidence": 0.0,
                "article_count": 0,
                "positive_articles": 0,
                "negative_articles": 0,
                "neutral_articles": 0
            }
        
        sentiment_scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for article in articles:
            title = article.get("title", "")
            content = article.get("content", "")
            
            # Analyze title and content
            title_sentiment = self.sentiment_analyzer.analyze_text_sentiment(title)
            content_sentiment = self.sentiment_analyzer.analyze_text_sentiment(content)
            
            # Weight title more heavily than content
            combined_score = (title_sentiment["score"] * 0.7 + content_sentiment["score"] * 0.3)
            combined_confidence = (title_sentiment["confidence"] + content_sentiment["confidence"]) / 2
            
            sentiment_scores.append({
                "score": combined_score,
                "confidence": combined_confidence
            })
            
            # Count sentiment categories
            if combined_score > 0.1:
                positive_count += 1
            elif combined_score < -0.1:
                negative_count += 1
            else:
                neutral_count += 1
        
        # Aggregate all sentiment scores
        overall_sentiment = self.sentiment_analyzer.aggregate_sentiment(sentiment_scores)
        
        return {
            "overall_sentiment": overall_sentiment["score"],
            "confidence": overall_sentiment["confidence"],
            "article_count": len(articles),
            "positive_articles": positive_count,
            "negative_articles": negative_count,
            "neutral_articles": neutral_count,
            "sentiment_distribution": {
                "positive": positive_count / len(articles),
                "negative": negative_count / len(articles),
                "neutral": neutral_count / len(articles)
            }
        }


class SocialMediaAnalyzer:
    """Social media sentiment analysis utilities"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def analyze_social_posts(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment from social media posts"""
        if not posts:
            return {
                "overall_sentiment": 0.0,
                "confidence": 0.0,
                "post_count": 0,
                "engagement_weighted_sentiment": 0.0
            }
        
        sentiment_scores = []
        engagement_weights = []
        
        for post in posts:
            text = post.get("text", "")
            likes = post.get("likes", 0)
            shares = post.get("shares", 0)
            comments = post.get("comments", 0)
            
            # Analyze post sentiment
            post_sentiment = self.sentiment_analyzer.analyze_text_sentiment(text)
            sentiment_scores.append(post_sentiment)
            
            # Calculate engagement weight
            engagement_score = likes + (shares * 2) + (comments * 1.5)  # Weight shares and comments more
            engagement_weights.append(max(1.0, np.log(engagement_score + 1)))  # Log scale to prevent outliers
        
        # Regular average
        overall_sentiment = self.sentiment_analyzer.aggregate_sentiment(sentiment_scores)
        
        # Engagement-weighted average
        engagement_weighted = self.sentiment_analyzer.aggregate_sentiment(sentiment_scores, engagement_weights)
        
        return {
            "overall_sentiment": overall_sentiment["score"],
            "confidence": overall_sentiment["confidence"],
            "post_count": len(posts),
            "engagement_weighted_sentiment": engagement_weighted["score"],
            "total_engagement": sum(p.get("likes", 0) + p.get("shares", 0) + p.get("comments", 0) for p in posts)
        }


class SentimentAnalysisAgent(BaseAgent):
    """Sentiment Analysis Agent for market sentiment analysis"""
    
    def __init__(self):
        super().__init__(AgentType.SENTIMENT, "sentiment_analysis_agent")
        self.sentiment_analyzer = SentimentAnalyzer()
        self.news_analyzer = NewsAnalyzer()
        self.social_analyzer = SocialMediaAnalyzer()
        
        # Sentiment analysis configuration
        self.sentiment_weights = {
            "news": 0.4,
            "social_media": 0.3,
            "analyst_reports": 0.3
        }
        
        self.logger.log_analysis(
            symbol="SYSTEM",
            analysis_type="initialization",
            result={"status": "Sentiment Analysis Agent initialized"}
        )
    
    def _initialize_agent(self):
        """Initialize sentiment analysis specific components"""
        self.sentiment_cache = {}
        self.source_reliability = {
            "reuters": 0.9,
            "bloomberg": 0.9,
            "wsj": 0.85,
            "cnbc": 0.8,
            "marketwatch": 0.75,
            "twitter": 0.6,
            "reddit": 0.5
        }
    
    def get_system_prompt(self) -> str:
        """Get system prompt for sentiment analysis"""
        return """You are a Sentiment Analysis Agent specializing in analyzing market sentiment from news, social media, and analyst reports.

Your responsibilities:
1. Analyze news articles and headlines for market sentiment
2. Process social media sentiment and engagement metrics
3. Evaluate analyst reports and recommendations
4. Aggregate sentiment from multiple sources with appropriate weights
5. Identify sentiment trends and momentum shifts
6. Assess impact of sentiment on stock price movements

Key principles:
- Weight sources by reliability and relevance
- Consider sentiment momentum and changes over time
- Distinguish between short-term noise and meaningful sentiment shifts
- Account for market context and broader sentiment
- Identify contrarian opportunities when sentiment is extreme
- Consider volume and engagement of sentiment sources

Always provide:
- Clear recommendation (buy/sell/hold)
- Confidence level (0.0 to 1.0)
- Detailed reasoning based on sentiment analysis
- Sentiment scores from different sources
- Sentiment trend and momentum assessment
- Risk factors related to sentiment extremes"""
    
    def get_analysis_functions(self) -> List[Dict[str, Any]]:
        """Get sentiment analysis function definitions"""
        return TradingFunctions.get_functions_by_category(FunctionCategory.SENTIMENT_ANALYSIS)
    
    async def analyze(self, context: MarketContext) -> AnalysisResult:
        """Perform sentiment analysis on market context"""
        try:
            # Get sentiment data (mock data for demonstration)
            sentiment_data = await self._get_sentiment_data(context.symbol)
            
            # Analyze news sentiment
            news_sentiment = await self._analyze_news_sentiment(sentiment_data.get("news", []))
            
            # Analyze social media sentiment
            social_sentiment = await self._analyze_social_sentiment(sentiment_data.get("social_media", []))
            
            # Analyze analyst sentiment
            analyst_sentiment = await self._analyze_analyst_sentiment(sentiment_data.get("analyst_reports", []))
            
            # Aggregate overall sentiment
            overall_sentiment = await self._aggregate_sentiment(news_sentiment, social_sentiment, analyst_sentiment)
            
            # Generate analysis prompt
            analysis_prompt = self._create_analysis_prompt(context, news_sentiment, social_sentiment, 
                                                         analyst_sentiment, overall_sentiment)
            
            # Query OpenAI for analysis
            messages = [
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.query_openai(messages, ModelType.GPT_4_TURBO)
            
            # Parse response
            if response["type"] == "function_call":
                result = self.parse_function_response(response)
                
                # Add sentiment data to analysis
                result.analysis_data.update({
                    "news_sentiment": news_sentiment,
                    "social_sentiment": social_sentiment,
                    "analyst_sentiment": analyst_sentiment,
                    "overall_sentiment": overall_sentiment,
                    "sentiment_summary": self._create_sentiment_summary(overall_sentiment)
                })
                
                # Validate result
                if self.validate_analysis_result(result):
                    return result
                else:
                    return self._create_fallback_result(context, overall_sentiment)
            else:
                return self._parse_text_response(context, response["content"], overall_sentiment)
                
        except Exception as e:
            self.logger.log_error(e, {"symbol": context.symbol, "context": "sentiment_analysis"})
            return self._create_error_result(context)
    
    async def _get_sentiment_data(self, symbol: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get sentiment data from various sources (mock data for demonstration)"""
        # In a real implementation, this would fetch from news APIs, social media APIs, etc.
        return {
            "news": [
                {
                    "title": f"{symbol} reports strong quarterly earnings, beats estimates",
                    "content": "The company showed excellent growth in revenue and profitability...",
                    "source": "reuters",
                    "timestamp": datetime.now(timezone.utc) - timedelta(hours=2)
                },
                {
                    "title": f"Analysts upgrade {symbol} price target on positive outlook",
                    "content": "Multiple analysts have raised their price targets following strong fundamentals...",
                    "source": "bloomberg",
                    "timestamp": datetime.now(timezone.utc) - timedelta(hours=6)
                },
                {
                    "title": f"Market volatility affects {symbol} trading",
                    "content": "Broader market concerns have impacted trading volumes...",
                    "source": "cnbc",
                    "timestamp": datetime.now(timezone.utc) - timedelta(hours=12)
                }
            ],
            "social_media": [
                {
                    "text": f"${symbol} looking bullish after earnings beat! 🚀",
                    "likes": 150,
                    "shares": 25,
                    "comments": 30,
                    "platform": "twitter"
                },
                {
                    "text": f"Great quarter for ${symbol}, strong fundamentals",
                    "likes": 89,
                    "shares": 12,
                    "comments": 18,
                    "platform": "reddit"
                },
                {
                    "text": f"Concerned about ${symbol} valuation at these levels",
                    "likes": 45,
                    "shares": 8,
                    "comments": 22,
                    "platform": "twitter"
                }
            ],
            "analyst_reports": [
                {
                    "analyst": "Goldman Sachs",
                    "rating": "Buy",
                    "price_target": 150.0,
                    "summary": "Strong fundamentals and growth prospects support higher valuation"
                },
                {
                    "analyst": "Morgan Stanley",
                    "rating": "Overweight",
                    "price_target": 145.0,
                    "summary": "Positive on long-term growth trajectory despite near-term headwinds"
                }
            ]
        }
    
    async def _analyze_news_sentiment(self, news_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze news sentiment"""
        return self.news_analyzer.analyze_news_articles(news_articles)
    
    async def _analyze_social_sentiment(self, social_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze social media sentiment"""
        return self.social_analyzer.analyze_social_posts(social_posts)
    
    async def _analyze_analyst_sentiment(self, analyst_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze analyst sentiment"""
        if not analyst_reports:
            return {
                "overall_sentiment": 0.0,
                "confidence": 0.0,
                "report_count": 0,
                "buy_ratings": 0,
                "hold_ratings": 0,
                "sell_ratings": 0
            }
        
        sentiment_scores = []
        buy_count = 0
        hold_count = 0
        sell_count = 0
        
        for report in analyst_reports:
            rating = report.get("rating", "").lower()
            summary = report.get("summary", "")
            
            # Convert rating to sentiment score
            if rating in ["buy", "strong buy", "overweight"]:
                rating_score = 0.8
                buy_count += 1
            elif rating in ["hold", "neutral", "equal weight"]:
                rating_score = 0.0
                hold_count += 1
            elif rating in ["sell", "strong sell", "underweight"]:
                rating_score = -0.8
                sell_count += 1
            else:
                rating_score = 0.0
                hold_count += 1
            
            # Analyze summary text
            summary_sentiment = self.sentiment_analyzer.analyze_text_sentiment(summary)
            
            # Combine rating and summary sentiment
            combined_score = (rating_score * 0.7 + summary_sentiment["score"] * 0.3)
            
            sentiment_scores.append({
                "score": combined_score,
                "confidence": 0.8  # High confidence in analyst reports
            })
        
        # Aggregate sentiment
        overall_sentiment = self.sentiment_analyzer.aggregate_sentiment(sentiment_scores)
        
        return {
            "overall_sentiment": overall_sentiment["score"],
            "confidence": overall_sentiment["confidence"],
            "report_count": len(analyst_reports),
            "buy_ratings": buy_count,
            "hold_ratings": hold_count,
            "sell_ratings": sell_count,
            "rating_distribution": {
                "buy": buy_count / len(analyst_reports),
                "hold": hold_count / len(analyst_reports),
                "sell": sell_count / len(analyst_reports)
            }
        }
    
    async def _aggregate_sentiment(self, news_sentiment: Dict[str, Any], 
                                 social_sentiment: Dict[str, Any],
                                 analyst_sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate sentiment from all sources"""
        sentiment_scores = []
        weights = []
        
        # Add news sentiment
        if news_sentiment["confidence"] > 0:
            sentiment_scores.append({
                "score": news_sentiment["overall_sentiment"],
                "confidence": news_sentiment["confidence"]
            })
            weights.append(self.sentiment_weights["news"])
        
        # Add social sentiment
        if social_sentiment["confidence"] > 0:
            sentiment_scores.append({
                "score": social_sentiment["overall_sentiment"],
                "confidence": social_sentiment["confidence"]
            })
            weights.append(self.sentiment_weights["social_media"])
        
        # Add analyst sentiment
        if analyst_sentiment["confidence"] > 0:
            sentiment_scores.append({
                "score": analyst_sentiment["overall_sentiment"],
                "confidence": analyst_sentiment["confidence"]
            })
            weights.append(self.sentiment_weights["analyst_reports"])
        
        if not sentiment_scores:
            return {
                "overall_sentiment": 0.0,
                "confidence": 0.0,
                "classification": "neutral"
            }
        
        # Weighted aggregation
        overall_sentiment = self.sentiment_analyzer.aggregate_sentiment(sentiment_scores, weights)
        
        # Classify sentiment
        classification = self.sentiment_analyzer.classify_sentiment(overall_sentiment["score"])
        
        return {
            "overall_sentiment": overall_sentiment["score"],
            "confidence": overall_sentiment["confidence"],
            "classification": classification,
            "source_breakdown": {
                "news": news_sentiment["overall_sentiment"],
                "social_media": social_sentiment["overall_sentiment"],
                "analyst": analyst_sentiment["overall_sentiment"]
            }
        }
    
    def _create_analysis_prompt(self, context: MarketContext, news_sentiment: Dict[str, Any],
                              social_sentiment: Dict[str, Any], analyst_sentiment: Dict[str, Any],
                              overall_sentiment: Dict[str, Any]) -> str:
        """Create analysis prompt for OpenAI"""
        current_price = context.current_price
        symbol = context.symbol
        
        prompt = f"""
Perform sentiment analysis for {symbol} at current price ${current_price:.2f}

NEWS SENTIMENT:
- Overall Score: {news_sentiment['overall_sentiment']:.3f} (-1 to 1)
- Confidence: {news_sentiment['confidence']:.3f}
- Articles Analyzed: {news_sentiment['article_count']}
- Positive Articles: {news_sentiment['positive_articles']}
- Negative Articles: {news_sentiment['negative_articles']}
- Neutral Articles: {news_sentiment['neutral_articles']}

SOCIAL MEDIA SENTIMENT:
- Overall Score: {social_sentiment['overall_sentiment']:.3f} (-1 to 1)
- Confidence: {social_sentiment['confidence']:.3f}
- Posts Analyzed: {social_sentiment['post_count']}
- Engagement-Weighted Score: {social_sentiment['engagement_weighted_sentiment']:.3f}
- Total Engagement: {social_sentiment['total_engagement']}

ANALYST SENTIMENT:
- Overall Score: {analyst_sentiment['overall_sentiment']:.3f} (-1 to 1)
- Confidence: {analyst_sentiment['confidence']:.3f}
- Reports Analyzed: {analyst_sentiment['report_count']}
- Buy Ratings: {analyst_sentiment['buy_ratings']}
- Hold Ratings: {analyst_sentiment['hold_ratings']}
- Sell Ratings: {analyst_sentiment['sell_ratings']}

OVERALL SENTIMENT:
- Aggregated Score: {overall_sentiment['overall_sentiment']:.3f} (-1 to 1)
- Classification: {overall_sentiment['classification']}
- Confidence: {overall_sentiment['confidence']:.3f}

Based on this sentiment analysis, provide:
1. Trading recommendation (buy/sell/hold)
2. Confidence level (0.0 to 1.0)
3. Detailed reasoning based on sentiment data
4. Assessment of sentiment momentum and trends
5. Risk factors related to sentiment extremes
6. Contrarian opportunities if applicable

Use the analyze_market_sentiment function to provide your analysis.
"""
        return prompt
    
    def _create_sentiment_summary(self, overall_sentiment: Dict[str, Any]) -> Dict[str, str]:
        """Create sentiment analysis summary"""
        summary = {}
        
        score = overall_sentiment["overall_sentiment"]
        classification = overall_sentiment["classification"]
        
        # Overall sentiment
        summary["overall"] = f"{classification.replace('_', ' ').title()} sentiment ({score:.2f})"
        
        # Sentiment strength
        if abs(score) > 0.6:
            summary["strength"] = "Strong sentiment signal"
        elif abs(score) > 0.3:
            summary["strength"] = "Moderate sentiment signal"
        else:
            summary["strength"] = "Weak sentiment signal"
        
        # Trading implication
        if score > 0.3:
            summary["implication"] = "Positive sentiment supports bullish outlook"
        elif score < -0.3:
            summary["implication"] = "Negative sentiment suggests bearish pressure"
        else:
            summary["implication"] = "Neutral sentiment provides limited directional bias"
        
        return summary
    
    def _create_fallback_result(self, context: MarketContext, overall_sentiment: Dict[str, Any]) -> AnalysisResult:
        """Create fallback result when analysis fails"""
        return AnalysisResult(
            agent_type=self.agent_type,
            symbol=context.symbol,
            recommendation=TradeAction.HOLD,
            confidence=0.3,
            reasoning="Sentiment analysis inconclusive - recommending hold position",
            analysis_data={
                "overall_sentiment": overall_sentiment,
                "fallback": True,
                "error": "Analysis validation failed"
            },
            timestamp=datetime.now(timezone.utc)
        )
    
    def _parse_text_response(self, context: MarketContext, content: str,
                           overall_sentiment: Dict[str, Any]) -> AnalysisResult:
        """Parse text response when function calling fails"""
        content_lower = content.lower()
        
        if "buy" in content_lower and "sell" not in content_lower:
            recommendation = TradeAction.BUY
            confidence = 0.6
        elif "sell" in content_lower and "buy" not in content_lower:
            recommendation = TradeAction.SELL
            confidence = 0.6
        else:
            recommendation = TradeAction.HOLD
            confidence = 0.5
        
        return AnalysisResult(
            agent_type=self.agent_type,
            symbol=context.symbol,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=content,
            analysis_data={
                "overall_sentiment": overall_sentiment,
                "response_type": "text_parsed"
            },
            timestamp=datetime.now(timezone.utc)
        )
    
    def _create_error_result(self, context: MarketContext) -> AnalysisResult:
        """Create error result when analysis completely fails"""
        return AnalysisResult(
            agent_type=self.agent_type,
            symbol=context.symbol,
            recommendation=TradeAction.HOLD,
            confidence=0.1,
            reasoning="Sentiment analysis failed due to error - defaulting to hold",
            analysis_data={"error": True},
            timestamp=datetime.now(timezone.utc)
        )
    
    def get_current_sentiment(self, context: MarketContext) -> Dict[str, Any]:
        """Get current sentiment summary for quick reference"""
        try:
            sentiment_data = self._get_sentiment_data(context.symbol)
            news_sentiment = self._analyze_news_sentiment(sentiment_data.get("news", []))
            social_sentiment = self._analyze_social_sentiment(sentiment_data.get("social_media", []))
            analyst_sentiment = self._analyze_analyst_sentiment(sentiment_data.get("analyst_reports", []))
            overall_sentiment = self._aggregate_sentiment(news_sentiment, social_sentiment, analyst_sentiment)
            
            return overall_sentiment
        except Exception as e:
            self.logger.log_error(e, {"symbol": context.symbol})
            return {"error": "Failed to get current sentiment"}


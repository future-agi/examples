"""
News and Sentiment Data Provider for the Multi-Agent AI Trading System
"""
import asyncio
import aiohttp
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import re
import hashlib

from config.settings import config
from src.utils.logging import get_component_logger

logger = get_component_logger("news_provider")


@dataclass
class NewsArticle:
    """News article data structure"""
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    sentiment_score: Optional[float] = None
    relevance_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at.isoformat(),
            "sentiment_score": self.sentiment_score,
            "relevance_score": self.relevance_score
        }
    
    def get_id(self) -> str:
        """Generate unique ID for the article"""
        content_hash = hashlib.md5(f"{self.title}{self.url}".encode()).hexdigest()
        return f"{self.source}_{content_hash[:8]}"


@dataclass
class SocialMediaPost:
    """Social media post data structure"""
    text: str
    platform: str
    author: str
    likes: int
    shares: int
    comments: int
    posted_at: datetime
    sentiment_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "platform": self.platform,
            "author": self.author,
            "likes": self.likes,
            "shares": self.shares,
            "comments": self.comments,
            "posted_at": self.posted_at.isoformat(),
            "sentiment_score": self.sentiment_score
        }


class MockNewsProvider:
    """Mock news provider for demonstration purposes"""
    
    def __init__(self):
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0
        
        # Mock news templates
        self.news_templates = {
            "earnings": [
                "{symbol} reports {result} quarterly earnings, {direction} estimates",
                "{symbol} {quarter} earnings {result} expectations with {metric} growth",
                "Analysts {reaction} after {symbol} {result} earnings report"
            ],
            "analyst": [
                "Analysts {action} {symbol} price target on {reason}",
                "{firm} {action} {symbol} rating to {rating}",
                "Wall Street {sentiment} on {symbol} following {event}"
            ],
            "market": [
                "{symbol} shares {direction} on {reason}",
                "Market volatility affects {symbol} trading",
                "{symbol} stock {movement} amid {market_condition}"
            ],
            "company": [
                "{symbol} announces {announcement}",
                "{symbol} CEO discusses {topic} in latest interview",
                "{symbol} expands {business_area} operations"
            ]
        }
        
        # Mock social media templates
        self.social_templates = [
            "${symbol} looking {sentiment} after {event}! {emoji}",
            "{sentiment_word} quarter for ${symbol}, {reason}",
            "{opinion} about ${symbol} {aspect} at these levels",
            "Just bought more ${symbol} - {reason} {emoji}",
            "${symbol} {prediction} - {reasoning}"
        ]
    
    async def _rate_limit(self):
        """Apply rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def _generate_mock_news(self, symbol: str, count: int = 5) -> List[NewsArticle]:
        """Generate mock news articles"""
        articles = []
        
        # Predefined values for templates
        template_values = {
            "symbol": symbol,
            "result": ["strong", "weak", "mixed", "better than expected", "disappointing"][hash(symbol) % 5],
            "direction": ["beats", "misses", "meets"][hash(symbol) % 3],
            "quarter": ["Q1", "Q2", "Q3", "Q4"][hash(symbol) % 4],
            "metric": ["revenue", "profit", "user", "subscription"][hash(symbol) % 4],
            "reaction": ["optimistic", "cautious", "positive", "concerned"][hash(symbol) % 4],
            "action": ["upgrade", "downgrade", "maintain", "initiate"][hash(symbol) % 4],
            "firm": ["Goldman Sachs", "Morgan Stanley", "JP Morgan", "Bank of America"][hash(symbol) % 4],
            "rating": ["Buy", "Hold", "Sell", "Overweight"][hash(symbol) % 4],
            "sentiment": ["bullish", "bearish", "mixed", "optimistic"][hash(symbol) % 4],
            "event": ["earnings", "guidance", "product launch", "acquisition"][hash(symbol) % 4],
            "reason": ["strong fundamentals", "market conditions", "sector rotation", "technical breakout"][hash(symbol) % 4],
            "movement": ["surges", "declines", "fluctuates", "stabilizes"][hash(symbol) % 4],
            "market_condition": ["broader market rally", "sector weakness", "economic uncertainty", "investor optimism"][hash(symbol) % 4],
            "announcement": ["new product", "partnership", "expansion", "restructuring"][hash(symbol) % 4],
            "topic": ["growth strategy", "market outlook", "innovation", "sustainability"][hash(symbol) % 4],
            "business_area": ["international", "digital", "retail", "enterprise"][hash(symbol) % 4]
        }
        
        sources = ["Reuters", "Bloomberg", "CNBC", "MarketWatch", "Yahoo Finance"]
        
        for i in range(count):
            # Choose random template category and template
            category = list(self.news_templates.keys())[i % len(self.news_templates)]
            template = self.news_templates[category][i % len(self.news_templates[category])]
            
            # Fill template
            title = template.format(**template_values)
            
            # Generate content
            content = f"The company showed {template_values['result']} performance in the latest quarter. " \
                     f"Analysts are {template_values['reaction']} about the {template_values['metric']} growth. " \
                     f"Market conditions and {template_values['reason']} continue to impact trading."
            
            # Create article
            article = NewsArticle(
                title=title,
                content=content,
                source=sources[i % len(sources)],
                url=f"https://example.com/news/{symbol.lower()}-{i}",
                published_at=datetime.now(timezone.utc) - timedelta(hours=i*2)
            )
            
            articles.append(article)
        
        return articles
    
    def _generate_mock_social_posts(self, symbol: str, count: int = 10) -> List[SocialMediaPost]:
        """Generate mock social media posts"""
        posts = []
        
        # Template values
        template_values = {
            "symbol": symbol,
            "sentiment": ["bullish", "bearish", "neutral"][hash(symbol) % 3],
            "event": ["earnings beat", "product launch", "analyst upgrade", "market rally"][hash(symbol) % 4],
            "emoji": ["🚀", "📈", "💪", "🔥", "📉", "😬"][hash(symbol) % 6],
            "sentiment_word": ["Great", "Disappointing", "Mixed", "Strong"][hash(symbol) % 4],
            "reason": ["strong fundamentals", "great management", "innovative products", "market leadership"][hash(symbol) % 4],
            "opinion": ["Concerned", "Excited", "Optimistic", "Cautious"][hash(symbol) % 4],
            "aspect": ["valuation", "growth prospects", "competition", "market position"][hash(symbol) % 4],
            "prediction": ["to the moon", "heading lower", "sideways action", "breakout coming"][hash(symbol) % 4],
            "reasoning": ["technical analysis shows strength", "fundamentals look solid", "market sentiment shifting", "insider buying"][hash(symbol) % 4]
        }
        
        platforms = ["twitter", "reddit", "stocktwits"]
        authors = ["trader123", "investor_pro", "market_guru", "stock_picker", "finance_nerd"]
        
        for i in range(count):
            template = self.social_templates[i % len(self.social_templates)]
            text = template.format(**template_values)
            
            # Generate engagement metrics
            base_engagement = hash(f"{symbol}{i}") % 1000
            
            post = SocialMediaPost(
                text=text,
                platform=platforms[i % len(platforms)],
                author=authors[i % len(authors)],
                likes=base_engagement + (i * 10),
                shares=max(1, (base_engagement // 10) + i),
                comments=max(1, (base_engagement // 20) + i),
                posted_at=datetime.now(timezone.utc) - timedelta(minutes=i*30)
            )
            
            posts.append(post)
        
        return posts
    
    async def get_news(self, symbol: str, limit: int = 10) -> List[NewsArticle]:
        """Get news articles for a symbol"""
        try:
            await self._rate_limit()
            
            # Generate mock news
            articles = self._generate_mock_news(symbol, limit)
            
            logger.info(f"Retrieved {len(articles)} news articles for {symbol}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []
    
    async def get_social_media_posts(self, symbol: str, limit: int = 20) -> List[SocialMediaPost]:
        """Get social media posts for a symbol"""
        try:
            await self._rate_limit()
            
            # Generate mock social posts
            posts = self._generate_mock_social_posts(symbol, limit)
            
            logger.info(f"Retrieved {len(posts)} social media posts for {symbol}")
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching social media posts for {symbol}: {e}")
            return []


class NewsDataProcessor:
    """Process and analyze news data"""
    
    def __init__(self):
        self.relevance_keywords = {
            "high": ["earnings", "revenue", "profit", "guidance", "acquisition", "merger", "ipo"],
            "medium": ["analyst", "upgrade", "downgrade", "target", "rating", "recommendation"],
            "low": ["market", "sector", "industry", "economic", "federal", "interest"]
        }
    
    def calculate_relevance_score(self, article: NewsArticle, symbol: str) -> float:
        """Calculate relevance score for an article"""
        try:
            text = f"{article.title} {article.content}".lower()
            symbol_lower = symbol.lower()
            
            # Base score for symbol mention
            score = 0.0
            
            # Symbol mentions
            symbol_count = text.count(symbol_lower)
            score += min(symbol_count * 0.2, 0.6)  # Max 0.6 for symbol mentions
            
            # Keyword relevance
            for relevance_level, keywords in self.relevance_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        if relevance_level == "high":
                            score += 0.3
                        elif relevance_level == "medium":
                            score += 0.2
                        else:
                            score += 0.1
            
            # Source reliability bonus
            reliable_sources = ["reuters", "bloomberg", "wall street journal"]
            if article.source.lower() in reliable_sources:
                score += 0.1
            
            # Recency bonus (newer articles get higher scores)
            hours_old = (datetime.now(timezone.utc) - article.published_at).total_seconds() / 3600
            if hours_old < 24:
                score += 0.1 * (1 - hours_old / 24)
            
            return min(score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.5  # Default score
    
    def filter_relevant_articles(self, articles: List[NewsArticle], symbol: str, 
                                min_relevance: float = 0.3) -> List[NewsArticle]:
        """Filter articles by relevance score"""
        relevant_articles = []
        
        for article in articles:
            relevance_score = self.calculate_relevance_score(article, symbol)
            article.relevance_score = relevance_score
            
            if relevance_score >= min_relevance:
                relevant_articles.append(article)
        
        # Sort by relevance score (descending)
        relevant_articles.sort(key=lambda x: x.relevance_score or 0, reverse=True)
        
        return relevant_articles
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        # Simple keyword extraction (in a real system, use NLP libraries)
        financial_terms = [
            "earnings", "revenue", "profit", "loss", "guidance", "forecast",
            "upgrade", "downgrade", "buy", "sell", "hold", "target price",
            "analyst", "recommendation", "rating", "outlook", "growth",
            "acquisition", "merger", "ipo", "dividend", "split"
        ]
        
        text_lower = text.lower()
        found_phrases = []
        
        for term in financial_terms:
            if term in text_lower:
                found_phrases.append(term)
        
        return found_phrases
    
    def summarize_news_sentiment(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Summarize overall news sentiment"""
        if not articles:
            return {
                "overall_sentiment": 0.0,
                "article_count": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0
            }
        
        # Simple sentiment analysis based on keywords
        positive_words = ["strong", "beat", "exceed", "growth", "positive", "upgrade", "buy"]
        negative_words = ["weak", "miss", "decline", "negative", "downgrade", "sell", "loss"]
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for article in articles:
            text = f"{article.title} {article.content}".lower()
            
            pos_score = sum(1 for word in positive_words if word in text)
            neg_score = sum(1 for word in negative_words if word in text)
            
            if pos_score > neg_score:
                positive_count += 1
            elif neg_score > pos_score:
                negative_count += 1
            else:
                neutral_count += 1
        
        total_articles = len(articles)
        overall_sentiment = (positive_count - negative_count) / total_articles
        
        return {
            "overall_sentiment": overall_sentiment,
            "article_count": total_articles,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "sentiment_distribution": {
                "positive": positive_count / total_articles,
                "negative": negative_count / total_articles,
                "neutral": neutral_count / total_articles
            }
        }


class NewsDataManager:
    """Main news data manager"""
    
    def __init__(self):
        self.news_provider = MockNewsProvider()
        self.processor = NewsDataProcessor()
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 1800  # 30 minutes
        
        logger.info("News Data Manager initialized")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache_expiry:
            return False
        return datetime.now(timezone.utc) < self.cache_expiry[cache_key]
    
    def _cache_data(self, cache_key: str, data: Any):
        """Cache data with expiry"""
        self.cache[cache_key] = data
        self.cache_expiry[cache_key] = datetime.now(timezone.utc) + timedelta(seconds=self.cache_duration)
    
    async def get_news_for_symbol(self, symbol: str, limit: int = 10) -> List[NewsArticle]:
        """Get news articles for a symbol"""
        try:
            cache_key = f"news_{symbol}_{limit}"
            
            # Check cache first
            if self._is_cache_valid(cache_key):
                logger.info(f"Using cached news for {symbol}")
                return self.cache[cache_key]
            
            # Fetch fresh news
            articles = await self.news_provider.get_news(symbol, limit)
            
            # Filter for relevance
            relevant_articles = self.processor.filter_relevant_articles(articles, symbol)
            
            # Cache the results
            self._cache_data(cache_key, relevant_articles)
            
            return relevant_articles
            
        except Exception as e:
            logger.error(f"Error getting news for {symbol}: {e}")
            return []
    
    async def get_social_media_for_symbol(self, symbol: str, limit: int = 20) -> List[SocialMediaPost]:
        """Get social media posts for a symbol"""
        try:
            cache_key = f"social_{symbol}_{limit}"
            
            # Check cache first
            if self._is_cache_valid(cache_key):
                logger.info(f"Using cached social media for {symbol}")
                return self.cache[cache_key]
            
            # Fetch fresh social media posts
            posts = await self.news_provider.get_social_media_posts(symbol, limit)
            
            # Cache the results
            self._cache_data(cache_key, posts)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error getting social media for {symbol}: {e}")
            return []
    
    async def get_sentiment_summary(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive sentiment summary for a symbol"""
        try:
            # Get news and social media data
            news_articles = await self.get_news_for_symbol(symbol)
            social_posts = await self.get_social_media_for_symbol(symbol)
            
            # Analyze news sentiment
            news_sentiment = self.processor.summarize_news_sentiment(news_articles)
            
            # Simple social media sentiment (based on engagement)
            social_sentiment = self._analyze_social_sentiment(social_posts)
            
            # Combine sentiments
            combined_sentiment = self._combine_sentiments(news_sentiment, social_sentiment)
            
            return {
                "symbol": symbol,
                "news_sentiment": news_sentiment,
                "social_sentiment": social_sentiment,
                "combined_sentiment": combined_sentiment,
                "data_freshness": {
                    "news_articles": len(news_articles),
                    "social_posts": len(social_posts),
                    "last_update": datetime.now(timezone.utc).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting sentiment summary for {symbol}: {e}")
            return {
                "symbol": symbol,
                "error": str(e),
                "news_sentiment": {},
                "social_sentiment": {},
                "combined_sentiment": {}
            }
    
    def _analyze_social_sentiment(self, posts: List[SocialMediaPost]) -> Dict[str, Any]:
        """Analyze social media sentiment"""
        if not posts:
            return {
                "overall_sentiment": 0.0,
                "post_count": 0,
                "engagement_weighted_sentiment": 0.0
            }
        
        # Simple sentiment based on keywords
        positive_words = ["bullish", "buy", "moon", "strong", "great", "love"]
        negative_words = ["bearish", "sell", "weak", "bad", "hate", "concerned"]
        
        total_sentiment = 0.0
        weighted_sentiment = 0.0
        total_engagement = 0
        
        for post in posts:
            text = post.text.lower()
            
            pos_score = sum(1 for word in positive_words if word in text)
            neg_score = sum(1 for word in negative_words if word in text)
            
            # Calculate sentiment (-1 to 1)
            if pos_score + neg_score > 0:
                sentiment = (pos_score - neg_score) / (pos_score + neg_score)
            else:
                sentiment = 0.0
            
            total_sentiment += sentiment
            
            # Weight by engagement
            engagement = post.likes + post.shares + post.comments
            weighted_sentiment += sentiment * engagement
            total_engagement += engagement
        
        avg_sentiment = total_sentiment / len(posts)
        engagement_weighted = weighted_sentiment / total_engagement if total_engagement > 0 else 0.0
        
        return {
            "overall_sentiment": avg_sentiment,
            "post_count": len(posts),
            "engagement_weighted_sentiment": engagement_weighted,
            "total_engagement": total_engagement
        }
    
    def _combine_sentiments(self, news_sentiment: Dict[str, Any], 
                          social_sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """Combine news and social media sentiments"""
        # Weight news more heavily than social media
        news_weight = 0.7
        social_weight = 0.3
        
        news_score = news_sentiment.get("overall_sentiment", 0.0)
        social_score = social_sentiment.get("overall_sentiment", 0.0)
        
        combined_score = (news_score * news_weight) + (social_score * social_weight)
        
        return {
            "overall_sentiment": combined_score,
            "confidence": min(
                news_sentiment.get("article_count", 0) / 10.0 + 
                social_sentiment.get("post_count", 0) / 20.0, 
                1.0
            ),
            "news_weight": news_weight,
            "social_weight": social_weight
        }


# Global news data manager instance
news_data_manager = NewsDataManager()


# -*- coding: utf-8 -*-
"""
Indian Stock Market News Analyzer
Fetches 20 most recent news articles and provides AI-generated summary
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from textblob import TextBlob
import streamlit as st
import warnings
warnings.filterwarnings('ignore')

# Sector-wise stocks
SECTORS = {
    "Information Technology (IT) & Services": [
        "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"
    ],
    "Banking & Financial Services": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS",
        "AXISBANK.NS", "BAJFINANCE.NS", "HDFCLIFE.NS", "ICICIPRULI.NS"
    ],
    "Conglomerates & Industrial": [
        "RELIANCE.NS", "LT.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "M&M.NS"
    ],
    "Consumer Goods & Telecom": [
        "ITC.NS", "HINDUNILVR.NS", "BRITANNIA.NS", "BHARTIARTL.NS", "MARUTI.NS"
    ],
    "Energy & Commodities": [
        "ONGC.NS", "NTPC.NS", "COALINDIA.NS", "HINDALCO.NS", "JSWSTEEL.NS"
    ]
}

NEWS_API_KEY = "6b4efd22e1b4433488adb20e81814840"

class StockNewsAnalyzer:
    def __init__(self, ticker, news_api_key):
        self.ticker = ticker
        self.news_api_key = news_api_key
        self.stock_data = None
        self.news_articles = []

    def fetch_stock_data(self):
        """Fetch current stock data"""
        stock = yf.Ticker(self.ticker)
        self.stock_data = stock.history(period="5d")
        return self.stock_data

    def get_company_name(self):
        """Get company name from ticker"""
        try:
            stock = yf.Ticker(self.ticker)
            info = stock.info
            company_name = info.get('longName', self.ticker.replace('.NS', ''))
            company_name = company_name.replace('Limited', '').replace('Ltd', '').strip()
            return company_name
        except:
            return self.ticker.replace('.NS', '')

    def fetch_news(self, days_back=30):
        """Fetch exactly 20 most recent news articles"""
        company_name = self.get_company_name()
        ticker_short = self.ticker.replace('.NS', '')

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        url = "https://newsapi.org/v2/everything"
        
        search_queries = [
            f'({company_name} OR {ticker_short}) AND (stock OR share OR market)',
            f'{company_name} stock',
            f'{ticker_short} share market',
            f'{company_name}',
            f'{ticker_short}'
        ]
        
        all_articles = []
        seen_urls = set()
        
        for query in search_queries:
            if len(all_articles) >= 20:
                break
                
            params = {
                'q': query,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 100,
                'apiKey': self.news_api_key
            }

            try:
                response = requests.get(url, params=params, timeout=15)
                news_data = response.json()

                if news_data.get('status') == 'ok':
                    articles = news_data.get('articles', [])
                    
                    for article in articles:
                        article_url = article.get('url', '')
                        if article_url and article_url not in seen_urls:
                            seen_urls.add(article_url)
                            all_articles.append(article)
                            
                            if len(all_articles) >= 20:
                                break

            except Exception as e:
                continue

        if len(all_articles) >= 20:
            self.news_articles = all_articles[:20]
            st.success(f"✅ Successfully fetched 20 news articles for {company_name}")
            return True
        elif len(all_articles) > 0:
            self.news_articles = all_articles
            st.warning(f"⚠️ Found only {len(all_articles)} news articles for {company_name}")
            return True
        else:
            st.error(f"❌ No news articles found for {company_name}")
            return False

    def generate_summary(self):
        """Generate a comprehensive summary from news articles"""
        if not self.news_articles:
            return "No news articles available for summary."
        
        # Analyze sentiment
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        all_text = []
        key_topics = []
        
        for article in self.news_articles:
            title = article.get('title', '')
            description = article.get('description', '')
            text = f"{title}. {description}"
            all_text.append(text)
            
            # Sentiment analysis
            blob = TextBlob(text)
            sentiment = blob.sentiment.polarity
            
            if sentiment > 0.1:
                positive_count += 1
            elif sentiment < -0.1:
                negative_count += 1
            else:
                neutral_count += 1
        
        # Generate summary
        company_name = self.get_company_name()
        total_articles = len(self.news_articles)
        
        # Determine overall sentiment
        if positive_count > negative_count:
            overall_sentiment = "predominantly positive"
            sentiment_emoji = "📈"
        elif negative_count > positive_count:
            overall_sentiment = "predominantly negative"
            sentiment_emoji = "📉"
        else:
            overall_sentiment = "mixed"
            sentiment_emoji = "➡️"
        
        # Create summary
        summary_lines = []
        summary_lines.append(f"📰 **News Summary for {company_name} ({self.ticker})**\n")
        summary_lines.append(f"**Analysis Period:** Last {total_articles} most recent articles\n")
        summary_lines.append(f"**Overall Sentiment:** {overall_sentiment.title()} {sentiment_emoji}\n")
        summary_lines.append(f"**Sentiment Breakdown:**")
        summary_lines.append(f"- Positive Articles: {positive_count} ({positive_count/total_articles*100:.1f}%)")
        summary_lines.append(f"- Negative Articles: {negative_count} ({negative_count/total_articles*100:.1f}%)")
        summary_lines.append(f"- Neutral Articles: {neutral_count} ({neutral_count/total_articles*100:.1f}%)\n")
        
        # Key insights from titles
        summary_lines.append("**Key Topics Covered:**")
        topics_mentioned = []
        
        keywords = {
            'earnings': ['earnings', 'profit', 'revenue', 'quarter', 'results'],
            'growth': ['growth', 'expansion', 'increase', 'rise', 'surge'],
            'challenges': ['fall', 'drop', 'decline', 'loss', 'challenge'],
            'innovation': ['launch', 'innovation', 'technology', 'digital', 'AI'],
            'market': ['market', 'stock', 'share', 'investor', 'trading'],
            'regulatory': ['regulatory', 'compliance', 'government', 'policy'],
            'partnership': ['partnership', 'deal', 'agreement', 'collaboration']
        }
        
        for topic, keywords_list in keywords.items():
            count = sum(1 for article in self.news_articles 
                       if any(keyword.lower() in article.get('title', '').lower() or 
                             keyword.lower() in article.get('description', '').lower() 
                             for keyword in keywords_list))
            if count > 0:
                topics_mentioned.append(f"- {topic.title()}: {count} mentions")
        
        summary_lines.extend(topics_mentioned if topics_mentioned else ["- General market and company updates"])
        
        summary_lines.append("\n**Key Highlights:**")
        
        # Add most recent article highlights
        for i, article in enumerate(self.news_articles[:5], 1):
            title = article.get('title', 'No title')
            date = article.get('publishedAt', '')[:10]
            summary_lines.append(f"{i}. [{date}] {title}")
        
        summary_lines.append(f"\n**Market Context:**")
        if len(self.stock_data) > 1:
            current_price = self.stock_data['Close'].iloc[-1]
            prev_price = self.stock_data['Close'].iloc[-2]
            price_change = ((current_price - prev_price) / prev_price) * 100
            
            summary_lines.append(f"- Current Stock Price: ₹{current_price:.2f}")
            summary_lines.append(f"- Recent Change: {price_change:+.2f}%")
        
        summary_lines.append("\n**Conclusion:**")
        if positive_count > negative_count * 1.5:
            summary_lines.append(f"The news coverage for {company_name} is strongly positive, suggesting favorable market sentiment and potential growth opportunities. Investors appear optimistic about the company's prospects.")
        elif negative_count > positive_count * 1.5:
            summary_lines.append(f"The news coverage for {company_name} shows concerning trends with predominantly negative sentiment. Investors should exercise caution and monitor developments closely.")
        else:
            summary_lines.append(f"The news coverage for {company_name} presents a balanced view with mixed sentiment. The company faces both opportunities and challenges, requiring careful analysis by investors.")
        
        return "\n".join(summary_lines)


def main():
    st.set_page_config(page_title="Stock News Analyzer", page_icon="📰", layout="wide")

    st.title("📰 Indian Stock Market News Analyzer")
    st.markdown("**AI-Powered Analysis of 20 Most Recent News Articles**")

    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/3/3a/Stock_market_icon.png", width=180)
        st.header("🎛️ Analysis Settings")

        sector = st.selectbox("📊 Select Sector", list(SECTORS.keys()))
        ticker = st.selectbox("🏢 Select Stock", SECTORS[sector])

        st.markdown("---")
        st.subheader("📰 News Settings")
        news_days = st.slider("News History (days)", 7, 90, 30)

        st.markdown("---")
        analyze_button = st.button("🚀 Analyze News", type="primary", use_container_width=True)

    if analyze_button:
        try:
            with st.spinner(f"🔍 Analyzing news for {ticker}..."):
                analyzer = StockNewsAnalyzer(ticker, NEWS_API_KEY)
                company_name = analyzer.get_company_name()

                st.info(f"📊 Fetching stock data for {company_name}...")
                analyzer.fetch_stock_data()

                st.info(f"📰 Fetching 20 most recent news articles...")
                news_fetched = analyzer.fetch_news(days_back=news_days)

                if not news_fetched:
                    st.error("❌ Cannot proceed without news data. Please try a different stock.")
                    return

                st.success("✅ Analysis Complete!")

                # Display Summary
                st.markdown("---")
                st.header("📋 News Summary & Analysis")
                
                summary = analyzer.generate_summary()
                st.markdown(summary)

                # Display Metrics
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)

                if len(analyzer.stock_data) > 0:
                    current_price = analyzer.stock_data['Close'].iloc[-1]
                    
                    with col1:
                        st.metric("Current Price", f"₹{current_price:.2f}")
                    
                    with col2:
                        if len(analyzer.stock_data) > 1:
                            prev_price = analyzer.stock_data['Close'].iloc[-2]
                            price_change = ((current_price - prev_price) / prev_price) * 100
                            st.metric("Recent Change", f"{price_change:+.2f}%", delta=f"{price_change:+.2f}%")
                
                with col3:
                    # Calculate average sentiment
                    sentiments = []
                    for article in analyzer.news_articles:
                        text = f"{article.get('title', '')} {article.get('description', '')}"
                        sentiment = TextBlob(text).sentiment.polarity
                        sentiments.append(sentiment)
                    
                    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
                    sentiment_emoji = "🟢" if avg_sentiment > 0.1 else "🔴" if avg_sentiment < -0.1 else "🟡"
                    st.metric("Avg Sentiment", f"{avg_sentiment:.3f} {sentiment_emoji}")
                
                with col4:
                    st.metric("News Articles", len(analyzer.news_articles))

                # Display All 20 News Articles
                st.markdown("---")
                st.header(f"📰 All {len(analyzer.news_articles)} News Articles")

                for idx, article in enumerate(analyzer.news_articles, 1):
                    with st.expander(f"📄 Article {idx}: {article.get('title', 'No Title')[:100]}..."):
                        cols = st.columns([3, 1])

                        with cols[0]:
                            st.markdown(f"**Source:** {article.get('source', {}).get('name', 'Unknown')}")
                            st.markdown(f"**Published:** {article.get('publishedAt', 'Unknown')[:10]}")
                            st.markdown(f"**Description:** {article.get('description', 'No description available')}")
                            st.markdown(f"[🔗 Read Full Article]({article.get('url', '#')})")

                        with cols[1]:
                            text = f"{article.get('title', '')} {article.get('description', '')}"
                            sentiment = TextBlob(text).sentiment.polarity

                            if sentiment > 0.1:
                                sent_label = "Positive 😊"
                                sent_color = "green"
                            elif sentiment < -0.1:
                                sent_label = "Negative 😟"
                                sent_color = "red"
                            else:
                                sent_label = "Neutral 😐"
                                sent_color = "gray"

                            st.markdown(f"**Sentiment:**")
                            st.markdown(f"<span style='color:{sent_color}; font-size:18px'>{sent_label}</span>",
                                       unsafe_allow_html=True)
                            st.markdown(f"**Score:** {sentiment:.3f}")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Tip: Try selecting a different stock or check your internet connection")

    else:
        st.info("👈 Select a sector and stock from the sidebar, then click 'Analyze News'")

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            ### 🎯 Features:
            - ✅ Fetches 20 most recent news articles
            - ✅ Sentiment analysis on each article
            - ✅ AI-generated comprehensive summary
            - ✅ Key topics and highlights
            - ✅ Overall market sentiment analysis
            - ✅ Current stock price tracking
            """)

        with col2:
            st.markdown("""
            ### 📊 Available Sectors:
            - 💻 IT & Services
            - 🏦 Banking & Financial Services
            - 🏭 Conglomerates & Industrial
            - 🛍️ Consumer Goods & Telecom
            - ⚡ Energy & Commodities
            """)

        st.success("🔐 Using NewsAPI for real-time news analysis")


if __name__ == "__main__":
    main()

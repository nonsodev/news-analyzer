# app.py - Enhanced Streamlit News Analyzer with Interactive Dashboard

import streamlit as st
from main import NewsAnalyzer
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any

def create_sentiment_gauge(sentiment_data: Dict[str, Any]) -> go.Figure:
    """Create a gauge chart for sentiment analysis"""
    sentiment_map = {"Positive": 0.8, "Negative": 0.2, "Neutral": 0.5, "Mixed": 0.6}
    value = sentiment_map.get(sentiment_data.get("overall_sentiment", "Neutral"), 0.5)
    confidence = sentiment_data.get("confidence", 0.5)
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Sentiment: {sentiment_data.get('overall_sentiment', 'Unknown')}"},
        delta = {'reference': 0.5},
        gauge = {
            'axis': {'range': [None, 1]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 0.3], 'color': "lightcoral"},
                {'range': [0.3, 0.7], 'color': "lightyellow"},
                {'range': [0.7, 1], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': confidence
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def create_bias_radar_chart(bias_data: Dict[str, Any]) -> go.Figure:
    """Create a radar chart for bias analysis"""
    categories = ['Factual Density', 'Objectivity', 'Emotional Neutrality', 'Balance', 'Credibility']
    
    # Convert bias data to radar metrics
    factual_density = bias_data.get('factual_density', 0.5)
    objectivity = 1 - bias_data.get('opinion_ratio', 0.5)
    emotional_neutrality = 0 if bias_data.get('emotional_language', False) else 1
    balance = bias_data.get('bias_confidence', 0.5)
    credibility = 0.8  # Placeholder - could be enhanced
    
    values = [factual_density, objectivity, emotional_neutrality, balance, credibility]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Content Analysis',
        line_color='blue'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=True,
        title="Content Quality Metrics",
        height=400
    )
    
    return fig

def create_source_credibility_chart(source_data: Dict[str, Any]) -> go.Figure:
    """Create a bar chart for source credibility"""
    sources = source_data.get('sources', [])
    
    if not sources:
        fig = go.Figure()
        fig.add_annotation(text="No source data available", x=0.5, y=0.5, showarrow=False)
        return fig
    
    domains = [s.get('domain', 'Unknown') for s in sources]
    scores = [s.get('credibility_score', 0) for s in sources]
    
    # Color code based on credibility
    colors = ['red' if score < 6 else 'orange' if score < 8 else 'green' for score in scores]
    
    fig = go.Figure(data=[
        go.Bar(x=domains, y=scores, marker_color=colors)
    ])
    
    fig.update_layout(
        title="Source Credibility Scores",
        xaxis_title="News Sources",
        yaxis_title="Credibility Score (0-10)",
        height=400,
        xaxis_tickangle=-45
    )
    
    return fig

def create_topic_distribution(entities: Dict[str, Any]) -> go.Figure:
    """Create a pie chart for topic distribution"""
    topics = entities.get('topics', [])
    
    if not topics:
        fig = go.Figure()
        fig.add_annotation(text="No topics identified", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Count topic frequency (simplified - in real app, you'd use more sophisticated analysis)
    topic_counts = {topic: len(topic.split()) for topic in topics[:8]}  # Limit to top 8
    
    fig = go.Figure(data=[go.Pie(
        labels=list(topic_counts.keys()), 
        values=list(topic_counts.values()),
        hole=.3
    )])
    
    fig.update_layout(
        title="Topic Distribution",
        height=400,
        annotations=[dict(text='Topics', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    
    return fig

def create_content_similarity_heatmap(content_analysis: Dict[str, Any]) -> go.Figure:
    """Create a heatmap showing content similarity between sources"""
    similarity_matrix = content_analysis.get('similarity_matrix', [])
    
    if not similarity_matrix:
        fig = go.Figure()
        fig.add_annotation(text="Similarity analysis not available", x=0.5, y=0.5, showarrow=False)
        return fig
    
    source_labels = [f"Source {i+1}" for i in range(len(similarity_matrix))]
    
    fig = go.Figure(data=go.Heatmap(
        z=similarity_matrix,
        x=source_labels,
        y=source_labels,
        colorscale='RdYlBu_r',
        zmin=0,
        zmax=1
    ))
    
    fig.update_layout(
        title="Content Similarity Matrix",
        height=400,
        xaxis_title="Sources",
        yaxis_title="Sources"
    )
    
    return fig

def display_analytics_dashboard(result: Dict[str, Any]):
    """Display the comprehensive analytics dashboard"""
    
    st.markdown("## 📊 News Intelligence Dashboard")
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Sources Analyzed", 
            result["source_analysis"].get("successful_loads", 0),
            delta=f"{result['source_analysis'].get('total_sources', 0)} total"
        )
    
    with col2:
        avg_cred = result["source_analysis"].get("avg_credibility", 0)
        st.metric(
            "Avg Source Credibility", 
            f"{avg_cred}/10",
            delta="High" if avg_cred > 8 else "Medium" if avg_cred > 6 else "Low"
        )
    
    with col3:
        unique_ratio = result["content_analysis"].get("unique_content_ratio", 0)
        st.metric(
            "Content Uniqueness", 
            f"{int(unique_ratio * 100)}%",
            delta="High" if unique_ratio > 0.7 else "Medium" if unique_ratio > 0.4 else "Low"
        )
    
    with col4:
        sentiment = result["sentiment_analysis"].get("overall_sentiment", "Unknown")
        confidence = result["sentiment_analysis"].get("confidence", 0)
        st.metric(
            "Sentiment Confidence", 
            f"{int(confidence * 100)}%",
            delta=sentiment
        )
    
    # Charts Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            create_sentiment_gauge(result["sentiment_analysis"]), 
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(
            create_bias_radar_chart(result["bias_analysis"]), 
            use_container_width=True
        )
    
    # Charts Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            create_source_credibility_chart(result["source_analysis"]), 
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(
            create_topic_distribution(result["entities"]), 
            use_container_width=True
        )
    
    # Content Similarity (Full Width)
    if len(result["source_analysis"].get("sources", [])) > 1:
        st.plotly_chart(
            create_content_similarity_heatmap(result["content_analysis"]), 
            use_container_width=True
        )
    
    # Detailed Analysis Sections
    with st.expander("🔍 Detailed Entity Analysis"):
        entities = result["entities"]
        
        if entities.get("people"):
            st.markdown("**Key People:**")
            st.write(", ".join(entities["people"][:10]))
        
        if entities.get("organizations"):
            st.markdown("**Organizations:**")
            st.write(", ".join(entities["organizations"][:10]))
        
        if entities.get("locations"):
            st.markdown("**Locations:**")
            st.write(", ".join(entities["locations"][:10]))
        
        if entities.get("key_numbers"):
            st.markdown("**Key Statistics:**")
            for stat in entities["key_numbers"][:5]:
                st.write(f"• {stat}")
    
    with st.expander("⚖️ Bias & Quality Analysis"):
        bias = result["bias_analysis"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Content Characteristics:**")
            st.write(f"• Political Lean: {bias.get('political_bias', 'Unknown')}")
            st.write(f"• Tone: {bias.get('tone', 'Unknown')}")
            st.write(f"• Emotional Language: {'Yes' if bias.get('emotional_language', False) else 'No'}")
        
        with col2:
            st.markdown("**Quality Metrics:**")
            st.write(f"• Factual Density: {int(bias.get('factual_density', 0) * 100)}%")
            st.write(f"• Opinion Ratio: {int(bias.get('opinion_ratio', 0) * 100)}%")
            st.write(f"• Analysis Confidence: {int(bias.get('bias_confidence', 0) * 100)}%")
    
    with st.expander("📋 Source Details"):
        sources = result["source_analysis"].get("sources", [])
        for i, source in enumerate(sources, 1):
            with st.container():
                st.markdown(f"**Source {i}: {source.get('domain', 'Unknown')}**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"Credibility: {source.get('credibility_score', 0)}/10")
                with col2:
                    st.write(f"Content Length: {source.get('content_length', 0):,} chars")
                with col3:
                    if source.get('error'):
                        st.error(f"Error: {source['error']}")
                    else:
                        st.success("✅ Loaded successfully")

def main():
    """Enhanced Streamlit application with analytics dashboard"""
    
    # Set page configuration
    st.set_page_config(
        page_title="Smart News Analyzer",
        page_icon="🧠",
        layout="wide"
    )

    # Enhanced header
    st.title("🧠 Smart News Analyzer")
    st.markdown("""
    Advanced news analysis platform with AI-powered insights, bias detection, and interactive visualizations.
    Get comprehensive intelligence from multiple news sources.
    """)

    # Initialize the enhanced analyzer
    analyzer = NewsAnalyzer()

    # Sidebar for advanced options
    with st.sidebar:
        st.header("⚙️ Analysis Settings")
        
        summary_length = st.selectbox(
            "Summary Length",
            ("Brief", "Standard", "Detailed"),
            index=1
        )
        
        st.markdown("---")
        st.markdown("**Analysis Features:**")
        st.markdown("✅ Smart Content Analysis")
        st.markdown("✅ Bias Detection")
        st.markdown("✅ Source Credibility")
        st.markdown("✅ Entity Extraction")
        st.markdown("✅ Sentiment Analysis")
        st.markdown("✅ Duplicate Detection")

    # Main input form
    with st.form("url_form"):
        st.markdown("### 📰 News Sources")
        urls = []
        
        # Allow up to 5 URL inputs with better UX
        for i in range(5):
            url = st.text_input(
                f"News Article URL #{i+1}", 
                key=f"url_{i}",
                placeholder="https://example.com/news-article"
            )
            if url:
                urls.append(url)
        
        # Enhanced submit button
        submitted = st.form_submit_button(
            "🚀 Analyze News", 
            type="primary",
            use_container_width=True
        )

    # Process form submission
    if submitted and urls:
        with st.spinner("🔄 Analyzing news articles and generating insights..."):
            # Generate comprehensive analysis
            result = analyzer.analyze_news(urls, summary_length=summary_length)
            
            # Display errors if any
            if result["errors"]:
                st.error("⚠️ Some issues occurred during analysis:")
                for error in result["errors"]:
                    st.error(f"• {error}")
            
            # Display results if available
            if result["summary"]:
                # Display analytics dashboard first
                display_analytics_dashboard(result)
                
                st.markdown("---")
                
                # Display the summary
                st.markdown("## 📄 Generated News Summary")
                
                # Keywords bar
                if result["keywords"]:
                    st.markdown("**🏷️ Key Topics:** " + " • ".join([f"`{kw}`" for kw in result["keywords"][:10]]))
                
                # Sentiment indicator
                sentiment = result["sentiment_analysis"].get("overall_sentiment", "Unknown")
                confidence = result["sentiment_analysis"].get("confidence", 0)
                sentiment_emoji = {
                    "Positive": "😊", "Negative": "😔", "Neutral": "😐", "Mixed": "☯️"
                }.get(sentiment, "❓")
                
                st.markdown(f"**🎭 Overall Sentiment:** {sentiment} {sentiment_emoji} (Confidence: {int(confidence * 100)}%)")
                
                st.markdown("---")
                
                # Display the actual summary
                st.markdown(result["summary"])
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Download summary
                    st.download_button(
                        label="📥 Download Summary",
                        data=result["summary"],
                        file_name=f"news_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                with col2:
                    # Download full analysis (JSON)
                    import json
                    analysis_json = json.dumps(result, indent=2, default=str)
                    st.download_button(
                        label="📊 Download Analysis",
                        data=analysis_json,
                        file_name=f"full_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                with col3:
                    # Share button (placeholder for future implementation)
                    if st.button("🔗 Share Results", use_container_width=True):
                        st.info("Share functionality coming soon!")
                
                # Quality indicators
                st.markdown("---")
                st.markdown("### 📋 Analysis Summary")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.info(f"""
                    **Content Quality**
                    - Sources: {result['source_analysis'].get('successful_loads', 0)}/{result['source_analysis'].get('total_sources', 0)}
                    - Avg Credibility: {result['source_analysis'].get('avg_credibility', 0)}/10
                    - Uniqueness: {int(result['content_analysis'].get('unique_content_ratio', 0) * 100)}%
                    """)
                
                with col2:
                    bias = result['bias_analysis']
                    st.info(f"""
                    **Content Analysis**
                    - Political Lean: {bias.get('political_bias', 'Unknown')}
                    - Tone: {bias.get('tone', 'Unknown')}
                    - Factual Density: {int(bias.get('factual_density', 0) * 100)}%
                    """)
                
                with col3:
                    entities = result['entities']
                    people_count = len(entities.get('people', []))
                    orgs_count = len(entities.get('organizations', []))
                    locations_count = len(entities.get('locations', []))
                    
                    st.info(f"""
                    **Entities Identified**
                    - People: {people_count}
                    - Organizations: {orgs_count}
                    - Locations: {locations_count}
                    """)
                
            else:
                st.error("❌ No content could be extracted or processed from the provided URLs.")
                
                # Show diagnostic information
                if result["source_analysis"].get("sources"):
                    st.markdown("### 🔍 Diagnostic Information")
                    for source in result["source_analysis"]["sources"]:
                        if source.get("error"):
                            st.error(f"**{source['domain']}**: {source['error']}")
                        else:
                            st.warning(f"**{source['domain']}**: Content loaded but processing failed")
                
    elif submitted:
        st.warning("⚠️ Please enter at least one URL to analyze.")

    # Enhanced instructions
    with st.expander("📖 How to Use the Smart News Analyzer"):
        st.markdown("""
        ### Getting Started
        1. **Enter URLs**: Add up to 5 news article URLs from different sources
        2. **Choose Length**: Select your preferred summary length (Brief/Standard/Detailed)
        3. **Analyze**: Click "Analyze News" to generate comprehensive insights
        
        ### What You'll Get
        
        #### 📊 **Interactive Dashboard**
        - **Sentiment Analysis**: Gauge showing overall emotional tone
        - **Bias Detection**: Radar chart revealing content objectivity
        - **Source Credibility**: Bar chart rating news source reliability
        - **Topic Distribution**: Pie chart of key themes covered
        - **Content Similarity**: Heatmap showing overlap between sources
        
        #### 🔍 **Smart Analysis Features**
        - **Entity Extraction**: Automatic identification of people, organizations, locations
        - **Duplicate Detection**: Identifies overlapping content across sources
        - **Quality Metrics**: Factual density, opinion ratio, emotional language detection
        - **Political Bias**: Left/Center/Right lean analysis with confidence scores
        
        #### 📄 **Enhanced Summary**
        - **Executive Summary**: Key takeaways at a glance  
        - **Multiple Perspectives**: Balanced view from different sources
        - **Critical Insights**: Analysis of implications and significance
        - **Future Watch**: What developments to monitor next
        
        ### Tips for Best Results
        - Use diverse, reputable news sources for balanced analysis
        - Include both primary sources and analysis pieces
        - Mix local and international perspectives when relevant
        - Check source credibility scores in the dashboard
        
        ### Understanding the Metrics
        - **Credibility Score**: 0-10 scale based on source reputation
        - **Content Uniqueness**: Percentage of non-duplicate information
        - **Sentiment Confidence**: How certain the AI is about emotional tone
        - **Factual Density**: Ratio of facts vs. opinions in content
        - **Bias Confidence**: Certainty level of political lean detection
        """)
    
    # Footer with additional info
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🛡️ Source Credibility**")
        st.caption("Automatic scoring based on journalism standards and reputation")
    
    with col2:
        st.markdown("**🎯 Bias Detection**")
        st.caption("AI-powered analysis of political lean and editorial tone")
    
    with col3:
        st.markdown("**📈 Smart Analytics**")
        st.caption("Interactive visualizations for deeper content insights")

if __name__ == "__main__":
    main()
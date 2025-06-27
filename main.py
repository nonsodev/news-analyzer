# main.py - Enhanced News Analyzer with Smart Content Analysis

import os
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Any, Tuple
import json
import re
from datetime import datetime
from urllib.parse import urlparse
import streamlit as st

# For Gemini via OpenAI client
from openai import OpenAI

# Load Google API Key from environment
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]


class NewsAnalyzer:
    """Enhanced news analyzer with smart content analysis capabilities"""
    
    def __init__(self, model_name="gemini-2.5-flash", temperature=0.5):
        """Initialize the news analyzer with specified model parameters"""
        self.llm = OpenAI(
            api_key=GOOGLE_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        self.model_name = model_name
        self.temperature = temperature
        
        # Source credibility database (expandable)
        self.credibility_scores = {
            'reuters.com': 9.5, 'ap.org': 9.4, 'bbc.com': 9.2, 'npr.org': 9.0,
            'pbs.org': 8.8, 'wsj.com': 8.7, 'nytimes.com': 8.5, 'washingtonpost.com': 8.3,
            'theguardian.com': 8.2, 'economist.com': 8.0, 'cnn.com': 7.5, 'foxnews.com': 7.0,
            'nbcnews.com': 7.8, 'abcnews.go.com': 7.7, 'cbsnews.com': 7.6, 'usatoday.com': 7.2
        }
    
    def load_articles(self, urls: List[str]) -> Tuple[List[Dict], List[str], List[Dict]]:
        """
        Load and process content from multiple URLs with metadata extraction
        
        Args:
            urls: List of URLs to process
            
        Returns:
            Tuple containing list of documents, list of errors, and list of source metadata
        """
        all_docs = []
        errors = []
        source_metadata = []
       
        for url in urls:
            if url.strip():
                try:
                    loader = WebBaseLoader(url)
                    docs = loader.load()
                    all_docs.extend(docs)
                    
                    # Extract source metadata
                    domain = urlparse(url).netloc.lower()
                    credibility = self.credibility_scores.get(domain, 6.0)  # Default score
                    
                    source_metadata.append({
                        'url': url,
                        'domain': domain,
                        'credibility_score': credibility,
                        'content_length': len(docs[0].page_content) if docs else 0,
                        'load_time': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    errors.append(f"Error loading {url}: {str(e)}")
                    # Still add metadata for failed loads
                    domain = urlparse(url).netloc.lower()
                    source_metadata.append({
                        'url': url,
                        'domain': domain,
                        'credibility_score': 0,
                        'content_length': 0,
                        'load_time': datetime.now().isoformat(),
                        'error': str(e)
                    })
        
        return all_docs, errors, source_metadata

    def _call_gemini_with_prompt(self, prompt_content: str) -> str:
        """Helper to call Gemini and get the content."""
        response = self.llm.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt_content}
            ],
            temperature=self.temperature
        )
        return response.choices[0].message.content
    
    def analyze_bias_and_tone(self, text: str) -> Dict[str, Any]:
        """
        Analyze bias and tone of the content using Gemini
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with bias and tone analysis
        """
        bias_prompt = f"""
        Analyze the following news content for bias and tone. Provide your analysis in the following JSON format:
        {{
            "political_bias": "Left/Center-Left/Center/Center-Right/Right/Unknown",
            "bias_confidence": 0.0-1.0,
            "tone": "Objective/Sensational/Alarmist/Optimistic/Pessimistic/Neutral",
            "emotional_language": true/false,
            "factual_density": 0.0-1.0,
            "opinion_ratio": 0.0-1.0
        }}
        
        Content to analyze:
        {text[:2000]}...
        """
        
        try:
            response = self._call_gemini_with_prompt(bias_prompt)
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._default_bias_analysis()
        except Exception as e:
            return self._default_bias_analysis()
    
    def _default_bias_analysis(self) -> Dict[str, Any]:
        """Return default bias analysis when parsing fails"""
        return {
            "political_bias": "Unknown",
            "bias_confidence": 0.0,
            "tone": "Neutral",
            "emotional_language": False,
            "factual_density": 0.5,
            "opinion_ratio": 0.5
        }
    
    def extract_entities_and_topics(self, text: str) -> Dict[str, Any]:
        """
        Extract entities, topics, and themes from the text
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with extracted entities and topics
        """
        entity_prompt = f"""
        Extract key information from the following news content. Provide your analysis in JSON format:
        {{
            "people": ["list of key people mentioned"],
            "organizations": ["list of organizations/companies"],
            "locations": ["list of places/countries"],
            "topics": ["list of main topics/themes"],
            "events": ["list of key events mentioned"],
            "dates": ["list of important dates"],
            "key_numbers": ["list of significant statistics/numbers with context"]
        }}
        
        Content:
        {text[:2000]}...
        """
        
        try:
            response = self._call_gemini_with_prompt(entity_prompt)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._default_entities()
        except Exception as e:
            return self._default_entities()
    
    def _default_entities(self) -> Dict[str, Any]:
        """Return default entity analysis when parsing fails"""
        return {
            "people": [],
            "organizations": [],
            "locations": [],
            "topics": [],
            "events": [],
            "dates": [],
            "key_numbers": []
        }
    
    def detect_duplicate_content(self, docs: List[Dict]) -> Dict[str, Any]:
        """
        Detect duplicate or highly similar content across sources
        
        Args:
            docs: List of document objects
            
        Returns:
            Dictionary with duplicate content analysis
        """
        if len(docs) < 2:
            return {"duplicates_found": False, "similarity_matrix": [], "unique_content_ratio": 1.0}
        
        # Simple similarity detection using overlapping sentences
        contents = [doc.page_content for doc in docs]
        similarity_matrix = []
        
        for i, content1 in enumerate(contents):
            row = []
            sentences1 = set(sent.strip().lower() for sent in content1.split('.') if len(sent.strip()) > 20)
            
            for j, content2 in enumerate(contents):
                if i == j:
                    row.append(1.0)
                else:
                    sentences2 = set(sent.strip().lower() for sent in content2.split('.') if len(sent.strip()) > 20)
                    if sentences1 and sentences2:
                        similarity = len(sentences1.intersection(sentences2)) / len(sentences1.union(sentences2))
                        row.append(round(similarity, 2))
                    else:
                        row.append(0.0)
            similarity_matrix.append(row)
        
        # Calculate overall uniqueness
        avg_similarity = sum(sum(row) for row in similarity_matrix) / (len(similarity_matrix) ** 2)
        unique_content_ratio = max(0.0, 1.0 - (avg_similarity - 1.0) / (len(docs) - 1))
        
        return {
            "duplicates_found": any(sim > 0.7 for row in similarity_matrix for sim in row if sim < 1.0),
            "similarity_matrix": similarity_matrix,
            "unique_content_ratio": round(unique_content_ratio, 2)
        }
    
    def create_summary_prompt(self, docs: List[Dict], summary_length: str = "Standard") -> str:
        """Create enhanced summary prompt with analysis integration"""
        length_instruction = ""
        if summary_length == "Brief":
            length_instruction = "Keep the summary concise and to the point, focusing only on the most critical information. Aim for around 150-200 words total."
        elif summary_length == "Detailed":
            length_instruction = "Provide a comprehensive and detailed summary, including all relevant nuances and background information. Aim for at least 500 words total."
        else:
            length_instruction = "Provide a standard length summary, covering key aspects of each news item. Aim for around 300-400 words total."
        
        summary_template = f"""
        You are a professional news editor and journalist. Create a comprehensive news summary that incorporates multiple perspectives and highlights key insights. {length_instruction}
        
        SOURCES:
        {{context}}
        
        Format your response as follows:
        
        ## Executive Summary
        A compelling 2-3 sentence overview of the main story and its significance.
        
        ## Key Developments
        
        ### Primary Story: [Catchy Title]
        Main narrative with important details and context.
        
        ### Related Developments: [If applicable]
        Supporting stories or related news items.
        
        ## Critical Insights
        - Key takeaways and implications
        - Different perspectives or viewpoints presented
        - Potential impact or consequences
        
        ## What to Watch
        Future developments or follow-up items to monitor.
        """
        
        prompt = PromptTemplate.from_template(summary_template)
        context = "\n\n".join([doc.page_content for doc in docs])
        return prompt.format(context=context)

    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords with enhanced categorization"""
        keyword_prompt = f"""
        Extract up to 15 relevant keywords and key phrases from the following news summary.
        Focus on: names, organizations, locations, events, and important concepts.
        Provide them as a comma-separated list, ordered by importance.
        
        SUMMARY:
        {text}
        
        KEYWORDS:
        """
        
        try:
            response_content = self._call_gemini_with_prompt(keyword_prompt)
            keywords = [k.strip() for k in response_content.split(',') if k.strip()]
            return keywords[:15]  # Limit to 15 keywords
        except Exception as e:
            return []

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Enhanced sentiment analysis with confidence scores"""
        sentiment_prompt = f"""
        Analyze the sentiment of the following news summary. Provide your analysis in JSON format:
        {{
            "overall_sentiment": "Positive/Negative/Neutral/Mixed",
            "confidence": 0.0-1.0,
            "emotional_intensity": 0.0-1.0,
            "sentiment_breakdown": {{
                "positive_aspects": ["list of positive elements"],
                "negative_aspects": ["list of negative elements"],
                "neutral_aspects": ["list of neutral elements"]
            }}
        }}
        
        SUMMARY:
        {text}
        """
        
        try:
            response_content = self._call_gemini_with_prompt(sentiment_prompt)
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"overall_sentiment": "Neutral", "confidence": 0.5, "emotional_intensity": 0.5, "sentiment_breakdown": {"positive_aspects": [], "negative_aspects": [], "neutral_aspects": []}}
        except Exception as e:
            return {"overall_sentiment": "Analysis Failed", "confidence": 0.0, "emotional_intensity": 0.0, "sentiment_breakdown": {"positive_aspects": [], "negative_aspects": [], "neutral_aspects": []}}
            
    def analyze_news(self, urls: List[str], summary_length: str = "Standard") -> Dict[str, Any]:
        """
        Comprehensive news analysis with smart content analysis
        
        Args:
            urls: List of URLs to news articles
            summary_length: Desired length of the summary
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        result = {
            "summary": None,
            "keywords": [],
            "sentiment_analysis": {},
            "bias_analysis": {},
            "entities": {},
            "source_analysis": {},
            "content_analysis": {},
            "errors": []
        }
        
        # Load articles with metadata
        docs, errors, source_metadata = self.load_articles(urls)
        result["errors"] = errors
        result["source_analysis"] = {
            "sources": source_metadata,
            "avg_credibility": round(sum(s.get('credibility_score', 0) for s in source_metadata) / len(source_metadata), 1) if source_metadata else 0,
            "total_sources": len(source_metadata),
            "successful_loads": len([s for s in source_metadata if s.get('content_length', 0) > 0])
        }
        
        if docs:
            try:
                # Generate summary
                prompt_content = self.create_summary_prompt(docs, summary_length)
                summary = self._call_gemini_with_prompt(prompt_content)
                result["summary"] = summary

                if summary:
                    # Extract keywords
                    result["keywords"] = self.extract_keywords(summary)
                    
                    # Analyze sentiment
                    result["sentiment_analysis"] = self.analyze_sentiment(summary)
                    
                    # Analyze bias and tone
                    full_content = "\n\n".join([doc.page_content for doc in docs])
                    result["bias_analysis"] = self.analyze_bias_and_tone(full_content)
                    
                    # Extract entities
                    result["entities"] = self.extract_entities_and_topics(full_content)
                    
                    # Analyze content duplication
                    result["content_analysis"] = self.detect_duplicate_content(docs)

            except Exception as e:
                result["errors"].append(f"Analysis error: {str(e)}")
        
        return result

# Maintain backward compatibility
NewsSummarizer = NewsAnalyzer
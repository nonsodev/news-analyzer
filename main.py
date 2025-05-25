# news_summarizer.py - Core functionality module

import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Any, Tuple

# Load environment variables
load_dotenv()

class NewsSummarizer:
    """Core class for loading and summarizing news articles"""
    
    def __init__(self, model_name="gpt-4o", temperature=0.5):
        """Initialize the news summarizer with specified model parameters"""
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature
        )
    
    def load_articles(self, urls: List[str]) -> Tuple[List[Dict], List[str]]:
        """
        Load and process content from multiple URLs
        
        Args:
            urls: List of URLs to process
            
        Returns:
            Tuple containing list of document splits and list of error messages
        """
        all_docs = []
        errors = []
       
        for url in urls:
            if url.strip():  # Skip empty URLs
                try:
                    loader = WebBaseLoader(url)
                    docs = loader.load()
                    all_docs.extend(docs)
                except Exception as e:
                    errors.append(f"Error loading {url}: {str(e)}")
        
        # Split documents into chunks if documents were loaded
        if all_docs:
            return all_docs, errors
        else:
            return [], errors
    
    def create_summary_chain(self):
        """Create the LangChain chain for summarizing news articles"""
        # Create the summary template
        summary_template = """
        You are a professional news editor and journalist. Your task is to create news articles based on the following sources
        SOURCES:
        {context}
        it should be formatted like this:
        sub heading: a comprehensive sentence that highlights in an enticing way what happened in all the news sources, should not be more than two lines
        news 1 - some title:
        The news summarized with important parts highlighted
        news 1 - some title:
        The news summarized with important parts highlighted
        """
        
        # Create prompt from template
        prompt = PromptTemplate.from_template(summary_template)
        
        # Create chain
        chain = (
            {"context": lambda docs: "\n\n".join([doc.page_content for doc in docs])}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return chain
    
    def summarize(self, urls: List[str]) -> Dict[str, Any]:
        """
        Generate a news summary from the provided URLs
        
        Args:
            urls: List of URLs to news articles
            
        Returns:
            Dictionary with summary and errors
        """
        result = {
            "summary": None,
            "errors": []
        }
        

        docs, errors = self.load_articles(urls)
        result["errors"] = errors
        
        if docs:
            try:
                # Create and run the chain
                chain = self.create_summary_chain()
                summary = chain.invoke(docs)
                result["summary"] = summary
            except Exception as e:
                result["errors"].append(f"Summarization error: {str(e)}")
        
        return result
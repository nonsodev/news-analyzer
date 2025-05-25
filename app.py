# app.py - Streamlit application

import streamlit as st
from main import NewsSummarizer
from typing import List

def main():
    """Main Streamlit application function"""
    # Set page configuration
    st.set_page_config(
        page_title="News Summarizer",
        page_icon="📰",
        layout="wide"
    )

    # Create the app header
    st.title("📰 News Summarizer")
    st.markdown("""
    This app allows you to input links to multiple news articles and generates a consolidated summary in a proper news format.
    """)

    # Initialize the news summarizer
    summarizer = NewsSummarizer()

    # Create the Streamlit interface
    with st.form("url_form"):
        urls = []
        
        # Allow up to 5 URL inputs
        for i in range(5):
            url = st.text_input(f"News article URL #{i+1}", key=f"url_{i}")
            if url:
                urls.append(url)
        
        # Submit button
        submitted = st.form_submit_button("Generate Summary")

    # Process form submission
    if submitted and urls:
        with st.spinner("Processing news articles..."):
            # Generate summary
            result = summarizer.summarize(urls)
            
            # Display status messages for each URL
            if result["errors"]:
                for error in result["errors"]:
                    st.error(f"❌ {error}")
            
            # Display the summary if available
            if result["summary"]:
                st.markdown("## Generated News Summary")
                st.markdown(result["summary"])
                
                # Add download button
                st.download_button(
                    label="Download Summary",
                    data=result["summary"],
                    file_name="news_summary.md",
                    mime="text/markdown"
                )
            else:
                st.error("No content could be extracted or processed from the provided URLs.")
    elif submitted:
        st.warning("Please enter at least one URL.")

    # Add instructions at the bottom
    with st.expander("How to use this app"):
        st.markdown("""
        1. Enter the URLs of news articles you want to summarize (up to 5)
        2. Click "Generate Summary" to process the articles
        3. The app will create a consolidated news article based on all sources
        4. You can download the generated summary as a markdown file
        
        **Note:** The summary is formatted in the standard inverted pyramid structure:
        * **Headline:** A concise and attention-grabbing title
        * **Byline:** "AI News Summarizer"
        * **Lead:** Opening paragraph with the most crucial information (who, what, when, where, why, how)
        * **Body:** Additional details, context, and background information
        * **Ending:** Concluding thought or future implications
        """)

if __name__ == "__main__":
    main()
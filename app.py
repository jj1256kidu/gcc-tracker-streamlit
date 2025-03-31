import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import quote_plus
import time

# Page Configuration
st.set_page_config(
    page_title="GCC Tracker",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .company-info {
        padding: 20px;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        margin: 10px 0;
        background-color: #f8f9fa;
    }
    .person-card {
        padding: 15px;
        border: 1px solid #f0f0f0;
        border-radius: 5px;
        margin: 5px 0;
        background-color: white;
    }
    .search-result {
        margin: 10px 0;
        padding: 10px;
        border-left: 3px solid #007bff;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def search_company_info(company_name):
    """Search company information using DuckDuckGo"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Search for company website and LinkedIn
        search_query = quote_plus(f"{company_name} company website linkedin")
        url = f"https://api.duckduckgo.com/?q={search_query}&format=json"
        response = requests.get(url)
        results = response.json()

        company_info = {
            'name': company_name,
            'website': None,
            'linkedin_url': None,
            'description': None,
            'locations': []
        }

        # Process search results
        if 'Results' in results:
            for result in results['Results']:
                if not company_info['website'] and 'company' in result['FirstURL'].lower():
                    company_info['website'] = result['FirstURL']
                if not company_info['linkedin_url'] and 'linkedin.com/company' in result['FirstURL'].lower():
                    company_info['linkedin_url'] = result['FirstURL']

        # Get additional info from Wikipedia if available
        if 'Abstract' in results and results['Abstract']:
            company_info['description'] = results['Abstract']

        return company_info

    except Exception as e:
        st.error(f"Error searching company: {str(e)}")
        return None

@st.cache_data(ttl=3600)
def search_people(company_name):
    """Search key people using DuckDuckGo"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        search_query = quote_plus(f"{company_name} CEO CTO CFO linkedin")
        url = f"https://api.duckduckgo.com/?q={search_query}&format=json"
        response = requests.get(url)
        results = response.json()

        people = []
        if 'Results' in results:
            for result in results['Results']:
                if 'linkedin.com/in/' in result['FirstURL'].lower():
                    person = {
                        'name': result.get('Text', '').split('-')[0].strip(),
                        'title': result.get('Text', '').split('-')[1].strip() if '-' in result.get('Text', '') else '',
                        'linkedin_url': result['FirstURL']
                    }
                    people.append(person)

        return people[:5]  # Return top 5 results

    except Exception as e:
        st.error(f"Error searching people: {str(e)}")
        return []

def main():
    st.title("🏢 GCC Company Search")
    
    # Search bar
    col1, col2 = st.columns([3, 1])
    with col1:
        company_name = st.text_input("Enter company name", placeholder="Example: Microsoft, Google, etc.")
    with col2:
        st.write("")
        st.write("")
        search_button = st.button("🔍 Search")
    
    if company_name and search_button:
        # Create tabs
        tab1, tab2 = st.tabs(["Company Info", "Key People"])
        
        with tab1:
            with st.spinner('Searching company information...'):
                company_info = search_company_info(company_name)
                
                if company_info:
                    st.markdown(f"""
                    <div class="company-info">
                        <h2>{company_info['name']}</h2>
                        <p><strong>🌐 Website:</strong> <a href="{company_info['website']}" target="_blank">{company_info['website']}</a></p>
                        <p><strong>👥 LinkedIn:</strong> <a href="{company_info['linkedin_url']}" target="_blank">{company_info['linkedin_url']}</a></p>
                        <p><strong>📝 Description:</strong> {company_info['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("No company information found")
        
        with tab2:
            with st.spinner('Searching key people...'):
                people = search_people(company_name)
                
                if people:
                    for person in people:
                        st.markdown(f"""
                        <div class="person-card">
                            <h3>{person['name']}</h3>
                            <p><strong>🎯 Title:</strong> {person['title']}</p>
                            <p><strong>🔗 LinkedIn:</strong> <a href="{person['linkedin_url']}" target="_blank">View Profile</a></p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No key people information found")

    # Add information about usage
    with st.expander("ℹ️ How to use"):
        st.markdown("""
        1. Enter the company name in the search bar
        2. Click the Search button
        3. View company information in the 'Company Info' tab
        4. View key people information in the 'Key People' tab
        
        Note: The search results are cached for 1 hour to improve performance.
        """)

if __name__ == "__main__":
    main()

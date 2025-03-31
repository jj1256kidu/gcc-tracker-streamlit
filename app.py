import streamlit as st
import pandas as pd
import requests
import concurrent.futures
from urllib.parse import quote_plus
import time
import re

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
    .exec-card {
        background-color: white;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #ddd;
        margin: 10px 0;
    }
    .exec-card:hover {
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .role-tag {
        background-color: #e1f5fe;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
    }
    </style>
""", unsafe_allow_html=True)

# Define executive roles to search for
EXECUTIVE_ROLES = [
    'CEO', 'Chief Executive Officer',
    'CTO', 'Chief Technology Officer',
    'Founder', 'Co-Founder',
    'Director',
    'VP', 'Vice President',
    'Head',
    'Managing Director',
    'President',
    'Chairman',
    'Chief',
    'Executive'
]

# Create regex pattern for executive roles
ROLE_PATTERN = re.compile('|'.join(EXECUTIVE_ROLES), re.IGNORECASE)

@st.cache_data(ttl=1800)
def search_company_basic(company_name):
    """Quick search for basic company info"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        search_query = quote_plus(f"{company_name} company linkedin")
        response = requests.get(
            f"https://api.duckduckgo.com/?q={search_query}&format=json",
            headers=headers,
            timeout=5
        )
        data = response.json()
        
        company_info = {
            'name': company_name,
            'linkedin_url': None,
            'website': None,
            'description': data.get('Abstract', '')
        }
        
        # Extract LinkedIn and website URLs
        for result in data.get('Results', []):
            url = result.get('FirstURL', '')
            if 'linkedin.com/company' in url.lower() and not company_info['linkedin_url']:
                company_info['linkedin_url'] = url
            elif not company_info['website'] and 'linkedin.com' not in url.lower():
                company_info['website'] = url
                
        return company_info
    except Exception as e:
        st.error(f"Error in basic search: {str(e)}")
        return None

@st.cache_data(ttl=1800)
def search_executives(company_name):
    """Search for executive profiles"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Multiple search queries for different executive roles
        executives = []
        search_terms = [
            f"{company_name} CEO linkedin",
            f"{company_name} CTO linkedin",
            f"{company_name} founder linkedin",
            f"{company_name} director linkedin"
        ]
        
        def search_term(term):
            try:
                response = requests.get(
                    f"https://api.duckduckgo.com/?q={quote_plus(term)}&format=json",
                    headers=headers,
                    timeout=5
                )
                return response.json()
            except:
                return None
        
        # Use ThreadPoolExecutor for parallel searches
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            search_results = list(executor.map(search_term, search_terms))
        
        # Process results
        seen_profiles = set()  # To avoid duplicates
        for result in search_results:
            if result and 'Results' in result:
                for item in result['Results']:
                    url = item.get('FirstURL', '')
                    if 'linkedin.com/in/' in url.lower() and url not in seen_profiles:
                        text = item.get('Text', '')
                        # Check if the role matches executive positions
                        if ROLE_PATTERN.search(text):
                            name = text.split('-')[0].strip() if '-' in text else text
                            role = text.split('-')[1].strip() if '-' in text else 'Executive'
                            executives.append({
                                'name': name,
                                'role': role,
                                'linkedin_url': url
                            })
                            seen_profiles.add(url)
        
        return executives
    except Exception as e:
        st.error(f"Error in executive search: {str(e)}")
        return []

def main():
    st.title("🏢 GCC Executive Search")
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    with col1:
        company_name = st.text_input(
            "Enter company name",
            placeholder="Example: Microsoft, Google, etc."
        )
    with col2:
        st.write("")
        st.write("")
        search_button = st.button("🔍 Search")
    
    if company_name and search_button:
        # Create two columns for parallel display
        col1, col2 = st.columns([1, 1])
        
        # Use threads to search company info and executives simultaneously
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_company = executor.submit(search_company_basic, company_name)
            future_executives = executor.submit(search_executives, company_name)
            
            # Display company information
            with col1:
                with st.spinner('Loading company information...'):
                    company_info = future_company.result()
                    if company_info:
                        st.subheader("Company Information")
                        st.markdown(f"""
                        <div style="padding: 15px; border-radius: 5px; border: 1px solid #ddd;">
                            <h3>{company_info['name']}</h3>
                            <p><strong>🔗 LinkedIn:</strong> <a href="{company_info['linkedin_url']}" target="_blank">Company Profile</a></p>
                            <p><strong>🌐 Website:</strong> <a href="{company_info['website']}" target="_blank">Company Website</a></p>
                            <p><strong>📝 Description:</strong> {company_info['description']}</p>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Display executive information
            with col2:
                with st.spinner('Loading executive information...'):
                    executives = future_executives.result()
                    if executives:
                        st.subheader("Key Executives")
                        for exec in executives:
                            st.markdown(f"""
                            <div class="exec-card">
                                <h4>{exec['name']}</h4>
                                <p><span class="role-tag">{exec['role']}</span></p>
                                <p><a href="{exec['linkedin_url']}" target="_blank">View LinkedIn Profile</a></p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No executive information found")
    
    # Add usage information
    with st.expander("ℹ️ About this tool"):
        st.markdown("""
        This tool searches for:
        - Company LinkedIn profile and website
        - Key executives including:
          - CEO/Chief Executive Officer
          - CTO/Chief Technology Officer
          - Founders
          - Directors
          - VPs and Heads of Departments
          
        Results are cached for 30 minutes to improve performance.
        """)

if __name__ == "__main__":
    main()

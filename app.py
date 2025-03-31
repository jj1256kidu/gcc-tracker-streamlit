import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
from urllib.parse import quote
import subprocess
import sys

# Install required packages
def install_requirements():
    requirements = [
        'requests==2.31.0',
        'pandas==1.5.3',
        'beautifulsoup4==4.12.2',
        'lxml==4.9.3'
    ]
    for package in requirements:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Run installation
if 'packages_installed' not in st.session_state:
    install_requirements()
    st.session_state.packages_installed = True

# Page configuration
st.set_page_config(
    page_title="India Tech Center Tracker",
    page_icon="🏢",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.company-card {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
    border: 1px solid #e9ecef;
}
.person-card {
    background-color: white;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 10px;
    border: 1px solid #e9ecef;
}
.role-badge {
    background-color: #e9ecef;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    margin-right: 8px;
}
.location-badge {
    background-color: #007bff;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    margin-right: 8px;
}
</style>
""", unsafe_allow_html=True)

class CompanySearcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    @st.cache_data(ttl=3600)
    def search_company(self, company_name):
        """Search for company information"""
        try:
            search_queries = [
                f"{company_name} careers india",
                f"{company_name} office locations india",
                f"{company_name} india development center",
                f"{company_name} india tech hub",
                f"{company_name} india headquarters",
                f"{company_name} india jobs linkedin",
                f"{company_name} india engineering"
            ]
            
            company_info = {
                'name': company_name,
                'website': None,
                'linkedin': None,
                'description': None,
                'locations': set(),
                'found_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            for query in search_queries:
                url = f"https://www.google.com/search?q={quote(query)}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract links
                    for result in soup.find_all('div', {'class': 'g'}):
                        link = result.find('a')
                        if not link:
                            continue
                            
                        href = link.get('href', '')
                        
                        # Find company profiles
                        if 'linkedin.com/company' in href and not company_info['linkedin']:
                            company_info['linkedin'] = href
                        elif any(domain in href for domain in ['.com', '.in', '.co.in']):
                            if company_name.lower() in href.lower() and not company_info['website']:
                                company_info['website'] = href
                    
                    # Extract description
                    desc = soup.find('div', {'class': ['VwiC3b', 'yXK7lf']})
                    if desc and not company_info['description']:
                        text = desc.text.strip()
                        if len(text) > 100:
                            company_info['description'] = text
                    
                    # Find locations
                    city_variants = {
                        'Bangalore': ['bangalore', 'bengaluru', 'blr'],
                        'Hyderabad': ['hyderabad', 'hyd'],
                        'Pune': ['pune'],
                        'Chennai': ['chennai', 'madras'],
                        'Mumbai': ['mumbai', 'bombay'],
                        'Delhi NCR': ['delhi', 'new delhi', 'gurgaon', 'gurugram', 'noida'],
                    }
                    
                    page_text = soup.get_text().lower()
                    for city, variants in city_variants.items():
                        if any(variant in page_text for variant in variants):
                            company_info['locations'].add(city)
                
                time.sleep(1)
            
            company_info['locations'] = list(company_info['locations'])
            return company_info if company_info['linkedin'] or company_info['website'] else None
            
        except Exception as e:
            st.error(f"Error searching company: {str(e)}")
            return None

    @st.cache_data(ttl=3600)
    def search_people(self, company_name):
        """Search for company executives"""
        executives = []
        
        search_patterns = [
            f"{company_name} india managing director linkedin",
            f"{company_name} india director linkedin",
            f"{company_name} india head linkedin",
            f"{company_name} india engineering head linkedin",
            f"{company_name} india tech lead linkedin",
            f"{company_name} india engineering manager linkedin",
            f"{company_name} india vice president linkedin"
        ]
        
        try:
            for query in search_patterns:
                url = f"https://www.google.com/search?q={quote(query)}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    for result in soup.find_all('div', class_='g'):
                        link = result.find('a')
                        title = result.find('h3')
                        
                        if link and title and 'linkedin.com/in/' in link.get('href', ''):
                            text = title.text
                            if '-' in text:
                                name, position = text.split('-', 1)
                                
                                # Categorize role
                                role_category = 'Other'
                                position_lower = position.lower()
                                
                                if any(word in position_lower for word in ['director', 'managing']):
                                    role_category = 'Director'
                                elif any(word in position_lower for word in ['vp', 'vice president']):
                                    role_category = 'VP'
                                elif any(word in position_lower for word in ['head', 'leader']):
                                    role_category = 'Head'
                                elif any(word in position_lower for word in ['manager', 'lead']):
                                    role_category = 'Manager'
                                
                                # Avoid duplicates
                                if not any(e['name'].lower() == name.strip().lower() for e in executives):
                                    executives.append({
                                        'name': name.strip(),
                                        'role': position.strip(),
                                        'category': role_category,
                                        'linkedin_url': link.get('href'),
                                        'company': company_name
                                    })
                
                time.sleep(1)
            
            return pd.DataFrame(executives) if executives else pd.DataFrame()
            
        except Exception as e:
            st.error(f"Error searching people: {str(e)}")
            return pd.DataFrame()

def main():
    st.title("🏢 India Tech Center Tracker")
    
    # Initialize searcher
    searcher = CompanySearcher()
    
    # Search interface
    col1, col2 = st.columns([3,1])
    with col1:
        company_input = st.text_input(
            "Enter company name",
            placeholder="Example: Microsoft, Google, Amazon..."
        )
    with col2:
        st.write("")
        st.write("")
        search = st.button("🔍 Search")
    
    # Search tips
    with st.expander("Search Tips"):
        st.markdown("""
        - Use complete company names (e.g., "Microsoft" instead of "MS")
        - For better results, try official company names (e.g., "Accenture" instead of "Accenture India")
        - The search takes about 30-60 seconds to gather comprehensive information
        - Results are cached for 1 hour to improve performance
        """)
    
    if company_input and search:
        with st.spinner(f"Searching for {company_input}..."):
            progress = st.progress(0)
            
            # Search company info
            progress.progress(25)
            company_info = searcher.search_company(company_input)
            
            # Search people
            progress.progress(75)
            people_df = searcher.search_people(company_input)
            
            progress.progress(100)
            
            # Display results
            tab1, tab2 = st.tabs(["Company Information", "Key People"])
            
            with tab1:
                if company_info:
                    st.success("Company Information Found")
                    
                    # Company card
                    st.markdown(f"""
                    <div class="company-card">
                        <h2>{company_info['name']}</h2>
                        
                        <h4>Locations:</h4>
                        <p>{''.join([f'<span class="location-badge">{loc}</span>' for loc in company_info['locations']])}</p>
                        
                        <h4>Links:</h4>
                        <p>
                            {'<a href="' + company_info['website'] + '" target="_blank">🌐 Website</a>' if company_info['website'] else ''}
                            {' | ' if company_info['website'] and company_info['linkedin'] else ''}
                            {'<a href="' + company_info['linkedin'] + '" target="_blank">👥 LinkedIn</a>' if company_info['linkedin'] else ''}
                        </p>
                        
                        <h4>Description:</h4>
                        <p>{company_info['description'] if company_info['description'] else 'No description available'}</p>
                        
                        <small>Last updated: {company_info['found_at']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("No company information found. Try modifying your search terms.")
            
            with tab2:
                if not people_df.empty:
                    st.success(f"Found {len(people_df)} key people")
                    
                    # Filters
                    col1, col2 = st.columns(2)
                    with col1:
                        role_filter = st.selectbox(
                            "Filter by role category",
                            ['All'] + list(people_df['category'].unique())
                        )
                    
                    # Apply filters
                    filtered_df = people_df
                    if role_filter != 'All':
                        filtered_df = filtered_df[filtered_df['category'] == role_filter]
                    
                    # Display people cards
                    for _, person in filtered_df.iterrows():
                        st.markdown(f"""
                        <div class="person-card">
                            <h4>{person['name']}</h4>
                            <p>
                                <span class="role-badge">{person['category']}</span>
                                {person['role']}
                            </p>
                            <a href="{person['linkedin_url']}" target="_blank">View LinkedIn Profile</a>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No key people found. Try modifying your search terms.")

if __name__ == "__main__":
    main()

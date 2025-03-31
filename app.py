import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# Page Configuration
st.set_page_config(page_title="GCC Search", layout="wide")

# Search headers to mimic browser behavior
HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    }
]

def get_random_headers():
    return random.choice(HEADERS_LIST)

def search_linkedin(company_name):
    """Search LinkedIn for company and people"""
    base_url = "https://www.linkedin.com/company/"
    search_url = f"{base_url}{company_name.lower().replace(' ', '-')}"
    
    try:
        response = requests.get(search_url, headers=get_random_headers(), timeout=10)
        if response.status_code == 200:
            return response.url
    except:
        pass
    return None

def search_google(query):
    """Search using Google with delay and rotating headers"""
    search_url = f"https://www.google.com/search?q={query}"
    
    try:
        response = requests.get(search_url, headers=get_random_headers(), timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
    except Exception as e:
        st.error(f"Search error: {e}")
    return None

def extract_company_data(company_name):
    """Extract company information from multiple sources"""
    company_data = []
    
    # Direct LinkedIn search
    linkedin_url = search_linkedin(company_name)
    if linkedin_url:
        company_data.append({
            'Company Name': company_name,
            'LinkedIn URL': linkedin_url,
            'Source': 'LinkedIn Direct'
        })
    
    # Google search
    time.sleep(1)  # Add delay between searches
    soup = search_google(f"{company_name} gcc india linkedin")
    if soup:
        for result in soup.find_all('div', class_='g'):
            link = result.find('a')
            if link:
                href = link.get('href', '')
                if 'linkedin.com/company' in href:
                    company_data.append({
                        'Company Name': company_name,
                        'LinkedIn URL': href,
                        'Source': 'Google Search'
                    })
    
    return pd.DataFrame(company_data)

def extract_people_data(company_name):
    """Extract people information from multiple sources"""
    people_data = []
    search_terms = [
        ('CEO', 'Leadership'),
        ('CTO', 'Technology'),
        ('Director', 'Management'),
        ('Vice President', 'Executive'),
        ('Head', 'Management')
    ]
    
    for role, level in search_terms:
        time.sleep(1)  # Add delay between searches
        soup = search_google(f"{company_name} {role} india linkedin")
        if soup:
            for result in soup.find_all('div', class_='g'):
                link = result.find('a')
                title = result.find('h3')
                if link and title and 'linkedin.com/in/' in link.get('href', ''):
                    text = title.text.split('-')
                    if len(text) >= 2:
                        name = text[0].strip()
                        position = text[1].strip()
                        
                        # Avoid duplicates
                        if not any(p.get('Name') == name for p in people_data):
                            people_data.append({
                                'Name': name,
                                'Position': position,
                                'Level': level,
                                'Company': company_name,
                                'LinkedIn URL': link.get('href', ''),
                                'Found Via': role
                            })
    
    return pd.DataFrame(people_data)

def main():
    st.title("🔍 GCC Company & People Search")
    
    # Search interface
    col1, col2 = st.columns([4,1])
    with col1:
        company_name = st.text_input(
            "",
            placeholder="Enter company name (e.g., Microsoft, Google, TCS)",
            help="Enter the full company name for better results"
        )
    with col2:
        st.write("")
        st.write("")
        search = st.button("🔍 Search")
    
    if company_name and search:
        # Progress bar
        progress_bar = st.progress(0)
        
        # Search company information
        with st.spinner('Searching company information...'):
            company_df = extract_company_data(company_name)
            progress_bar.progress(50)
        
        # Search people information
        with st.spinner('Searching key people...'):
            people_df = extract_people_data(company_name)
            progress_bar.progress(100)
        
        # Display results in tabs
        tab1, tab2 = st.tabs(["🏢 Company", "👥 Key People"])
        
        with tab1:
            if not company_df.empty:
                st.success(f"Found {len(company_df)} company results")
                st.dataframe(
                    company_df,
                    column_config={
                        "LinkedIn URL": st.column_config.LinkColumn("LinkedIn Profile")
                    },
                    hide_index=True
                )
            else:
                st.warning(f"No company profile found for {company_name}. Try these tips:")
                st.info("""
                - Check the company name spelling
                - Try the parent company name
                - Add 'India' or 'GCC' to the company name
                """)
        
        with tab2:
            if not people_df.empty:
                st.success(f"Found {len(people_df)} people")
                
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    levels = ['All'] + sorted(people_df['Level'].unique().tolist())
                    level_filter = st.selectbox('Filter by Level', levels)
                
                # Apply filters
                filtered_df = people_df
                if level_filter != 'All':
                    filtered_df = filtered_df[filtered_df['Level'] == level_filter]
                
                # Display results
                st.dataframe(
                    filtered_df,
                    column_config={
                        "LinkedIn URL": st.column_config.LinkColumn("Profile"),
                        "Name": st.column_config.TextColumn(width="medium"),
                        "Position": st.column_config.TextColumn(width="large"),
                        "Level": st.column_config.TextColumn(width="small")
                    },
                    hide_index=True
                )
            else:
                st.warning(f"No key people found for {company_name}. Try these tips:")
                st.info("""
                - Use the complete company name
                - Try searching for specific roles (CEO, CTO, etc.)
                - Add location information (India, Bangalore, etc.)
                """)

    # Add search tips
    with st.expander("ℹ️ Search Tips"):
        st.markdown("""
        ### For better results:
        1. Use the complete company name
        2. Try different variations of the company name
        3. Include 'India' or 'GCC' in the search
        4. Wait for the search to complete
        5. Check both Company and People tabs
        
        ### Example searches:
        - "Microsoft India"
        - "Google India GCC"
        - "TCS Global"
        """)

if __name__ == "__main__":
    main()

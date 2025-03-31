import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import quote

# Page config
st.set_page_config(layout="wide", page_title="GCC Tracker")

# Custom headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
}

# Cache the session
if 'search_results' not in st.session_state:
    st.session_state.search_results = {}

def fetch_linkedin_data(company_name):
    """Fetch data from LinkedIn public pages"""
    encoded_name = quote(company_name)
    url = f"https://www.linkedin.com/company/{encoded_name}/about/"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
    except Exception as e:
        st.error(f"Error fetching LinkedIn data: {e}")
    return None

def fetch_company_website(company_name):
    """Fetch company website data"""
    try:
        response = requests.get(f"https://www.{company_name.lower().replace(' ', '')}.com", 
                              headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.url
    except:
        return None

def search_people(company_name):
    """Search for company executives"""
    base_url = "https://www.linkedin.com/search/results/people/"
    query = f"?keywords={quote(company_name)}%20CEO%20CTO%20Director%20VP&origin=GLOBAL_SEARCH_HEADER"
    
    try:
        response = requests.get(base_url + query, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
    except Exception as e:
        st.error(f"Error searching people: {e}")
    return None

def main():
    st.title("🌐 Live GCC Company Tracker")
    
    # Search interface
    col1, col2 = st.columns([3,1])
    with col1:
        company_name = st.text_input("Enter company name", 
                                   placeholder="e.g., Microsoft, Google, Amazon")
    with col2:
        st.write("")
        st.write("")
        search = st.button("🔍 Search")
    
    if company_name and search:
        # Create progress bar
        progress = st.progress(0)
        status = st.empty()
        
        # Initialize results
        company_data = []
        people_data = []
        
        # Fetch company data
        status.text("Searching company information...")
        progress.progress(25)
        
        # Try LinkedIn
        linkedin_data = fetch_linkedin_data(company_name)
        if linkedin_data:
            company_info = {
                'Company Name': company_name,
                'LinkedIn URL': f"https://www.linkedin.com/company/{quote(company_name)}/",
                'Website': fetch_company_website(company_name),
                'Type': 'GCC/Development Center'
            }
            company_data.append(company_info)
        
        progress.progress(50)
        status.text("Searching key people...")
        
        # Search for people
        people_soup = search_people(company_name)
        if people_soup:
            for person in people_soup.find_all('div', {'class': 'entity-result__item'}):
                name_elem = person.find('span', {'class': 'entity-result__title-text'})
                role_elem = person.find('div', {'class': 'entity-result__primary-subtitle'})
                
                if name_elem and role_elem:
                    person_info = {
                        'Name': name_elem.text.strip(),
                        'Role': role_elem.text.strip(),
                        'Company': company_name,
                        'LinkedIn URL': f"https://www.linkedin.com/in/{name_elem.text.strip().lower().replace(' ', '-')}/"
                    }
                    people_data.append(person_info)
        
        progress.progress(75)
        status.text("Processing results...")
        
        # Create DataFrames
        company_df = pd.DataFrame(company_data)
        people_df = pd.DataFrame(people_data)
        
        # Store in session state
        st.session_state.search_results[company_name] = {
            'company': company_df,
            'people': people_df,
            'timestamp': pd.Timestamp.now()
        }
        
        progress.progress(100)
        status.empty()
        
        # Display results in tabs
        tab1, tab2 = st.tabs(["Company Information", "Key People"])
        
        with tab1:
            if not company_df.empty:
                st.dataframe(
                    company_df,
                    column_config={
                        "LinkedIn URL": st.column_config.LinkColumn(),
                        "Website": st.column_config.LinkColumn()
                    },
                    hide_index=True
                )
                
                # Additional company info
                st.subheader("Recent Updates")
                st.markdown(f"""
                - Company: {company_name}
                - Location: India
                - Last Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
                """)
            else:
                st.info("No company information found. Try a different search term.")
        
        with tab2:
            if not people_df.empty:
                # Add filters
                roles = ['All'] + list(people_df['Role'].unique())
                selected_role = st.selectbox("Filter by Role", roles)
                
                # Apply filter
                if selected_role != 'All':
                    filtered_df = people_df[people_df['Role'].str.contains(selected_role, case=False)]
                else:
                    filtered_df = people_df
                
                # Display results
                st.dataframe(
                    filtered_df,
                    column_config={
                        "LinkedIn URL": st.column_config.LinkColumn("Profile"),
                        "Name": st.column_config.TextColumn(width="medium"),
                        "Role": st.column_config.TextColumn(width="large")
                    },
                    hide_index=True
                )
            else:
                st.info("No key people found. Try a different search term.")
        
        # Show search tips
        with st.expander("Search Tips"):
            st.markdown("""
            ### For better results:
            1. Use the complete company name
            2. Try adding 'India' or 'GCC' to the company name
            3. Search for major tech companies
            
            ### Example searches:
            - Microsoft India
            - Google Development Center
            - Amazon Development Center India
            """)

if __name__ == "__main__":
    main()

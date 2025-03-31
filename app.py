import streamlit as st
import subprocess
import sys
import os

# Function to install required packages
def install_dependencies():
    st.write("Installing required packages...")
    requirements = [
        'requests==2.31.0',
        'pandas==1.5.3',
        'beautifulsoup4==4.12.2',
        'fuzzywuzzy==0.18.0',
        'python-Levenshtein==0.21.1',
        'lxml==4.9.3'
    ]
    
    for package in requirements:
        try:
            st.write(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except Exception as e:
            st.error(f"Error installing {package}: {str(e)}")
            return False
    return True

# Check and install dependencies
if 'dependencies_installed' not in st.session_state:
    st.session_state.dependencies_installed = install_dependencies()

# Only proceed if dependencies are installed
if st.session_state.dependencies_installed:
    import requests
    import pandas as pd
    from bs4 import BeautifulSoup
    from fuzzywuzzy import fuzz
    from datetime import datetime
    import time
    from urllib.parse import quote
    
    # Page config
    st.set_page_config(layout="wide", page_title="Dynamic GCC Tracker")

    # Initialize session state for company database
    if 'company_database' not in st.session_state:
        st.session_state.company_database = {}

    class CompanySearcher:
        def __init__(self):
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            self.session = requests.Session()
            self.session.headers.update(self.headers)

        def search_company(self, company_name):
            """Search for company information"""
            try:
                # Search LinkedIn
                linkedin_url = f"https://www.linkedin.com/company/{quote(company_name.lower().replace(' ', '-'))}"
                company_info = {
                    'name': company_name,
                    'linkedin_url': linkedin_url,
                    'website': f"https://www.{company_name.lower().replace(' ', '')}.com",
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }

                # Search Google for additional information
                search_query = f"{company_name} company gcc india development center"
                google_url = f"https://www.google.com/search?q={quote(search_query)}"
                response = self.session.get(google_url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try to find description
                    for div in soup.find_all('div', {'class': ['VwiC3b', 'yXK7lf']}):
                        if len(div.text) > 50:
                            company_info['description'] = div.text.strip()
                            break
                
                return company_info
            except Exception as e:
                st.error(f"Error searching company: {str(e)}")
                return None

        def search_people(self, company_name):
            """Search for company executives"""
            executives = []
            search_patterns = [
                "CEO", "CTO", "Director", "VP", "Head",
                "Chief", "President", "Leader"
            ]
            
            for pattern in search_patterns:
                try:
                    search_query = f"{company_name} {pattern} india linkedin"
                    url = f"https://www.google.com/search?q={quote(search_query)}"
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
                                    
                                    # Avoid duplicates
                                    if not any(fuzz.ratio(e.get('name', ''), name.strip()) > 90 
                                             for e in executives):
                                        executives.append({
                                            'name': name.strip(),
                                            'position': position.strip(),
                                            'linkedin_url': link.get('href'),
                                            'company': company_name
                                        })
                    
                    time.sleep(1)  # Respect rate limits
                except Exception as e:
                    continue
            
            return pd.DataFrame(executives)

    def main():
        st.title("🌐 GCC Company & People Search")
        
        # Initialize searcher
        searcher = CompanySearcher()
        
        # Search interface
        col1, col2 = st.columns([3,1])
        with col1:
            company_input = st.text_input(
                "Enter company name",
                placeholder="Enter any company name (e.g., Microsoft, Google, Amazon)..."
            )
        with col2:
            st.write("")
            st.write("")
            search = st.button("🔍 Search")
        
        if company_input and search:
            with st.spinner("Searching... Please wait"):
                # Progress tracking
                progress = st.progress(0)
                
                # Search company info
                progress.progress(25)
                company_info = searcher.search_company(company_input)
                
                # Search people
                progress.progress(75)
                people_df = searcher.search_people(company_input)
                
                progress.progress(100)
                
                # Display results in tabs
                tab1, tab2 = st.tabs(["Company Information", "Key People"])
                
                with tab1:
                    if company_info:
                        st.success("Company Information Found")
                        
                        # Display company info
                        st.markdown(f"""
                        ### {company_info['name']}
                        
                        **Website:** [{company_info['website']}]({company_info['website']})  
                        **LinkedIn:** [{company_info['linkedin_url']}]({company_info['linkedin_url']})
                        
                        **Description:**  
                        {company_info.get('description', 'No description available')}
                        
                        **Last Updated:** {company_info['last_updated']}
                        """)
                    else:
                        st.warning("No company information found")
                
                with tab2:
                    if not people_df.empty:
                        st.success(f"Found {len(people_df)} key people")
                        
                        # Add filters
                        position_filter = st.text_input("Filter by position", "")
                        
                        # Apply filters
                        filtered_df = people_df
                        if position_filter:
                            filtered_df = filtered_df[
                                filtered_df['position'].str.contains(position_filter, case=False)
                            ]
                        
                        # Display results
                        st.dataframe(
                            filtered_df,
                            column_config={
                                "linkedin_url": st.column_config.LinkColumn("LinkedIn Profile")
                            },
                            hide_index=True
                        )
                    else:
                        st.warning("No key people found")

    if __name__ == "__main__":
        main()
else:
    st.error("Failed to install required dependencies. Please try again.")

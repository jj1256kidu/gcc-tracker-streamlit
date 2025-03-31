import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import json
from urllib.parse import quote
import time
import re
from datetime import datetime

# Page config
st.set_page_config(layout="wide", page_title="Dynamic GCC Tracker")

# Initialize session state for dynamic company database
if 'company_database' not in st.session_state:
    st.session_state.company_database = {}

class DynamicCompanySearcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def search_company_sources(self, company_name):
        """Search multiple sources for company information"""
        sources = [
            self.search_linkedin,
            self.search_google,
            self.search_crunchbase,
            self.search_gcc_directories
        ]
        
        company_info = {}
        for source_func in sources:
            try:
                info = source_func(company_name)
                if info:
                    company_info.update(info)
            except Exception as e:
                continue
        
        return company_info

    def search_linkedin(self, company_name):
        """Search LinkedIn for company information"""
        try:
            url = f"https://www.linkedin.com/company/{quote(company_name.lower().replace(' ', '-'))}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract company info from LinkedIn
                info = {
                    'name': company_name,
                    'linkedin_url': url,
                    'source': 'LinkedIn',
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }
                
                # Try to find additional information
                description = soup.find('section', {'class': 'description'})
                if description:
                    info['description'] = description.text.strip()
                
                return info
        except:
            return None

    def search_google(self, company_name):
        """Search Google for company information"""
        try:
            search_query = f"{company_name} company gcc india development center"
            url = f"https://www.google.com/search?q={quote(search_query)}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract information from search results
                info = {
                    'name': company_name,
                    'source': 'Google',
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }
                
                # Find company website
                for result in soup.find_all('div', class_='g'):
                    link = result.find('a')
                    if link and company_name.lower() in link.get('href', '').lower():
                        info['website'] = link.get('href')
                        break
                
                return info
        except:
            return None

    def search_gcc_directories(self, company_name):
        """Search GCC directories for company information"""
        gcc_directories = [
            "https://nasscom.in/gcc-companies",  # Example URL
            "https://www.gccdirectory.com",      # Example URL
        ]
        
        for directory in gcc_directories:
            try:
                response = self.session.get(directory, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # Extract GCC-specific information
                    # This is a placeholder for actual implementation
                    return {
                        'name': company_name,
                        'type': 'GCC',
                        'source': 'GCC Directory',
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    }
            except:
                continue
        
        return None

    def update_company_database(self, company_name, company_info):
        """Update the dynamic company database"""
        if company_info:
            st.session_state.company_database[company_name.lower()] = {
                'info': company_info,
                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                'variations': self.generate_name_variations(company_name)
            }

    def generate_name_variations(self, company_name):
        """Generate variations of company name"""
        name = company_name.lower()
        variations = [
            name,
            name.replace(' ', ''),
            name + ' india',
            name + ' gcc',
            name + ' development center'
        ]
        
        # Add common abbreviations
        words = name.split()
        if len(words) > 1:
            abbrev = ''.join(word[0] for word in words)
            variations.append(abbrev)
        
        return list(set(variations))

    def search_executives(self, company_name):
        """Search for company executives"""
        executives = []
        search_patterns = [
            "CEO", "CTO", "Director", "VP", "Head",
            "Chief", "President", "Leader", "Manager"
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
                                
                                # Avoid duplicates using fuzzy matching
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
    st.title("🌐 Dynamic GCC Company Tracker")
    
    # Initialize searcher
    searcher = DynamicCompanySearcher()
    
    # Search interface
    col1, col2 = st.columns([3,1])
    with col1:
        company_input = st.text_input(
            "Enter company name",
            placeholder="Enter any company name..."
        )
    with col2:
        st.write("")
        st.write("")
        search = st.button("🔍 Search")
    
    if company_input and search:
        with st.spinner("Searching... Please wait"):
            # Progress tracking
            progress = st.progress(0)
            
            # Search or get from database
            company_key = company_input.lower()
            if company_key in st.session_state.company_database:
                company_info = st.session_state.company_database[company_key]['info']
                st.info("Retrieved from database")
            else:
                progress.progress(25)
                company_info = searcher.search_company_sources(company_input)
                if company_info:
                    searcher.update_company_database(company_input, company_info)
            
            progress.progress(50)
            
            # Search executives
            people_df = searcher.search_executives(company_input)
            
            progress.progress(100)
            
            # Display results
            tab1, tab2, tab3 = st.tabs(["Company Info", "Key People", "Database Stats"])
            
            with tab1:
                if company_info:
                    st.success("Company Information Found")
                    # Display as JSON with formatting
                    st.json(company_info)
                else:
                    st.warning("No company information found")
            
            with tab2:
                if not people_df.empty:
                    st.success(f"Found {len(people_df)} key people")
                    st.dataframe(
                        people_df,
                        column_config={
                            "linkedin_url": st.column_config.LinkColumn("LinkedIn Profile")
                        },
                        hide_index=True
                    )
                else:
                    st.warning("No key people found")
            
            with tab3:
                st.subheader("Database Statistics")
                st.write(f"Total companies in database: {len(st.session_state.company_database)}")
                st.write("Recently searched companies:")
                for company, data in list(st.session_state.company_database.items())[-5:]:
                    st.write(f"- {company}: Last updated {data['last_updated']}")

if __name__ == "__main__":
    main()

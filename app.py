import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
import spacy
import re
from urllib.parse import quote
import time

# Load SpaCy model for entity recognition
try:
    nlp = spacy.load("en_core_web_sm")
except:
    st.warning("Installing required language model...")
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Page config
st.set_page_config(layout="wide", page_title="Smart GCC Tracker")

# Known company patterns and variations
COMPANY_PATTERNS = {
    "microsoft": [
        "Microsoft", "Microsoft India", "Microsoft IDC", 
        "Microsoft India Development Center", "Microsoft R&D"
    ],
    "google": [
        "Google", "Google India", "Google Development Center", 
        "Google IDC", "Google R&D India"
    ],
    "amazon": [
        "Amazon", "Amazon India", "Amazon Development Center", 
        "Amazon IDC", "Amazon R&D"
    ],
    # Add more companies as needed
}

# Executive role patterns
EXECUTIVE_ROLES = {
    "leadership": ["CEO", "Chief Executive", "Managing Director", "Country Head"],
    "technology": ["CTO", "Chief Technology", "Tech Head", "Engineering Head"],
    "product": ["CPO", "Product Head", "VP Product", "Director Product"],
    "engineering": ["Engineering Director", "VP Engineering", "Engineering Head"],
    "operations": ["COO", "Operations Head", "VP Operations"]
}

class SmartCompanySearch:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def normalize_company_name(self, partial_name):
        """Use AI to normalize and complete company name"""
        partial_name = partial_name.lower()
        
        # Check known patterns
        for base_name, variations in COMPANY_PATTERNS.items():
            if base_name in partial_name or any(fuzz.partial_ratio(v.lower(), partial_name) > 80 for v in variations):
                return variations[0]  # Return standardized name
        
        # Use SpaCy for unknown companies
        doc = nlp(partial_name)
        for ent in doc.ents:
            if ent.label_ == "ORG":
                return ent.text
        
        return partial_name.title()

    def get_company_variations(self, company_name):
        """Generate variations of company name for searching"""
        base_name = self.normalize_company_name(company_name)
        variations = [
            base_name,
            f"{base_name} India",
            f"{base_name} GCC",
            f"{base_name} Development Center",
            f"{base_name} R&D"
        ]
        return list(set(variations))

    def search_company(self, company_name):
        """Smart company search with multiple attempts"""
        company_data = []
        variations = self.get_company_variations(company_name)
        
        for variation in variations:
            try:
                # LinkedIn search
                linkedin_url = f"https://www.linkedin.com/company/{quote(variation.lower().replace(' ', '-'))}"
                response = self.session.get(linkedin_url, timeout=10)
                
                if response.status_code == 200:
                    company_data.append({
                        'Company Name': variation,
                        'Standard Name': self.normalize_company_name(company_name),
                        'LinkedIn': linkedin_url,
                        'Type': 'GCC/Development Center',
                        'Location': 'India',
                        'Source': 'LinkedIn'
                    })
                
                time.sleep(1)  # Respect rate limits
            except Exception as e:
                continue
        
        return pd.DataFrame(company_data).drop_duplicates(subset=['LinkedIn'])

    def search_executives(self, company_name):
        """Smart executive search with role matching"""
        executives = []
        normalized_name = self.normalize_company_name(company_name)
        
        for role_category, role_patterns in EXECUTIVE_ROLES.items():
            for role in role_patterns:
                try:
                    search_query = f"{normalized_name} {role} india linkedin"
                    url = f"https://www.google.com/search?q={quote(search_query)}"
                    response = self.session.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        for result in soup.find_all('div', class_='g'):
                            link = result.find('a')
                            title = result.find('h3')
                            
                            if link and title and 'linkedin.com/in/' in link.get('href', ''):
                                name_parts = title.text.split('-')
                                if len(name_parts) >= 2:
                                    name = name_parts[0].strip()
                                    position = name_parts[1].strip()
                                    
                                    # Check if this is a relevant executive role
                                    if any(rp.lower() in position.lower() for rp in role_patterns):
                                        executive = {
                                            'Name': name,
                                            'Position': position,
                                            'Category': role_category,
                                            'Company': normalized_name,
                                            'LinkedIn': link.get('href'),
                                            'Location': 'India'
                                        }
                                        
                                        # Avoid duplicates using fuzzy matching
                                        if not any(fuzz.ratio(e['Name'], name) > 90 for e in executives):
                                            executives.append(executive)
                    
                    time.sleep(1)  # Respect rate limits
                except Exception as e:
                    continue
        
        return pd.DataFrame(executives)

def main():
    st.title("🎯 Smart GCC Company Tracker")
    
    # Initialize search engine
    searcher = SmartCompanySearch()
    
    # Search interface
    col1, col2 = st.columns([3,1])
    with col1:
        company_input = st.text_input(
            "Enter company name (full or partial)",
            placeholder="e.g., msft, google, amzn, etc."
        )
    with col2:
        st.write("")
        st.write("")
        search = st.button("🔍 Search")
    
    if company_input and search:
        with st.spinner("Searching... Please wait"):
            # Create progress bar
            progress = st.progress(0)
            
            # Search company
            progress.progress(25)
            company_df = searcher.search_company(company_input)
            
            # Search executives
            progress.progress(75)
            people_df = searcher.search_executives(company_input)
            
            progress.progress(100)
            
            # Display results in tabs
            tab1, tab2 = st.tabs(["Company Info", "Key Executives"])
            
            with tab1:
                if not company_df.empty:
                    st.success(f"Found company information for {company_df['Standard Name'].iloc[0]}")
                    st.dataframe(
                        company_df,
                        column_config={
                            "LinkedIn": st.column_config.LinkColumn()
                        },
                        hide_index=True
                    )
                else:
                    st.warning("No company information found")
            
            with tab2:
                if not people_df.empty:
                    # Add filters
                    col1, col2 = st.columns(2)
                    with col1:
                        categories = ['All'] + list(people_df['Category'].unique())
                        category_filter = st.selectbox("Filter by Category", categories)
                    
                    # Apply filters
                    filtered_df = people_df
                    if category_filter != 'All':
                        filtered_df = filtered_df[filtered_df['Category'] == category_filter]
                    
                    st.dataframe(
                        filtered_df,
                        column_config={
                            "LinkedIn": st.column_config.LinkColumn("Profile")
                        },
                        hide_index=True
                    )
                else:
                    st.warning("No executive information found")

if __name__ == "__main__":
    main()

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import quote

# Page Configuration
st.set_page_config(page_title="GCC Search", layout="wide")

# Clean UI
st.markdown("""
<style>
    .main {padding: 0 !important;}
    .stDataFrame {font-size: 14px !important;}
    .st-emotion-cache-16idsys p {font-size: 14px;}
    .search-box {margin-bottom: 20px;}
</style>
""", unsafe_allow_html=True)

def get_search_results(query):
    """Get search results from Google"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        url = f"https://www.google.com/search?q={quote(query)}"
        response = requests.get(url, headers=headers, timeout=10)
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        st.error(f"Search failed: {e}")
        return None

def extract_linkedin_data(company_name):
    """Extract LinkedIn profiles and company data"""
    # Search for company and people
    company_data = []
    people_data = []
    
    # Company search
    soup = get_search_results(f"{company_name} company gcc linkedin")
    if soup:
        for result in soup.find_all('div', class_='g'):
            link = result.find('a')
            if link and 'linkedin.com/company' in link.get('href', ''):
                company_data.append({
                    'Company': company_name,
                    'LinkedIn': link.get('href'),
                    'Type': 'Company Profile'
                })
                break
    
    # People search
    search_terms = [
        ('CEO', 'Leadership'),
        ('CTO', 'Technology'),
        ('Director', 'Management'),
        ('Vice President', 'Executive'),
        ('Head', 'Management')
    ]
    
    for role, level in search_terms:
        soup = get_search_results(f"{company_name} {role} linkedin")
        if soup:
            for result in soup.find_all('div', class_='g'):
                link = result.find('a')
                title = result.find('h3')
                if link and title and 'linkedin.com/in' in link.get('href', ''):
                    text = title.text.split('-')
                    if len(text) >= 2:
                        name = text[0].strip()
                        position = text[1].strip()
                        # Check if this person is already added
                        if not any(p['Name'] == name for p in people_data):
                            people_data.append({
                                'Name': name,
                                'Position': position,
                                'Level': level,
                                'Company': company_name,
                                'LinkedIn': link.get('href')
                            })
    
    return pd.DataFrame(company_data), pd.DataFrame(people_data)

def main():
    st.title("🔍 GCC Company Search")
    
    # Search box
    col1, col2 = st.columns([4,1])
    with col1:
        company = st.text_input("", placeholder="Enter company name (e.g., Microsoft, Google)")
    with col2:
        search = st.button("Search")
    
    if company and search:
        with st.spinner('Searching...'):
            company_df, people_df = extract_linkedin_data(company)
            
            # Display results in tabs
            tab1, tab2 = st.tabs(["🏢 Company", "👥 Key People"])
            
            with tab1:
                if not company_df.empty:
                    st.dataframe(
                        company_df,
                        column_config={
                            "LinkedIn": st.column_config.LinkColumn()
                        },
                        hide_index=True
                    )
                else:
                    st.info("No company profile found")
            
            with tab2:
                if not people_df.empty:
                    # Add filters
                    col1, col2 = st.columns(2)
                    with col1:
                        levels = ['All'] + sorted(people_df['Level'].unique().tolist())
                        level_filter = st.selectbox('Filter by Level', levels)
                    
                    # Apply filters
                    filtered_df = people_df
                    if level_filter != 'All':
                        filtered_df = filtered_df[filtered_df['Level'] == level_filter]
                    
                    # Display filtered results
                    st.dataframe(
                        filtered_df,
                        column_config={
                            "LinkedIn": st.column_config.LinkColumn(),
                            "Name": st.column_config.TextColumn(width="medium"),
                            "Position": st.column_config.TextColumn(width="large"),
                            "Level": st.column_config.TextColumn(width="small")
                        },
                        hide_index=True
                    )
                else:
                    st.info("No key people found")

if __name__ == "__main__":
    main()

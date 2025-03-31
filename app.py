import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import quote_plus

# Page Configuration
st.set_page_config(
    page_title="GCC Search",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stDataFrame {
        font-size: 14px;
    }
    .search-container {
        padding: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

def search_google(query):
    """Perform Google search"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    try:
        response = requests.get(url, headers=headers)
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return None

def find_company_info(company_name):
    """Find company information"""
    soup = search_google(f"{company_name} company gcc linkedin")
    
    if not soup:
        return pd.DataFrame()
    
    company_data = []
    
    for result in soup.find_all('div', {'class': ['g']}):
        title = result.find('h3')
        link = result.find('a')
        description = result.find('div', {'class': 'VwiC3b'})
        
        if title and link:
            company_info = {
                'Company Name': company_name,
                'Title': title.text,
                'URL': link.get('href', ''),
                'Description': description.text if description else 'N/A'
            }
            company_data.append(company_info)
    
    return pd.DataFrame(company_data)

def find_people_info(company_name):
    """Find people information"""
    people_data = []
    search_terms = [
        f"{company_name} CEO linkedin",
        f"{company_name} CTO linkedin",
        f"{company_name} Director linkedin",
        f"{company_name} VP linkedin"
    ]
    
    for term in search_terms:
        soup = search_google(term)
        if not soup:
            continue
            
        for result in soup.find_all('div', {'class': ['g']}):
            title = result.find('h3')
            link = result.find('a')
            
            if title and link and 'linkedin.com/in/' in link.get('href', ''):
                text = title.text
                if '-' in text:
                    name, role = text.split('-', 1)
                    person_info = {
                        'Name': name.strip(),
                        'Role': role.strip(),
                        'Company': company_name,
                        'LinkedIn URL': link.get('href', '')
                    }
                    # Avoid duplicates
                    if not any(p['Name'] == person_info['Name'] for p in people_data):
                        people_data.append(person_info)
    
    return pd.DataFrame(people_data)

def main():
    st.title("🔍 GCC Search")
    
    # Search interface
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            company_name = st.text_input(
                "Enter company name",
                placeholder="Example: Microsoft, Google, etc."
            )
        with col2:
            st.write("")
            st.write("")
            search = st.button("🔍 Search")
    
    if company_name and search:
        # Create tabs
        tab1, tab2 = st.tabs(["Company Information", "Key People"])
        
        with tab1:
            with st.spinner('Searching company information...'):
                company_df = find_company_info(company_name)
                if not company_df.empty:
                    st.subheader("Company Details")
                    # Display filtered columns in the table
                    display_df = company_df[['Company Name', 'Title', 'URL']]
                    st.dataframe(
                        display_df,
                        column_config={
                            "URL": st.column_config.LinkColumn("Link")
                        },
                        hide_index=True
                    )
                else:
                    st.info("No company information found")
        
        with tab2:
            with st.spinner('Searching key people...'):
                people_df = find_people_info(company_name)
                if not people_df.empty:
                    st.subheader("Key People")
                    # Add filters for roles
                    roles = ['All'] + list(people_df['Role'].unique())
                    selected_role = st.selectbox("Filter by Role", roles)
                    
                    # Filter data based on selection
                    if selected_role != 'All':
                        filtered_df = people_df[people_df['Role'].str.contains(selected_role, case=False)]
                    else:
                        filtered_df = people_df
                    
                    # Display the table
                    st.dataframe(
                        filtered_df,
                        column_config={
                            "LinkedIn URL": st.column_config.LinkColumn("LinkedIn Profile")
                        },
                        hide_index=True
                    )
                else:
                    st.info("No key people found")
    
    # Add search tips
    with st.expander("Search Tips"):
        st.markdown("""
        - Enter the complete company name for better results
        - Results show company information and key executives
        - Click on links to visit profiles
        - Use the role filter to find specific positions
        """)

if __name__ == "__main__":
    main()

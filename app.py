import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Page Configuration
st.set_page_config(
    page_title="GCC Search",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stTable {
        width: 100%;
    }
    .linkedin-link {
        color: #0a66c2;
        text-decoration: none;
    }
    .header-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800)
def search_company_and_people(company_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # Company Information
        company_data = {
            'Company Name': [],
            'Website': [],
            'LinkedIn URL': [],
            'Location': [],
            'Industry': []
        }
        
        # People Information
        people_data = {
            'Name': [],
            'Designation': [],
            'LinkedIn URL': [],
            'Company': []
        }
        
        # Search for company
        search_url = f"https://www.google.com/search?q={company_name} company gcc linkedin"
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract company info
        for result in soup.find_all('div', {'class': ['g', 'tF2Cxc']}):
            link = result.find('a')
            if link and ('linkedin.com/company' in link['href'] or company_name.lower() in link['href'].lower()):
                company_data['Company Name'].append(company_name)
                company_data['Website'].append(link['href'])
                company_data['LinkedIn URL'].append(link['href'] if 'linkedin.com' in link['href'] else '')
                company_data['Location'].append('N/A')  # Would need additional scraping
                company_data['Industry'].append('N/A')  # Would need additional scraping
                break
        
        # Search for people
        search_terms = [
            f"{company_name} CEO linkedin",
            f"{company_name} CTO linkedin",
            f"{company_name} Founder linkedin",
            f"{company_name} Director linkedin",
            f"{company_name} Vice President linkedin"
        ]
        
        for term in search_terms:
            search_url = f"https://www.google.com/search?q={term}"
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for result in soup.find_all('div', {'class': ['g', 'tF2Cxc']}):
                title = result.find('h3')
                link = result.find('a')
                
                if title and link and 'linkedin.com/in/' in link['href']:
                    text = title.text
                    if '-' in text:
                        name, designation = text.split('-', 1)
                        people_data['Name'].append(name.strip())
                        people_data['Designation'].append(designation.strip())
                        people_data['LinkedIn URL'].append(link['href'])
                        people_data['Company'].append(company_name)
            
            time.sleep(1)  # Avoid rate limiting
        
        return pd.DataFrame(company_data), pd.DataFrame(people_data)
    
    except Exception as e:
        st.error(f"Error in search: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

def main():
    st.title("🔍 GCC Company Search")
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    with col1:
        company_name = st.text_input("Enter company name", placeholder="Example: Microsoft, Google, etc.")
    with col2:
        st.write("")
        st.write("")
        search_button = st.button("🔍 Search")
    
    if company_name and search_button:
        with st.spinner('Searching...'):
            company_df, people_df = search_company_and_people(company_name)
            
            # Display results in tabs
            tab1, tab2 = st.tabs(["Company Information", "Key People"])
            
            with tab1:
                if not company_df.empty:
                    st.subheader("Company Details")
                    # Display company information in a table
                    st.dataframe(
                        company_df,
                        column_config={
                            "LinkedIn URL": st.column_config.LinkColumn("LinkedIn URL"),
                            "Website": st.column_config.LinkColumn("Website")
                        },
                        hide_index=True
                    )
                else:
                    st.info("No company information found")
            
            with tab2:
                if not people_df.empty:
                    st.subheader("Key People")
                    # Display people information in a table
                    st.dataframe(
                        people_df,
                        column_config={
                            "LinkedIn URL": st.column_config.LinkColumn("LinkedIn URL")
                        },
                        hide_index=True
                    )
                    
                    # Export buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Export to Excel"):
                            with pd.ExcelWriter(f"{company_name}_search_results.xlsx") as writer:
                                company_df.to_excel(writer, sheet_name='Company Info', index=False)
                                people_df.to_excel(writer, sheet_name='Key People', index=False)
                            st.success("Data exported to Excel!")
                    with col2:
                        if st.button("Export to CSV"):
                            people_df.to_csv(f"{company_name}_key_people.csv", index=False)
                            st.success("Data exported to CSV!")
                else:
                    st.info("No key people found")
        
        # Display search tips
        with st.expander("Search Tips"):
            st.markdown("""
            - Enter the full company name for better results
            - Results include C-level executives, founders, and directors
            - Click column headers to sort the data
            - Use the export buttons to download the results
            """)

if __name__ == "__main__":
    main()

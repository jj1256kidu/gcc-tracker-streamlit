import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="GCC Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stDataFrame {
        font-size: 14px;
    }
    .filter-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .metric-container {
        background-color: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800)
def search_company_and_people(company_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # Enhanced Company Information
        company_data = {
            'Company Name': [],
            'Website': [],
            'LinkedIn URL': [],
            'Location': [],
            'Industry': [],
            'Company Type': [],
            'Employee Range': [],
            'Founded Year': [],
            'GCC Status': [],
            'Last Updated': []
        }
        
        # Enhanced People Information
        people_data = {
            'Name': [],
            'Designation': [],
            'Function': [],  # Added field
            'Level': [],     # Added field
            'Location': [],  # Added field
            'Experience': [],  # Added field
            'LinkedIn URL': [],
            'Company': [],
            'Email Domain': [],  # Added field
            'Last Updated': []
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
                company_data['Location'].append('India')  # Default for GCC
                company_data['Industry'].append('Technology')  # Default
                company_data['Company Type'].append('GCC')
                company_data['Employee Range'].append('1000+')
                company_data['Founded Year'].append('N/A')
                company_data['GCC Status'].append('Active')
                company_data['Last Updated'].append(datetime.now().strftime('%Y-%m-%d'))
                break
        
        # Search for people with enhanced roles
        search_terms = [
            ('CEO', 'CXO', 'Leadership'),
            ('CTO', 'Technology', 'Leadership'),
            ('Founder', 'Leadership', 'Leadership'),
            ('Director', 'Management', 'Senior'),
            ('Vice President', 'Management', 'Senior'),
            ('Head', 'Management', 'Senior')
        ]
        
        for role, function, level in search_terms:
            search_url = f"https://www.google.com/search?q={company_name} {role} linkedin"
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
                        people_data['Function'].append(function)
                        people_data['Level'].append(level)
                        people_data['Location'].append('India')  # Default
                        people_data['Experience'].append('10+ years')  # Default
                        people_data['LinkedIn URL'].append(link['href'])
                        people_data['Company'].append(company_name)
                        people_data['Email Domain'].append(f"@{company_name.lower().replace(' ', '')}.com")
                        people_data['Last Updated'].append(datetime.now().strftime('%Y-%m-%d'))
            
            time.sleep(1)
        
        return pd.DataFrame(company_data), pd.DataFrame(people_data)
    
    except Exception as e:
        st.error(f"Error in search: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

def main():
    st.title("🔍 Enhanced GCC Search")
    
    # Search interface with filters
    with st.container():
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            company_name = st.text_input("Enter company name", placeholder="Example: Microsoft, Google, etc.")
        with col2:
            search_type = st.selectbox("Search Type", ["All", "Company Only", "People Only"])
        with col3:
            st.write("")
            st.write("")
            search_button = st.button("🔍 Search", use_container_width=True)
    
    if company_name and search_button:
        with st.spinner('Searching...'):
            company_df, people_df = search_company_and_people(company_name)
            
            # Display metrics
            if not company_df.empty or not people_df.empty:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Results", len(company_df) + len(people_df))
                with col2:
                    st.metric("Companies Found", len(company_df))
                with col3:
                    st.metric("People Found", len(people_df))
                with col4:
                    st.metric("Last Updated", datetime.now().strftime('%Y-%m-%d'))
            
            # Tabs for different views
            tab1, tab2, tab3 = st.tabs(["Company Information", "Key People", "Analytics"])
            
            with tab1:
                if not company_df.empty and search_type != "People Only":
                    st.subheader("Company Details")
                    
                    # Filters for company data
                    with st.expander("Filters"):
                        col1, col2 = st.columns(2)
                        with col1:
                            industry_filter = st.multiselect(
                                "Industry",
                                options=company_df['Industry'].unique()
                            )
                        with col2:
                            location_filter = st.multiselect(
                                "Location",
                                options=company_df['Location'].unique()
                            )
                    
                    # Apply filters
                    filtered_company_df = company_df
                    if industry_filter:
                        filtered_company_df = filtered_company_df[filtered_company_df['Industry'].isin(industry_filter)]
                    if location_filter:
                        filtered_company_df = filtered_company_df[filtered_company_df['Location'].isin(location_filter)]
                    
                    # Display company table
                    st.dataframe(
                        filtered_company_df,
                        column_config={
                            "LinkedIn URL": st.column_config.LinkColumn("LinkedIn URL"),
                            "Website": st.column_config.LinkColumn("Website")
                        },
                        hide_index=True
                    )
            
            with tab2:
                if not people_df.empty and search_type != "Company Only":
                    st.subheader("Key People")
                    
                    # Filters for people data
                    with st.expander("Filters"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            function_filter = st.multiselect(
                                "Function",
                                options=people_df['Function'].unique()
                            )
                        with col2:
                            level_filter = st.multiselect(
                                "Level",
                                options=people_df['Level'].unique()
                            )
                        with col3:
                            location_filter = st.multiselect(
                                "Location",
                                options=people_df['Location'].unique()
                            )
                    
                    # Apply filters
                    filtered_people_df = people_df
                    if function_filter:
                        filtered_people_df = filtered_people_df[filtered_people_df['Function'].isin(function_filter)]
                    if level_filter:
                        filtered_people_df = filtered_people_df[filtered_people_df['Level'].isin(level_filter)]
                    if location_filter:
                        filtered_people_df = filtered_people_df[filtered_people_df['Location'].isin(location_filter)]
                    
                    # Display people table
                    st.dataframe(
                        filtered_people_df,
                        column_config={
                            "LinkedIn URL": st.column_config.LinkColumn("LinkedIn URL")
                        },
                        hide_index=True
                    )
            
            with tab3:
                if not people_df.empty:
                    st.subheader("People Analytics")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("Distribution by Function")
                        function_counts = people_df['Function'].value_counts()
                        st.bar_chart(function_counts)
                    
                    with col2:
                        st.write("Distribution by Level")
                        level_counts = people_df['Level'].value_counts()
                        st.bar_chart(level_counts)
            
            # Export options
            st.sidebar.header("Export Options")
            export_format = st.sidebar.selectbox("Select Format", ["Excel", "CSV", "JSON"])
            if st.sidebar.button("Export Data"):
                if export_format == "Excel":
                    with pd.ExcelWriter(f"{company_name}_search_results.xlsx") as writer:
                        company_df.to_excel(writer, sheet_name='Company Info', index=False)
                        people_df.to_excel(writer, sheet_name='Key People', index=False)
                    st.sidebar.success("Exported to Excel!")
                elif export_format == "CSV":
                    company_df.to_csv(f"{company_name}_company_info.csv", index=False)
                    people_df.to_csv(f"{company_name}_key_people.csv", index=False)
                    st.sidebar.success("Exported to CSV!")
                else:
                    combined_data = {
                        'company_info': company_df.to_dict('records'),
                        'key_people': people_df.to_dict('records')
                    }
                    st.sidebar.download_button(
                        "Download JSON",
                        data=pd.json_normalize(combined_data).to_json(),
                        file_name=f"{company_name}_search_results.json",
                        mime="application/json"
                    )

if __name__ == "__main__":
    main()

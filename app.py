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
    /* Search box styling */
    .search-container {
        margin: 20px 0;
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 10px;
    }
    
    /* Result card styling */
    .result-card {
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #007bff;
        background-color: white;
        border-radius: 4px;
    }
    
    /* Person card styling */
    .person-card {
        padding: 10px;
        margin: 5px 0;
        background-color: #f8f9fa;
        border-radius: 4px;
    }
    
    .designation {
        color: #666;
        font-size: 0.9em;
    }
    
    .linkedin-link {
        color: #0077b5;
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800)
def search_company_and_people(query):
    """Search for company and people information"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    results = {
        'company_info': [],
        'people': []
    }
    
    try:
        # Search for company
        company_search = requests.get(
            f"https://www.google.com/search?q={quote_plus(f'{query} company gcc linkedin')}",
            headers=headers
        )
        company_soup = BeautifulSoup(company_search.text, 'html.parser')
        
        # Search for people
        people_search = requests.get(
            f"https://www.google.com/search?q={quote_plus(f'{query} executives leadership team linkedin')}",
            headers=headers
        )
        people_soup = BeautifulSoup(people_search.text, 'html.parser')
        
        # Extract company information
        for result in company_soup.find_all('div', class_='g'):
            link = result.find('a')
            if link and 'linkedin.com/company' in link.get('href', ''):
                title = result.find('h3')
                snippet = result.find('div', class_='VwiC3b')
                if title and snippet:
                    results['company_info'].append({
                        'name': title.text,
                        'description': snippet.text,
                        'linkedin_url': link.get('href')
                    })
        
        # Extract people information
        for result in people_soup.find_all('div', class_='g'):
            link = result.find('a')
            if link and 'linkedin.com/in' in link.get('href', ''):
                title = result.find('h3')
                snippet = result.find('div', class_='VwiC3b')
                if title and snippet:
                    # Extract name and designation
                    full_title = title.text.split('-')
                    name = full_title[0].strip()
                    designation = full_title[1].strip() if len(full_title) > 1 else "Executive"
                    
                    results['people'].append({
                        'name': name,
                        'designation': designation,
                        'linkedin_url': link.get('href')
                    })
        
        return results
    
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return results

def main():
    # Search interface
    st.markdown("<h1 style='text-align: center'>🔍 GCC Search</h1>", unsafe_allow_html=True)
    
    # Search box
    query = st.text_input(
        "",
        placeholder="Search for company or executive...",
        help="Enter company name to search for company and executive information"
    )
    
    if query:
        with st.spinner('Searching...'):
            results = search_company_and_people(query)
            
            # Display results
            if results['company_info'] or results['people']:
                # Company information
                if results['company_info']:
                    st.subheader("Company Information")
                    for company in results['company_info']:
                        st.markdown(f"""
                        <div class="result-card">
                            <h3>{company['name']}</h3>
                            <p>{company['description']}</p>
                            <a href="{company['linkedin_url']}" target="_blank">Company LinkedIn Profile</a>
                        </div>
                        """, unsafe_allow_html=True)
                
                # People information
                if results['people']:
                    st.subheader("Key People")
                    cols = st.columns(2)
                    for idx, person in enumerate(results['people']):
                        with cols[idx % 2]:
                            st.markdown(f"""
                            <div class="person-card">
                                <h4>{person['name']}</h4>
                                <p class="designation">{person['designation']}</p>
                                <a class="linkedin-link" href="{person['linkedin_url']}" target="_blank">
                                    View LinkedIn Profile
                                </a>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Export option
                if st.button("Export Results"):
                    # Create DataFrame for export
                    company_df = pd.DataFrame(results['company_info'])
                    people_df = pd.DataFrame(results['people'])
                    
                    # Create Excel file
                    with pd.ExcelWriter('gcc_search_results.xlsx') as writer:
                        company_df.to_excel(writer, sheet_name='Company Info', index=False)
                        people_df.to_excel(writer, sheet_name='Key People', index=False)
                    
                    st.success("Results exported to gcc_search_results.xlsx")
            
            else:
                st.info("No results found. Try modifying your search terms.")
    
    # Footer with usage information
    st.markdown("---")
    st.markdown("""
    <small>
    Search for companies and their key executives. Results include:
    - Company LinkedIn profiles
    - Company descriptions
    - Key executives and their roles
    - LinkedIn profiles of executives
    </small>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

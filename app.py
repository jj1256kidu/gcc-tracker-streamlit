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
    .search-box {
        margin: 20px 0;
    }
    .result-card {
        background-color: white;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #ddd;
        border-radius: 5px;
    }
    .person-info {
        background-color: #f8f9fa;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .linkedin-button {
        color: #0a66c2;
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)

def get_company_info(company_name):
    """Get company information using custom search"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        # Search for company LinkedIn page
        search_url = f"https://www.google.com/search?q={company_name}+company+linkedin+gcc"
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        company_info = {
            'name': company_name,
            'linkedin_url': '',
            'website': '',
            'description': ''
        }
        
        # Find LinkedIn URL
        for link in soup.find_all('a'):
            href = str(link.get('href', ''))
            if 'linkedin.com/company' in href:
                company_info['linkedin_url'] = href
                break
        
        # Find company website
        search_url = f"https://www.google.com/search?q={company_name}+company+website"
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for link in soup.find_all('a'):
            href = str(link.get('href', ''))
            if not any(x in href for x in ['google', 'linkedin', 'facebook', 'twitter']):
                if company_name.lower() in href.lower():
                    company_info['website'] = href
                    break
        
        # Find description
        for div in soup.find_all('div', {'class': ['VwiC3b', 'yXK7lf']}):
            if len(div.text) > 50:
                company_info['description'] = div.text
                break
        
        return company_info
    
    except Exception as e:
        st.error(f"Error fetching company info: {str(e)}")
        return None

def get_people_info(company_name):
    """Get key people information"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    people = []
    search_terms = [
        f"{company_name} CEO linkedin",
        f"{company_name} CTO linkedin",
        f"{company_name} Founder linkedin",
        f"{company_name} Director linkedin",
        f"{company_name} VP linkedin"
    ]
    
    try:
        for term in search_terms:
            search_url = f"https://www.google.com/search?q={term}"
            response = requests.get(search_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for result in soup.find_all('div', {'class': ['g', 'tF2Cxc']}):
                title = result.find('h3')
                if title and 'linkedin.com/in/' in str(result):
                    name_parts = title.text.split('-')
                    if len(name_parts) >= 2:
                        person = {
                            'name': name_parts[0].strip(),
                            'title': name_parts[1].strip(),
                            'linkedin_url': result.find('a')['href']
                        }
                        # Avoid duplicates
                        if not any(p['name'] == person['name'] for p in people):
                            people.append(person)
            
            # Add delay to avoid rate limiting
            time.sleep(1)
        
        return people
    
    except Exception as e:
        st.error(f"Error fetching people info: {str(e)}")
        return []

def main():
    st.title("🔍 GCC Company Search")
    
    # Search box
    company_name = st.text_input(
        "Enter company name",
        placeholder="Example: Microsoft, Google, TCS, etc.",
        key="search_box"
    )
    
    if company_name:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            with st.spinner('Searching company information...'):
                company_info = get_company_info(company_name)
                if company_info:
                    st.subheader("Company Information")
                    st.markdown(f"""
                    <div class="result-card">
                        <h3>{company_info['name']}</h3>
                        <p>{company_info['description']}</p>
                        <p><strong>Website:</strong> <a href="{company_info['website']}" target="_blank">{company_info['website']}</a></p>
                        <p><strong>LinkedIn:</strong> <a href="{company_info['linkedin_url']}" target="_blank">Company Profile</a></p>
                    </div>
                    """, unsafe_allow_html=True)
        
        with col2:
            with st.spinner('Searching key people...'):
                people = get_people_info(company_name)
                if people:
                    st.subheader("Key People")
                    for person in people:
                        st.markdown(f"""
                        <div class="person-info">
                            <h4>{person['name']}</h4>
                            <p>{person['title']}</p>
                            <a href="{person['linkedin_url']}" target="_blank" class="linkedin-button">
                                View LinkedIn Profile
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                
                    # Export button
                    if st.button("Export to Excel"):
                        df = pd.DataFrame(people)
                        df.to_excel(f"{company_name}_key_people.xlsx", index=False)
                        st.success("Data exported successfully!")
                else:
                    st.info("No key people found. Try a different search term.")

if __name__ == "__main__":
    main()

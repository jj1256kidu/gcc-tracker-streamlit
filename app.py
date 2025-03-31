import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Page Configuration
st.set_page_config(
    page_title="GCC Tracker",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .company-info {
        padding: 20px;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        margin: 10px 0;
    }
    .person-card {
        padding: 15px;
        border: 1px solid #f0f0f0;
        border-radius: 5px;
        margin: 5px 0;
    }
    .highlight {
        background-color: #f0f8ff;
        padding: 2px 5px;
        border-radius: 3px;
    }
    </style>
""", unsafe_allow_html=True)

def search_company(company_name):
    """Search company information using Google"""
    try:
        # Set up Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Search for company website
        driver.get(f"https://www.google.com/search?q={company_name} company website")
        website = driver.find_element(By.CSS_SELECTOR, "cite").text
        
        # Search for LinkedIn page
        driver.get(f"https://www.google.com/search?q={company_name} linkedin company")
        linkedin_url = ""
        links = driver.find_elements(By.CSS_SELECTOR, "cite")
        for link in links:
            if "linkedin.com/company" in link.text:
                linkedin_url = link.text
                break
        
        # Get company information from LinkedIn
        if linkedin_url:
            driver.get(linkedin_url)
            time.sleep(2)  # Wait for page to load
            
            try:
                company_info = {
                    'name': company_name,
                    'website': website,
                    'linkedin': linkedin_url,
                    'description': driver.find_element(By.CLASS_NAME, "about-us__description").text,
                    'industry': driver.find_element(By.CLASS_NAME, "company-industries").text,
                    'headquarters': driver.find_element(By.CLASS_NAME, "company-location").text
                }
            except:
                company_info = {
                    'name': company_name,
                    'website': website,
                    'linkedin': linkedin_url,
                    'description': "Description not found",
                    'industry': "Industry not found",
                    'headquarters': "Location not found"
                }
        
        driver.quit()
        return company_info
    
    except Exception as e:
        st.error(f"Error searching company: {str(e)}")
        return None

def search_key_people(company_linkedin_url):
    """Search key people from company's LinkedIn page"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"{company_linkedin_url}/people")
        time.sleep(2)
        
        people = []
        people_elements = driver.find_elements(By.CLASS_NAME, "employee-card")
        
        for element in people_elements[:10]:  # Get first 10 people
            try:
                name = element.find_element(By.CLASS_NAME, "employee-name").text
                title = element.find_element(By.CLASS_NAME, "employee-title").text
                linkedin_url = element.find_element(By.CLASS_NAME, "employee-link").get_attribute("href")
                location = element.find_element(By.CLASS_NAME, "employee-location").text
                
                people.append({
                    'name': name,
                    'title': title,
                    'linkedin': linkedin_url,
                    'location': location
                })
            except:
                continue
        
        driver.quit()
        return people
    
    except Exception as e:
        st.error(f"Error searching people: {str(e)}")
        return []

def main():
    st.title("GCC Company Search")
    
    # Search bar
    company_name = st.text_input("Enter company name to search")
    
    if company_name:
        with st.spinner('Searching company information...'):
            company_info = search_company(company_name)
            
            if company_info:
                # Display company information
                st.header("Company Information")
                with st.container():
                    st.markdown(f"""
                    <div class="company-info">
                        <h3>{company_info['name']}</h3>
                        <p><strong>Website:</strong> <a href="{company_info['website']}" target="_blank">{company_info['website']}</a></p>
                        <p><strong>LinkedIn:</strong> <a href="{company_info['linkedin']}" target="_blank">{company_info['linkedin']}</a></p>
                        <p><strong>Industry:</strong> {company_info['industry']}</p>
                        <p><strong>Headquarters:</strong> {company_info['headquarters']}</p>
                        <p><strong>Description:</strong> {company_info['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Search for key people
                st.header("Key People")
                with st.spinner('Searching key people...'):
                    people = search_key_people(company_info['linkedin'])
                    
                    if people:
                        for person in people:
                            st.markdown(f"""
                            <div class="person-card">
                                <h4>{person['name']}</h4>
                                <p><strong>Title:</strong> {person['title']}</p>
                                <p><strong>Location:</strong> {person['location']}</p>
                                <p><strong>LinkedIn:</strong> <a href="{person['linkedin']}" target="_blank">{person['linkedin']}</a></p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No key people information found")
            else:
                st.error("Company information not found")

if __name__ == "__main__":
    main()

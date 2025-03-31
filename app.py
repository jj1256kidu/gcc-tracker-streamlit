import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="GCC Tracker",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sample Data (moved from external file)
sample_companies = [
    {
        'name': 'Tech Corp GCC',
        'website': 'https://techcorp.com',
        'linkedin_url': 'https://linkedin.com/company/techcorp',
        'city': 'Bangalore',
        'industry': 'Technology',
        'description': 'Leading technology GCC'
    },
    {
        'name': 'Finance Solutions',
        'website': 'https://finsolutions.com',
        'linkedin_url': 'https://linkedin.com/company/finsolutions',
        'city': 'Mumbai',
        'industry': 'Finance',
        'description': 'Financial services GCC'
    }
]

sample_stakeholders = [
    {
        'name': 'John Doe',
        'role': 'CEO',
        'linkedin_url': 'https://linkedin.com/in/johndoe',
        'email': 'john@techcorp.com',
        'company_id': 1
    },
    {
        'name': 'Jane Smith',
        'role': 'CTO',
        'linkedin_url': 'https://linkedin.com/in/janesmith',
        'email': 'jane@finsolutions.com',
        'company_id': 2
    }
]

# Database Setup
def init_db():
    try:
        conn = sqlite3.connect('gcc_tracker.db')
        c = conn.cursor()
        
        # Create companies table
        c.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                website TEXT,
                linkedin_url TEXT,
                city TEXT,
                industry TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create stakeholders table
        c.execute('''
            CREATE TABLE IF NOT EXISTS stakeholders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT,
                linkedin_url TEXT,
                email TEXT,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (id)
            )
        ''')
        
        # Insert sample data if tables are empty
        c.execute("SELECT COUNT(*) FROM companies")
        if c.fetchone()[0] == 0:
            for company in sample_companies:
                c.execute("""
                    INSERT INTO companies (name, website, linkedin_url, city, industry, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (company['name'], company['website'], company['linkedin_url'], 
                     company['city'], company['industry'], company['description']))
            
            for stakeholder in sample_stakeholders:
                c.execute("""
                    INSERT INTO stakeholders (name, role, linkedin_url, email, company_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (stakeholder['name'], stakeholder['role'], stakeholder['linkedin_url'],
                     stakeholder['email'], stakeholder['company_id']))
        
        conn.commit()
    except Exception as e:
        st.error(f"Database Error: {str(e)}")
    finally:
        conn.close()

# Authentication
def check_authentication(username: str, password: str) -> bool:
    return (username == st.secrets.get("admin_username", "admin") and 
            password == st.secrets.get("admin_password", "password"))

# Data Management
@st.cache_data(ttl=3600)
def get_companies():
    try:
        conn = sqlite3.connect('gcc_tracker.db')
        companies = pd.read_sql_query("SELECT * FROM companies", conn)
        return companies
    except Exception as e:
        st.error(f"Error loading companies: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data(ttl=3600)
def get_stakeholders():
    try:
        conn = sqlite3.connect('gcc_tracker.db')
        stakeholders = pd.read_sql_query("""
            SELECT s.*, c.name as company_name 
            FROM stakeholders s 
            JOIN companies c ON s.company_id = c.id
        """, conn)
        return stakeholders
    except Exception as e:
        st.error(f"Error loading stakeholders: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

# UI Components
def show_companies_page():
    st.header("Companies")
    
    companies = get_companies()
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        city_filter = st.selectbox("City", ["All"] + list(companies['city'].unique()))
    with col2:
        search = st.text_input("Search companies")
    
    # Filter data
    if city_filter != "All":
        companies = companies[companies['city'] == city_filter]
    if search:
        companies = companies[companies['name'].str.contains(search, case=False)]
    
    # Display data
    st.dataframe(companies)

def show_stakeholders_page():
    st.header("Stakeholders")
    
    stakeholders = get_stakeholders()
    
    # Search filter
    search = st.text_input("Search stakeholders")
    
    # Filter data
    if search:
        stakeholders = stakeholders[
            stakeholders['name'].str.contains(search, case=False) |
            stakeholders['role'].str.contains(search, case=False)
        ]
    
    # Display data
    st.dataframe(stakeholders)

def show_admin_page():
    st.header("Admin Panel")
    
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.success("Cache cleared!")
    
    if st.button("Export Data"):
        companies = get_companies()
        st.download_button(
            label="Download Companies CSV",
            data=companies.to_csv(index=False),
            file_name="companies.csv",
            mime="text/csv"
        )

# Main Application
def main():
    st.title("GCC Tracker")
    
    # Initialize database
    init_db()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a page",
        ["Companies", "Stakeholders", "Admin"]
    )
    
    # Display metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Companies", len(get_companies()))
    with col2:
        st.metric("Total Stakeholders", len(get_stakeholders()))
    
    # Page routing
    if page == "Companies":
        show_companies_page()
    elif page == "Stakeholders":
        show_stakeholders_page()
    elif page == "Admin":
        show_admin_page()

def login():
    st.title("GCC Tracker - Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if check_authentication(username, password):
                st.session_state['authenticated'] = True
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

if __name__ == "__main__":
    if 'authenticated' not in st.session_state:
        login()
    else:
        main()

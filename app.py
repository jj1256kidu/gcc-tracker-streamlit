import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import sqlite3
import jwt
from typing import Optional
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .company-card {
        padding: 20px;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Database Setup
def init_db():
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    ''')
    
    # Create developments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS developments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            title TEXT NOT NULL,
            content TEXT,
            source_url TEXT,
            published_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    ''')
    
    # Insert sample data if tables are empty
    c.execute("SELECT COUNT(*) FROM companies")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO companies (name, website, linkedin_url, city, industry, description)
            VALUES 
            ('Tech Corp GCC', 'https://techcorp.com', 'https://linkedin.com/company/techcorp', 
             'Bangalore', 'Technology', 'Leading technology GCC'),
            ('Finance Solutions', 'https://finsolutions.com', 'https://linkedin.com/company/finsolutions', 
             'Mumbai', 'Finance', 'Financial services GCC')
        """)
    
    conn.commit()
    conn.close()

# Authentication
class AuthHandler:
    def __init__(self):
        self.secret = st.secrets.get("jwt_secret", "your-secret-key")
        self.algorithm = "HS256"

    def create_token(self, username: str) -> str:
        payload = {
            'exp': datetime.utcnow() + timedelta(hours=8),
            'iat': datetime.utcnow(),
            'sub': username
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload['sub']
        except:
            return None

def check_authentication(username: str, password: str) -> bool:
    return (username == st.secrets.get("admin_username", "admin") and 
            password == st.secrets.get("admin_password", "password"))

# Data Management
@st.cache_data(ttl=3600)
def get_companies():
    conn = sqlite3.connect('gcc_tracker.db')
    companies = pd.read_sql_query("SELECT * FROM companies", conn)
    conn.close()
    return companies

@st.cache_data(ttl=3600)
def get_stakeholders():
    conn = sqlite3.connect('gcc_tracker.db')
    stakeholders = pd.read_sql_query("""
        SELECT s.*, c.name as company_name 
        FROM stakeholders s 
        JOIN companies c ON s.company_id = c.id
    """, conn)
    conn.close()
    return stakeholders

@st.cache_data(ttl=3600)
def get_developments():
    conn = sqlite3.connect('gcc_tracker.db')
    developments = pd.read_sql_query("""
        SELECT d.*, c.name as company_name 
        FROM developments d 
        JOIN companies c ON d.company_id = c.id
        ORDER BY published_date DESC
    """, conn)
    conn.close()
    return developments

# Add new company form
def add_company_form():
    with st.form("add_company"):
        st.subheader("Add New Company")
        name = st.text_input("Company Name")
        website = st.text_input("Website")
        linkedin_url = st.text_input("LinkedIn URL")
        city = st.selectbox("City", ["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Chennai", "Pune"])
        industry = st.selectbox("Industry", ["Technology", "Finance", "Healthcare", "Retail", "Manufacturing"])
        description = st.text_area("Description")
        
        if st.form_submit_button("Add Company"):
            conn = sqlite3.connect('gcc_tracker.db')
            c = conn.cursor()
            c.execute("""
                INSERT INTO companies (name, website, linkedin_url, city, industry, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, website, linkedin_url, city, industry, description))
            conn.commit()
            conn.close()
            st.success("Company added successfully!")
            st.cache_data.clear()

# UI Components
def show_companies_page():
    st.header("Companies")
    
    # Add company button
    if st.button("Add New Company"):
        st.session_state['show_add_company'] = True
    
    if st.session_state.get('show_add_company', False):
        add_company_form()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        city_filter = st.selectbox("City", ["All", "Bangalore", "Mumbai", "Delhi", "Hyderabad"])
    with col2:
        industry_filter = st.selectbox("Industry", ["All", "Technology", "Finance", "Healthcare"])
    with col3:
        search = st.text_input("Search companies")
    
    # Get and filter data
    companies = get_companies()
    
    if city_filter != "All":
        companies = companies[companies['city'] == city_filter]
    if industry_filter != "All":
        companies = companies[companies['industry'] == industry_filter]
    if search:
        companies = companies[companies['name'].str.contains(search, case=False)]
    
    # Display data
    for _, company in companies.iterrows():
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(company['name'])
                st.write(f"🌆 {company['city']} | 🏭 {company['industry']}")
                st.write(company['description'])
            with col2:
                st.write(f"[Website]({company['website']})")
                st.write(f"[LinkedIn]({company['linkedin_url']})")
            st.markdown("---")

def show_stakeholders_page():
    st.header("Stakeholders")
    
    # Filters
    search = st.text_input("Search stakeholders")
    
    # Get and filter data
    stakeholders = get_stakeholders()
    
    if search:
        stakeholders = stakeholders[
            stakeholders['name'].str.contains(search, case=False) |
            stakeholders['role'].str.contains(search, case=False)
        ]
    
    # Display data
    for _, stakeholder in stakeholders.iterrows():
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(stakeholder['name'])
                st.write(f"🎯 {stakeholder['role']} at {stakeholder['company_name']}")
            with col2:
                if stakeholder['linkedin_url']:
                    st.write(f"[LinkedIn]({stakeholder['linkedin_url']})")
                if stakeholder['email']:
                    st.write(f"📧 {stakeholder['email']}")
            st.markdown("---")

def show_developments_page():
    st.header("Latest Developments")
    
    developments = get_developments()
    
    for _, dev in developments.iterrows():
        with st.expander(f"{dev['company_name']}: {dev['title']}"):
            st.write(f"**Date:** {dev['published_date']}")
            st.write(dev['content'])
            if dev['source_url']:
                st.write(f"[Source]({dev['source_url']})")

def show_admin_page():
    st.header("Admin Panel")
    
    # Database Management
    st.subheader("Database Management")
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.success("Cache cleared!")
    
    # Data Export
    st.subheader("Export Data")
    if st.button("Export Companies"):
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
        ["Companies", "Stakeholders", "Developments", "Admin"]
    )
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Companies", len(get_companies()))
    with col2:
        st.metric("Total Stakeholders", len(get_stakeholders()))
    with col3:
        st.metric("Latest Updates", len(get_developments()))
    
    # Page routing
    if page == "Companies":
        show_companies_page()
    elif page == "Stakeholders":
        show_stakeholders_page()
    elif page == "Developments":
        show_developments_page()
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

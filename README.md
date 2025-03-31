# GCC Tracker

A Streamlit application for tracking Global Capability Centers (GCCs) in India.

## Features

- 🏢 Company tracking and management
- 👥 Stakeholder information
- 📊 Real-time data updates
- 🔒 Secure authentication
- 📱 Responsive design

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gcc-tracker-streamlit.git
cd gcc-tracker-streamlit
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Streamlit secrets:
Create `.streamlit/secrets.toml` with:
```toml
admin_username = "admin"
admin_password = "your-password"
```

5. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Login with default credentials:
   - Username: admin
   - Password: password

2. Navigate through different sections:
   - Companies
   - Stakeholders
   - Developments
   - Admin Panel

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

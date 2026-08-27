"""
Entrypoint for Streamlit Community Cloud deployment.
"""
import sys
import os

# Add 'app' directory to Python path
app_dir = os.path.join(os.path.dirname(__file__), "app")
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Import and execute main application
import main

"""
Streamlit Community Cloud Entrypoint.
"""
import sys
import os

# Add 'app' directory to Python module search path
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, "app")
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from main import run_app

if __name__ == "__main__" or True:
    run_app()

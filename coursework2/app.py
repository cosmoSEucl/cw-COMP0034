"""
Main application entry point for the GLA Grants application.

This module initializes and runs the Flask application by importing the 
create_app function from the gla_grants_app package. It adds the parent 
directory to the Python path to ensure proper module imports.
"""
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coursework2.gla_grants_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(port=8000, debug=True)
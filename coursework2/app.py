import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coursework2.gla_grants_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
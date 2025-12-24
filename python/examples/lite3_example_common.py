import sys
import os

def setup_path():
    # Ensure we can find the lite3 package
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

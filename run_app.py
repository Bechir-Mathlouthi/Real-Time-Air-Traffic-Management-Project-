import os
import sys

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.append(src_path)

# Run the Streamlit app
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    import sys
    
    sys.argv = ["streamlit", "run", os.path.join(src_path, "app.py")]
    sys.exit(stcli.main()) 
import streamlit as st
import os
import sys
import importlib.util
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def check_python_version():
    """Checks the Python version."""
    if sys.version_info < (3, 9):
        return "❌ Python 3.9 or higher is required."
    return f"✅ Python version {sys.version.split()[0]}"

def check_env_var():
    """Checks for the presence of the GOOGLE_API_KEY environment variable."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "❌ Missing GEMINI_API_KEY in environment variables."
    return "✅ GEMINI_API_KEY found."

def check_dependency(package_name):
    """Checks if a specific Python package is installed."""
    try:
        package_name = package_name.split('==')[0].split('<')[0].split('>')[0].split('~')[0].strip()
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            return f"❌ Missing dependency: {package_name}"
        return f"✅ {package_name} is installed."
    except Exception as e:
        return f"❓ Could not check dependency {package_name}: {e}"

def get_required_packages():
    """Reads and returns a list of packages from requirements.txt."""
    required_packages = []
    try:
        with open("requirements.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    required_packages.append(line)
    except FileNotFoundError:
        st.error("❌ `requirements.txt` not found.")
    return required_packages

def run_health_check():
    """
    Performs a series of checks to ensure the application's core components are operational.
    """
    st.subheader("System Health Check")
    st.markdown("##### 🐍 Checking Python Version...")
    st.text(check_python_version())
    st.markdown("##### 🔑 Checking for Google API Key...")
    env_status = check_env_var()
    st.text(env_status)
    api_key_status = "✅" in env_status
    if api_key_status:
        st.markdown("##### 🌐 Checking LLM API Connectivity...")
        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel('gemini-2.5-flash')
            with st.spinner('Connecting to Gemini API...'):
                response = model.generate_content("Ping")
            if response and response.text:
                st.success("✅ LLM API is reachable and responding.")
            else:
                st.error("❌ LLM API is reachable but returned an unexpected response.")
        except Exception as e:
            st.error(f"❌ Failed to connect to LLM API. Error: {e}")
            st.info("This may be due to an invalid API key, network issues, or API rate limits.")

    st.markdown("##### 📦 Checking All Required Libraries...")
    required_packages = get_required_packages()
    if required_packages:
        for pkg in required_packages:
            st.text(check_dependency(pkg))

    st.markdown("\n##### ✅ Health check completed.")


def main():
    """
    Main function to run the Streamlit app.
    """
    st.title("AI Report Generator")
    st.markdown("An automated system for generating professional reports from raw data.")

    if st.button("Run System Health Check"):
        st.empty()
        run_health_check()

    st.divider()

    st.header("Upload Your Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file:
        st.write("File uploaded successfully!")

if __name__ == "__main__":
    main()

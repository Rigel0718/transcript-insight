import streamlit as st
import requests
import os

# --- App Configuration ---
st.set_page_config(
    page_title="Transcript Insight",
    page_icon="📄",
    layout="centered",
)

# --- Backend API URL ---
FASTAPI_URL = "http://api:8000/upload/"

st.title("📄 Transcript Insight")
st.markdown(
    "Upload a PDF of a transcript, and this tool will extract the key information."
)

uploaded_file = st.file_uploader(
    "Choose a PDF file", type="pdf", help="Please upload a valid PDF file."
)

if uploaded_file is not None:

    # Show a spinner while processing
    with st.spinner("Processing your document... please wait."):
        try:
            # Prepare the file for the POST request
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}

            # FastAPI backend
            response = requests.post(FASTAPI_URL, files=files, timeout=300) # 5-minute timeout

            # Check the response from the backend
            if response.status_code == 200:
                result = response.json()
                final_text = result.get("final_result")

                st.success("Processing complete!")
                st.subheader("Extracted Information:")
                st.text_area("Result", final_text, height=400)
            else:
                # Handle errors from the backend
                error_detail = response.json().get("detail", "An unknown error occurred.")
                st.error(f"Error from server (Code: {response.status_code}): {error_detail}")

        except requests.exceptions.RequestException as e:
            # Handle network or connection errors
            st.error(f"Could not connect to the backend. Please ensure it's running. Error: {e}")
        except Exception as e:
            # Handle other unexpected errors
            st.error(f"An unexpected error occurred: {e}")

else:
    st.info("Please upload a PDF file to get started.")


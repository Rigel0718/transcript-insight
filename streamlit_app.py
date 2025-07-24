import streamlit as st
import httpx
import base64
import asyncio
import websockets
import json

# --- App Configuration ---
st.set_page_config(
    page_title="Transcript Insight",
    page_icon="📄",
    layout="centered",
)

# --- Backend API URL ---
FASTAPI_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8000/ws"

st.title("📄 Transcript Insight")
st.markdown(
    "Upload a PDF of a transcript, and this tool will extract the key information."
)

# --- Session State Initialization ---
if 'final_text' not in st.session_state:
    st.session_state.final_text = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None

uploaded_file = st.file_uploader(
    "Choose a PDF file", type="pdf", help="Please upload a valid PDF file."
)

async def listen_to_websocket(placeholder):
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    if "name" in data and "status" in data:
                        if data["status"] == "start":
                            placeholder.text(f"Processing: {data['name']}...")
                        elif data["status"] == "end":
                            if "duration" in data:
                                placeholder.text(f"Finished: {data['name']} in {data['duration']}s")
                            else:
                                placeholder.text(f"Finished: {data['name']}")
                    if data.get("event") == "eof":
                        break
                except asyncio.TimeoutError:
                    break
    except websockets.exceptions.ConnectionClosed:
        pass

async def process_file(uploaded_file, status_placeholder):
    async def upload_and_get_result():
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{FASTAPI_URL}/upload/", files=files, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            st.session_state.final_text = result.get("final_result")
        else:
            response.raise_for_status()

    try:
        await asyncio.gather(
            listen_to_websocket(status_placeholder),
            upload_and_get_result()
        )
    except httpx.RequestError as e:
        st.error(f"Could not connect to the backend. Please ensure it's running. Error: {e}")
        st.session_state.final_text = None
    except httpx.HTTPStatusError as e:
        error_detail = e.response.json().get("detail", "An unknown error occurred.")
        st.error(f"Error from server (Code: {e.response.status_code}): {error_detail}")
        st.session_state.final_text = None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.session_state.final_text = None

if uploaded_file is not None:
    # If a new file is uploaded, reset the session state
    if uploaded_file.name != st.session_state.uploaded_file_name:
        st.session_state.final_text = None
        st.session_state.analysis_results = None
        st.session_state.uploaded_file_name = uploaded_file.name

    if st.session_state.final_text is None:
        status_placeholder = st.empty()
        with st.spinner("Processing your document... please wait."):
            asyncio.run(process_file(uploaded_file, status_placeholder))

if st.session_state.final_text is not None:
    st.success("Processing complete!")
    st.subheader("Extracted Information:")
    if isinstance(st.session_state.final_text, dict):
        st.json(st.session_state.final_text, expanded=False) 
    else:
        st.text_area("Result", str(st.session_state.final_text), height=400)

    if st.button("Analyze Transcript"):
        with st.spinner("Analyzing the transcript..."):
            
            async def analyze():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(f"{FASTAPI_URL}/analyze", json={"transcript": st.session_state.final_text}, timeout=300)
                    if response.status_code == 200:
                        st.session_state.analysis_results = response.json()
                    else:
                        st.error("Failed to analyze the transcript. Please try again.")
                        st.session_state.analysis_results = None
                except httpx.RequestError as e:
                    st.error(f"Could not connect to the backend. Please ensure it's running. Error: {e}")
                    st.session_state.analysis_results = None
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
                    st.session_state.analysis_results = None
            
            asyncio.run(analyze())


if st.session_state.analysis_results is not None:
    st.header("Report")
    st.write(st.session_state.analysis_results.get("report"))

    st.header("Visualizations")
    for img_base64 in st.session_state.analysis_results.get("visualizations", []):
        st.image(base64.b64decode(img_base64))
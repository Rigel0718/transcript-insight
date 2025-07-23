# Transcript Insight

This project is a web application for analyzing transcripts. It consists of a FastAPI backend and a Streamlit frontend.

## Project Structure

The project is divided into two main components:

-   **FastAPI Backend:** The backend is a FastAPI application that provides an API for processing and analyzing transcripts. The main application file is `main.py`, and the Dockerfile for the backend is `Dockerfile.api`.
-   **Streamlit Frontend:** The frontend is a Streamlit application that provides a user interface for interacting with the backend. The main application file is `streamlit_app.py`, and the Dockerfile for the frontend is `Dockerfile.streamlit`.

## How it Works

The project uses Docker to containerize the backend and frontend applications. The `docker-compose.yml` file is used to orchestrate the two services.

-   The FastAPI backend runs on port 8000.
-   The Streamlit frontend runs on port 8501.

The frontend communicates with the backend to process and analyze transcripts.

## Parser

The parser uses a graph-based approach to analyze transcripts. It leverages the Upstage API for OCR and document parsing, and it includes a subgraph for handling OCR on specific elements.

![ParseGraph](images/ParseGraph.png)

# AI Artistry Pipeline: An Automated Generative Art Gallery
<!-- Replace with your live app URL! -->

This project is a complete, end-to-end data engineering pipeline that automatically generates, processes, and displays unique AI art in a polished web gallery. It showcases a modern, cloud-native approach to building automated ETL processes and AI-powered applications.
The creative engine of this project is a multi-stage LLM agent named '**The Alchemist**', which is tasked with generating "beyond imagination" art concepts based on the custom theme of "**Nocturne & Mechanism**".

## Architecture Overview
The project is divided into two main components: a serverless ETL pipeline for content generation and a Streamlit web application for presentation.

### The Automated ETL Pipeline:
1. **Generation (generate.py):** An LLM agent ("The Alchemist") is prompted with the core theme to generate a unique two-word concept. This concept is then enhanced by a second LLM call into a structured JSON object containing a detailed final prompt and the creative reasoning behind it.
2. **Image Creation:** The final prompt is sent to a generative image model (e.g., Gemini Imagen) to create a pair of high-resolution art pieces.
3. **Processing & Storage (upload.py):**
- The generated images and their JSON metadata are saved locally.
- High-quality thumbnails are created for web optimization.
- All assets (full-size images, thumbnails, JSON metadata) are uploaded to a versioned folder structure in Google Cloud Storage (GCS).
4. **Data Warehousing (upload.py):**
- The JSON metadata is consolidated into a newline-delimited JSON file.
- This file is staged in GCS and then loaded into a Google BigQuery table, which serves as the central metadata catalog for the entire gallery.

### The Web Application (gallery.py, pages/details.py):
1. **Frontend**: A multi-page Streamlit application provides a polished user interface.
2. **Data Source:** The app queries the BigQuery table to fetch the metadata for all generated art.
3. **Gallery View:** The main page displays a shuffled grid of clickable thumbnails. The image URLs are constructed directly from the GCS paths stored in BigQuery.
4. **Detail View:** Clicking a thumbnail navigates the user to a dedicated details page, showing the full-resolution image alongside the AI's creative reasoning and the final prompt used for generation.

## Tech Stack
- Cloud Platform: Google Cloud Platform (GCP)
- Data Warehouse: Google BigQuery
- Object Storage: Google Cloud Storage (GCS)
- LLM & Generative AI: Google Gemini API (for text and image generation)
- Web Framework: Streamlit
- Core Python Libraries: pandas, google-cloud-bigquery, google-cloud-storage, Pillow
- Environment Management: Conda & Pip

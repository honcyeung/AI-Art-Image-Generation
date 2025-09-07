import gallery

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv
import os

load_dotenv()
PROJECT_ID = os.environ["PROJECT_ID"]
GCP_BUCKET_NAME = os.environ["GCP_BUCKET_NAME"]
BIGQUERY_DATASET_ID = os.environ["BIGQUERY_DATASET_ID"]
BIGQUERY_TABLE_ID2 = os.environ["BIGQUERY_TABLE_ID2"]

@st.cache_data(ttl = 3600)
def fetch_single_image_data(images):

    try:
        client = bigquery.Client(project = PROJECT_ID)
        table_ref = f"{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID2}"
        query = f"""
            SELECT * FROM `{table_ref}`
            WHERE images = @images
            LIMIT 1
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters = [
                bigquery.ScalarQueryParameter("images", "STRING", images)
            ]
        )
        df = client.query(query, job_config = job_config).to_dataframe()
        if not df.empty:
            return df.iloc[0]

    except Exception as e:
        st.error(f"Failed to fetch image data: {e}")

        return None

def main():

    st.set_page_config(page_title = "Image Details", page_icon = "🎨", layout = "wide")
    css_content = gallery.load_custom_css()
    st.markdown(f'<style>{css_content}</style>', unsafe_allow_html = True)

    selected_image = st.query_params.get("images")
    if not selected_image:
        st.warning("Please select an image from the main gallery first.")
        st.link_button("Back to Gallery", "/")
        st.stop()

    image_data = fetch_single_image_data(selected_image)    
    if image_data is None:
        st.error("Could not find the selected image. It may have been moved or deleted.")
        st.link_button("Back to Gallery", "/")
        st.stop()
    
    col_title, col_button = st.columns([4, 1])
    with col_title:
        st.title(image_data['prompt_concept'])
    with col_button:
        st.markdown("<div class='back-button-container'>", unsafe_allow_html = True)
        if st.button("Back to Gallery"):
            st.switch_page("gallery.py")
    st.divider()

    col1, col2 = st.columns([2, 3]) 
    with col1:
        st.image(image_data["images_public_url"])

    with col2:
        st.subheader("Creative Reasoning by AI")
        st.info(f"{image_data['creative_concept']}")
        st.text_area(
            "Final Prompt",
            value = image_data['final_prompt'],
            height = 400,
            key = "final_prompt_textarea" # Give it a key for CSS targeting
        )

if __name__ == "__main__":
    main()
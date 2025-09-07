import os
import glob
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from google.cloud import storage, bigquery
import random

load_dotenv()
PROJECT_ID = os.environ["PROJECT_ID"]
GCP_BUCKET_NAME = os.environ["GCP_BUCKET_NAME"]
BIGQUERY_DATASET_ID = os.environ["BIGQUERY_DATASET_ID"]
BIGQUERY_TABLE_ID2 = os.environ["BIGQUERY_TABLE_ID2"]

def load_custom_css():

    try:
        with open("./style.css", "r") as f:
            css_content = f.read()
    
        return css_content
    except Exception as e:
        st.error(f"An error occurred while reading the CSS file: {e}")

@st.cache_data(ttl = 600)
def fetch_gallery_metadata():

    table_ref = f"{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID2}"
    query = f"""
            SELECT *
            FROM `{table_ref}`
            ORDER BY id    
            """

    try:
        client = bigquery.Client(project = PROJECT_ID)
        df = client.query(query).to_dataframe()
        print(f"Successfully fetched {len(df)} records.")

        return df
    except Exception as e:
        st.error(f"Failed to connect to BigQuery. Please check your GCP authentication. Error: {e}")

        return pd.DataFrame()

def shuffle_dataframe(df):

    unique_concepts = df['prompt_concept'].unique()
    random.shuffle(unique_concepts)
    
    shuffled_df = pd.DataFrame()
    for concept in unique_concepts:
        pair_df = df[df['prompt_concept'] == concept]
        shuffled_pair_df = pair_df.sample(frac = 1)
        shuffled_df = pd.concat([shuffled_df, shuffled_pair_df])

    return shuffled_df

def main():
    
    st.markdown("<a id='top'></a>", unsafe_allow_html = True)
    st.set_page_config(
        page_title = "Digital Art Gallery",
        page_icon = "🎨",
        layout = "wide"
    )
    css_content = load_custom_css()
    st.markdown(f'<style>{css_content}</style>', unsafe_allow_html = True)

    # Initialize session state for detail view if it doesn't exist
    if 'selected_image_id' not in st.session_state:
        st.session_state.selected_image_id = None

    # Add a title and an introduction
    with st.container():
        st.title("AI Artistry Gallery")
        st.markdown("An automated pipeline that generates unique concepts and visualizes them using AI.")
        st.divider()

    # Fetch the data from BigQuery
    df = fetch_gallery_metadata()
    if df.empty:
        st.warning("No images found in the database. Please run the generation pipeline.")
        st.stop()

        return

    # If not, we shuffle it once and store it in the session state.
    if 'shuffled_list' not in st.session_state:
        print("Shuffling data...")
        st.session_state.shuffled_list = shuffle_dataframe(df)
    
    if st.button("Shuffle Gallery", type = "primary"):
    # Delete the old list from the session state. On the next re-run,
    # the 'if' block above will trigger again, creating a new shuffled list.
        del st.session_state.shuffled_list
        st.rerun()

    st.header("The Gallery")
    cols = st.columns(4)

    for i, row in st.session_state.shuffled_list.iterrows():
        col = cols[i % len(cols)]
        with col: 
            st.markdown(
                f"""
                    <a href="/details?images={row['images']}" target="_self">
                        <img src="{row['thumbnails_public_url']}" alt="{row['prompt_concept']}">
                    </a>
                    """, unsafe_allow_html = True
                )

    st.markdown("""
        <div class="footer">
            <a href="#top" class="back-to-top" title="Back to Top">
                <i class="fa-solid fa-circle-chevron-up"></i>
            </a>
        </div>
    """, unsafe_allow_html = True)
    
if __name__ == "__main__":
    main()

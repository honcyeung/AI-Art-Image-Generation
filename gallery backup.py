from upload import upload_to_gcp_bucket

from PIL import Image
import os
import glob
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from google.cloud import storage, bigquery
import db_dtypes
import random

load_dotenv()
PROJECT_ID = os.environ["PROJECT_ID"]
GCP_BUCKET_NAME = os.environ["GCP_BUCKET_NAME"]
BIGQUERY_DATASET_ID = os.environ["BIGQUERY_DATASET_ID"]
BIGQUERY_TABLE_ID = os.environ["BIGQUERY_TABLE_ID"]

def load_custom_css():
    
    st.markdown("""
        <style>
            /* Import a custom font from Google Fonts */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            
            body {
                font-family: 'Inter', sans-serif;
            }

            /* Style the image thumbnails in the gallery */
            .stImage > img {
                border-radius: 12px;
                box-shadow: 0 8px 16px rgba(0,0,0,0.1);
                transition: transform 0.2s ease-in-out;
                cursor: pointer;
            }
            .stImage > img:hover {
                transform: scale(1.05);
            }

            /* Style the main "Shuffle Gallery" button */
            .stButton > button {
                border-radius: 8px;
                border: 2px solid #2E2E2E;
                background-color: #FFFFFF;
                color: #2E2E2E;
                font-weight: 600;
                transition: all 0.2s ease-in-out;
            }
            .stButton > button:hover {
                background-color: #2E2E2E;
                color: #FFFFFF;
                border-color: #2E2E2E;
            }
            
            /* Style for the detail view container */
            .detail-container {
                background-color: #f9f9f9;
                padding: 2rem;
                border-radius: 15px;
                border: 1px solid #e6e6e6;
            }
        </style>
    """, unsafe_allow_html = True)

@st.cache_data(ttl = 600)
def fetch_gallery_metadata():

    table_ref = f"{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}"
    query = f"""
            SELECT 
            id, prompt_concept, final_prompt
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

@st.cache_data(ttl = 600)
def list_blobs_with_prefix(folder_name):

    try:
        storage_client = storage.Client(project = PROJECT_ID)
        blobs = storage_client.list_blobs(GCP_BUCKET_NAME, prefix = folder_name)
        filenames = [os.path.basename(blob.name) for blob in blobs]

        return filenames
    except Exception as e:
        print(f"Error :{e}")

        return

def create_image_public_url(df, list_of_files, name = "images"):

    df_files = pd.DataFrame(list_of_files, columns = [name])
    df_files["id"] = df_files[name].str.split("_").str[:2].str.join("_")
    df2 = df.merge(df_files, on = "id")

    url = f"https://storage.googleapis.com/{GCP_BUCKET_NAME}/{name}/"
    df2[f"{name}_public_url"] = url + df2[name]

    return df2

def create_thumbnail_public_url(df, list_of_files, name = "thumbnails"):

    df_files = pd.DataFrame(list_of_files, columns = [name])
    df_files["images"] = df_files[name].str.replace("_thumbnail.png", ".png")
    df2 = df.merge(df_files, on = "images")

    url = f"https://storage.googleapis.com/{GCP_BUCKET_NAME}/{name}/"
    df2[f"{name}_public_url"] = url + df2[name]

    return df2

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
    
    # Set up the page configuration (title, icon, layout)
    st.set_page_config(
        page_title = "Digital Art Gallery",
        page_icon = "🎨",
        layout = "wide"
    )
    load_custom_css()

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

    # Get GCS public urls for thumbnails and images and merge with BigQuery data. Shuffle the final df
    image_names = list_blobs_with_prefix("images")
    thumbnail_names = list_blobs_with_prefix("thumbnails")

    if not image_names or not thumbnail_names:
        print(f"No image or thumbnail file name available.")

        return 
    df2 = create_image_public_url(df, image_names)
    df3 = create_thumbnail_public_url(df2, thumbnail_names)
    df_shuffled = shuffle_dataframe(df3)
    # df3.to_csv('test.csv', index = False)
    # return




    # If not, we shuffle it once and store it in the session state.
    if 'shuffled_list' not in st.session_state:
        print("Shuffling data...")
        st.session_state.shuffled_list = shuffle_dataframe(df3)
    
    if st.button("Shuffle Gallery", type = "primary"):
    # We just delete the old list from the session state. On the next re-run,
    # the 'if' block above will trigger again, creating a new shuffled list.
        del st.session_state.shuffled_list
        st.rerun() # Immediately rerun the script to show the new order

    st.header("The Gallery")
    cols = st.columns(4)

    for i, row in df_shuffled.iterrows():
        col = cols[i % len(cols)]
        with col:
            st.image(
                row["thumbnails_public_url"],
                caption = f"{row['prompt_concept']}",
            )

if __name__ == "__main__":
    main()

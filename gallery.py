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
    
    # 1. Set up the page configuration (title, icon, layout)
    st.set_page_config(
        page_title = "Digital Art Gallery",
        page_icon = "🎨",
        layout = "wide"
    )

    # 2. Add a title and an introduction
    st.title("🎨 AI Artistry Gallery")
    st.markdown("An automated pipeline that generates unique concepts and visualizes them using AI.")

    # 3. Fetch the data from BigQuery
    df = fetch_gallery_metadata()
    if df.empty:
        st.warning("No images found in the database. Please run the generation pipeline.")
        st.stop()

        return

    # 4. Get GCS public urls for thumbnails and images and merge with BigQuery data
    image_names = list_blobs_with_prefix("images")
    thumbnail_names = list_blobs_with_prefix("thumbnails")

    if not image_names or not thumbnail_names:
        print(f"No image or thumbnail file name available.")

        return 
    df2 = create_image_public_url(df, image_names)
    df3 = create_thumbnail_public_url(df2, thumbnail_names)
    # df3 = df3.drop_duplicates()
    # print(df3.loc[0, "thumbnails_public_url"])
    # df3.to_csv('test.csv', index = False)
    # return

    df_shuffled = shuffle_dataframe(df3)

    # 5. Display the gallery grid
    st.header("The Gallery")

    # Define the number of columns for the grid
    cols = st.columns(4)

    for i, row in df_shuffled.iterrows():
        col = cols[i % len(cols)]
        with col:
            st.image(
                row["thumbnails_public_url"],
                caption = f"Concept: {row['prompt_concept']}",
                # width = True
            )

if __name__ == "__main__":
    main()

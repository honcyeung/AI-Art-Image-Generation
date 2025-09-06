import os
import glob
from google.cloud import storage, bigquery
from dotenv import load_dotenv
import json
import pandas as pd

load_dotenv()
PROJECT_ID = os.environ["PROJECT_ID"]
GCP_BUCKET_NAME = os.environ["GCP_BUCKET_NAME"]
BIGQUERY_DATASET_ID = os.environ["BIGQUERY_DATASET_ID"]
BIGQUERY_TABLE_ID = os.environ["BIGQUERY_TABLE_ID"]
BIGQUERY_TABLE_ID2 = os.environ["BIGQUERY_TABLE_ID2"]

def upload_to_gcp_bucket(local_folder_path, file_format, gcp_destination_folder):

    try:
        storage_client = storage.Client(project = PROJECT_ID)
        bucket = storage_client.bucket(GCP_BUCKET_NAME)

        file_paths = glob.glob(os.path.join(local_folder_path, f"*.{file_format}"))
        if not file_paths:
            print(f"No {file_format} files found in {local_folder_path}.")

            return
        
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            blob = bucket.blob(os.path.join(gcp_destination_folder, file_name))
            blob.upload_from_filename(file_path)

        print(f"--- Successfully uploaded {len(file_paths)} {file_format} files. ---")
    except Exception as e:
        print(f"An error occurred during GCS upload: {e}")

        return
    
def flatten_json(filepath):

    try:
        with open(filepath, "r") as f: 
            data = json.load(f)

        flattened_data = {}
        for k, v in data.items():
            if isinstance(v, dict):
                flattened_data["id"] = k
                for sub_k, sub_v in v.items():
                    flattened_data[sub_k] = sub_v
            else:
                flattened_data[k] = v

        return flattened_data
    except Exception as e:
        print(f"Error loading JSON: {e}")

        return

def convert_to_ndjson(input_filepath, output_filepath, output_file):

    try:
        output_file = os.path.join(output_filepath, output_file)
        list_of_files = glob.glob(os.path.join(input_filepath, "*.json"))
        if not list_of_files:
            print(f"No json files found in {input_filepath}.")

            return
        
        flattened_data_list = []
        for file in list_of_files:
            with open(file, "r") as f:
                data = json.load(f)
                flattened_data = flatten_json(file)
                flattened_data_list.append(flattened_data)
        
        with open(output_file, "w") as f:
            for item in flattened_data_list:
                json_string = json.dumps(item)
                f.write(json_string + "\n")
    
        print(f"--- Successfully converted and wrote {len(flattened_data_list)} records to {output_file}. ---")

        return flattened_data_list

    except Exception as e:
        print(f"Error converting to ndjson: {e}")

        return

def load_ndjson_from_gcs_to_bigquery(output_filepath, gcp_destination_folder = "ndjson_prompt", gcp_destination_file = "ndjson_prompts.json"):

    try:
        upload_to_gcp_bucket(output_filepath, "json", gcp_destination_folder)
    except Exception as e:
        print(f"Error uploading ndjson to GCS: {e}")

        return
    
    try:
        client = bigquery.Client(project = PROJECT_ID)

        BIGQUERY_SCHEMA = [
            bigquery.SchemaField("id", "STRING", mode = "REQUIRED"),
            bigquery.SchemaField("prompt_concept", "STRING", mode = "NULLABLE"),
            bigquery.SchemaField("creative_concept", "STRING", mode = "NULLABLE"),
            bigquery.SchemaField("final_prompt", "STRING", mode = "NULLABLE"),
        ]

        job_config = bigquery.LoadJobConfig(
            source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            schema = BIGQUERY_SCHEMA,
            write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        gcs_uri = f"gs://{GCP_BUCKET_NAME}/{gcp_destination_folder}/{gcp_destination_file}"
        table_ref = f"{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}"
        load_job = client.load_table_from_uri(
            gcs_uri, table_ref, job_config = job_config
        )

        load_job.result() 

        destination_table = client.get_table(table_ref)
        print(f"Job finished. Loaded {destination_table.num_rows} rows.")

    except Exception as e:
        print(f"Error loading ndjson to BigQuery: {e}")

        return

def create_thumbnail(image_path, thumbnail_path, size = (256, 256)):

    try:
        file_paths = glob.glob(os.path.join(image_path, "*.png"))
        if not file_paths:
            print(f"No images found in {image_path}.")

            return
        
        thumbnail_filenames = []
        for file in file_paths:
            basenames = os.path.basename(file).split(".")
            thumbnail_filename = f"{basenames[0]}_thumbnail.{basenames[1]}"
            with Image.open(file) as img:
                img.thumbnail(size)
                img.save(os.path.join(thumbnail_path, thumbnail_filename))
            print(f"Successfully created thumbnail: {thumbnail_filename}")
            thumbnail_filenames.append(thumbnail_filename)

        return thumbnail_filenames
    except Exception as e:
        print(f"Error: {e}")

        return

# new parts

def fetch_image_metadata():

    table_ref = f"{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}"
    query = f"""
            SELECT 
            id, prompt_concept, creative_concept, final_prompt
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

def load_df_to_bigquery(df):
    
    try:
        client = bigquery.Client(project = PROJECT_ID)

        BIGQUERY_SCHEMA = [
            bigquery.SchemaField("id", "STRING", mode = "REQUIRED"),
            bigquery.SchemaField("prompt_concept", "STRING", mode = "NULLABLE"),
            bigquery.SchemaField("creative_concept", "STRING", mode = "NULLABLE"),
            bigquery.SchemaField("final_prompt", "STRING", mode = "NULLABLE"),
            bigquery.SchemaField("images", "STRING", mode = "NULLABLE"),
            bigquery.SchemaField("images_public_url", "STRING", mode = "NULLABLE"),
            bigquery.SchemaField("thumbnails", "STRING", mode = "NULLABLE"),
            bigquery.SchemaField("thumbnails_public_url", "STRING", mode = "NULLABLE"),
        ]

        job_config = bigquery.LoadJobConfig(
            schema = BIGQUERY_SCHEMA,
            write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        table_ref = f"{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID2}"
        load_job = client.load_table_from_dataframe(
            df, table_ref, job_config = job_config
        )

        load_job.result() 

        destination_table = client.get_table(table_ref)
        print(f"Job finished. Loaded {destination_table.num_rows} rows.")
    except Exception as e:
        print(f"Error loading dataframe to BigQuery: {e}")

        return

def run_upload_pipeline(image_path, prompt_path, output_ndjson_path, output_ndjson_file, thumbnail_path):

    # upload_to_gcp_bucket(image_path, "png", "images")
    # upload_to_gcp_bucket(prompt_path, "json", "prompts")
    # flattened_data_list = convert_to_ndjson(prompt_path, output_ndjson_path, output_ndjson_file)
    # load_ndjson_from_gcs_to_bigquery(output_ndjson_path, gcp_destination_folder = "ndjson_prompt", gcp_destination_file = output_ndjson_file)
    # thumbnail_filenames = create_thumbnail(image_path, thumbnail_path)
    # upload_to_gcp_bucket(thumbnail_path, "png", "thumbnails")


    # need to fix the silly df to bigquery problem

    df = fetch_image_metadata()
    image_names = list_blobs_with_prefix("images")
    thumbnail_names = list_blobs_with_prefix("thumbnails")
    df2 = create_image_public_url(df, image_names)
    df3 = create_thumbnail_public_url(df2, thumbnail_names)
    load_df_to_bigquery(df3)
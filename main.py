import generate
import save_display
import upload
import gallery

import subprocess
import sys
import warnings
warnings.filterwarnings('ignore') 

IMAGE_PATH = "./images/"
PROMPT_PATH = "./prompts/"
OUTPUT_NDJSON_PATH = "./ndjson_prompt/"
OUTPUT_NDJSON_FILE = "ndjson_prompts.json"
THUMBNAIL_PATH = "./thumbnails/"

GEMINI_TEXT_MODEL = "gemini-2.5-flash-lite" 
# GEMINI_IMAGE_MODEL = "imagen-3.0-generate-002"
GEMINI_IMAGE_MODEL = "imagen-4.0-ultra-generate-001"

TEMPERATURE = 1
NUMBER_OF_IMAGES = 2
ASPECT_RATIO = "3:4" # "1:1", "3:4", "4:3", "9:16", and "16:9". Default "1:1"
UNIQUE_CONCEPT = 0 # same concept may have more than 1 image; 0 to show all images, 1 to show 1 image per concept

def main():

    prompt_concept, initial_image_prompt, images = generate.run_generate_pipeline(GEMINI_TEXT_MODEL, GEMINI_IMAGE_MODEL, TEMPERATURE, NUMBER_OF_IMAGES, ASPECT_RATIO)
    save_display.run_save_and_display_pipeline(prompt_concept, initial_image_prompt, images)
    upload.run_upload_pipeline(IMAGE_PATH, PROMPT_PATH, OUTPUT_NDJSON_PATH, OUTPUT_NDJSON_FILE, THUMBNAIL_PATH)

    # Streamlit app
    command = [sys.executable, "-m", "streamlit", "run", "gallery.py", "--", f"--unique_concept={UNIQUE_CONCEPT}"]

    print("Starting Streamlit app...")
    try:
        subprocess.run(command, check = True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit app: {e}")

if __name__ == "__main__":
    main()
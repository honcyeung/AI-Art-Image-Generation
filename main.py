import generate
import save_display
import upload
import gallery

import warnings
warnings.filterwarnings('ignore') 

IMAGE_PATH = "./images/"
PROMPT_PATH = "./prompts/"
OUTPUT_NDJSON_PATH = "./ndjson_prompt/"
OUTPUT_NDJSON_FILE = "ndjson_prompts.json"
THUMBNAIL_PATH = "./thumbnails/"

def read_theme():

    try:
        with open("theme.txt", "r") as f:
            theme = f.read().strip()
            
            return theme
    except Exception as e:
        print(f"Error reading theme: {e}")

        return "digital art of a futuristic cityscape"

def main():

    # prompt_concept, initial_image_prompt, images = generate.run_generate_pipeline(theme = read_theme())
    # filenames = save_display.run_save_and_display_pipeline(prompt_concept, initial_image_prompt, images)
    # upload.run_upload_pipeline(IMAGE_PATH, PROMPT_PATH, OUTPUT_NDJSON_PATH, OUTPUT_NDJSON_FILE, THUMBNAIL_PATH)

if __name__ == "__main__":
    main()
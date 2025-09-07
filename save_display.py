import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime
import uuid
import io
import os
import json

IMAGE_PATH = "./images/"
EDITED_IMAGE_PATH = "./edited_images/"
PROMPT_PATH = "./prompts/"

def create_unique_filename(prompt_concept):

    current_time = datetime.now().strftime("%Y%m%d")
    concept_slug = prompt_concept.replace(" ", "-").lower()
    uuid_string = str(uuid.uuid4())[:8]
    filename = f"{current_time}_{concept_slug}_{uuid_string}.png"

    return filename

def create_filename_prefix(prompt_concept):

    current_time = datetime.now().strftime("%Y%m%d")
    concept_slug = prompt_concept.replace(" ", "-").lower()
    prefix = f"{current_time}_{concept_slug}"

    return prefix

def create_unique_filename(prefix):

    uuid_string = str(uuid.uuid4())[:8]
    filename = f"{prefix}_{uuid_string}.png"

    return filename

def save_image(image, filename):

    try:
        image_bytes_io = io.BytesIO()
        image_bytes_io.write(image.image.image_bytes)
        image_bytes_io.seek(0)
        raw_bytes = image_bytes_io.getvalue()
        path = os.path.join(IMAGE_PATH, f"{filename}")

        with open(path, "wb") as f:
            f.write(raw_bytes)
        print(f"Image saved to {path}")

        return
    except Exception as e:
        print(f"Error: {e}")

        return

def name_and_save_files(prompt_concept, initial_image_prompt, images):

    prefix = create_filename_prefix(prompt_concept)
    filenames = []
    for image in images:
        filename = create_unique_filename(prefix)
        save_image(image, filename)
        filenames.append(filename)
    
    initial_image_prompt["prompt_concept"] = prompt_concept
    prompt_json = dict()
    prompt_json[prefix] = initial_image_prompt

    try:
        with open(f"{PROMPT_PATH}/{prefix}.json", "w") as f:
            json.dump(prompt_json, f, indent = 4)
        print(f"Prompt JSON saved to {PROMPT_PATH}/{prefix}.json")
    except Exception as e:
        print(f"Error saving prompt JSON: {e}")

    return filenames

def display_images_side_by_side(filenames):

    try:
        image1_path = f"{IMAGE_PATH}/{filenames[0]}"
        image2_path = f"{IMAGE_PATH}/{filenames[1]}"
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)

        fig, axes = plt.subplots(1, 2, figsize = (14, 7))

        axes[0].imshow(img1)
        axes[0].set_title('Generated Image 1')
        axes[0].axis('off')  

        axes[1].imshow(img2)
        axes[1].set_title('Generated Image 2')
        axes[1].axis('off')  

        plt.tight_layout(pad = 1.7)
        plt.show()

    except FileNotFoundError as e:
        print(f"Error: One of the files was not found. {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def run_save_and_display_pipeline(prompt_concept, initial_image_prompt, images):
    
    filenames = name_and_save_files(prompt_concept, initial_image_prompt, images)
    display_images_side_by_side(filenames)

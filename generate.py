from dotenv import load_dotenv
import os
import requests
from google import genai
from google.genai import types
import io
import json

TEMPERATURE = 0.9
GEMINI_TEXT_MODEL = "gemini-2.5-flash-lite" 
# GEMINI_TEXT_MODEL = "gemini-2.5-flash" 
GEMINI_IMAGE_MODEL = "imagen-3.0-generate-002"
# GEMINI_IMAGE_MODEL = "imagen-4.0-ultra-generate-001"
IMAGE_PATH = "./images/"
NUMBER_OF_IMAGES = 2

load_dotenv()
PROMPTLAYER_API_KEY = os.environ["PROMPTLAYER_API_KEY"]
PROMPT_TEMPLATE_IDENTIFIER = os.environ["PROMPT_TEMPLATE_IDENTIFIER"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
PROJECT_ID = os.environ["PROJECT_ID"]
LOCATION = os.environ["REGION"]

client = genai.Client(api_key = GEMINI_API_KEY)
vertext_client = genai.Client(
    vertexai = True, project = PROJECT_ID, location = LOCATION
    )

def get_prompt():
  
    url = f"https://api.promptlayer.com/prompt-templates/{PROMPT_TEMPLATE_IDENTIFIER}"
    headers = {
        "X-API-KEY": PROMPTLAYER_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers = headers)
    response.raise_for_status()
    data = response.json()
    
    messages = data.get("prompt_template", {}).get("messages", {})

    system_prompts = []
    for m in messages:
        if m.get("role", {}) == "system":
            system_prompt = m.get("content", [])[0].get("text", "")
            system_prompts.append(system_prompt)

    if not system_prompts:
        raise ValueError("System prompts not found in the PromptLayer response.")

    return system_prompts

def create_prompt_concept(prompt, theme):

    formatted_prompt = prompt.format(theme = theme)
    try:
        response = client.models.generate_content(
            model = GEMINI_TEXT_MODEL,
            contents = formatted_prompt,
            config = types.GenerateContentConfig(
            temperature = TEMPERATURE, 
        )
    )
        if response.text:
            return response.text
        else:
            print("No text generated.")

            return
    except Exception as e:
        print(f"Error: {e}")

        return

def prompt_enhancer(prompt_concept, system_prompt):

    if not prompt_concept:
        print("No prompt concept provided for enhancement.")

        return

    try:
        response_schema = {
            "properties": {
                "creative_concept": {"type": "STRING"},
                "final_prompt": {"type": "STRING"},
            },
            "required": [
                "creative_concept",
                "final_prompt"],
            "type": "OBJECT",
        }

        response = client.models.generate_content(
            model = GEMINI_TEXT_MODEL,
            contents = prompt_concept,
            config = types.GenerateContentConfig(
            system_instruction = system_prompt,
            temperature = TEMPERATURE, 
            response_mime_type = "application/json",
            response_schema = response_schema
        )
    )
        if response.text:
            try:
                initial_image_prompts = json.loads(response.text)

                return initial_image_prompts
            except json.JSONDecodeError as e:
                print("Error: LLM did not return valid JSON.")
                
                return
        else:
            print("No text generated.")

            return
    except Exception as e:
        print(f"Error: {e}")

        return
    
def generate_initial_image(prompt, number_of_images = NUMBER_OF_IMAGES):

    try:
        response = vertext_client.models.generate_images(
            model = GEMINI_IMAGE_MODEL,
            prompt = prompt,
            config = types.GenerateImagesConfig(
                number_of_images = number_of_images,
                # aspect_ratio = "1:1",
                # output_mime_type = 'image/jpeg',
            )
        )

        if response.generated_images:
            return response.generated_images
        else:
            print("No images generated.")

            return
    except Exception as e:
        print(f"Error: {e}")

        return

def run_generate_pipeline(theme):
    
    system_prompts = get_prompt()
    prompt_concept = create_prompt_concept(system_prompts[0], theme)
    print(prompt_concept)
    print()
    initial_image_prompt = prompt_enhancer(prompt_concept, system_prompts[1])
    print(initial_image_prompt["creative_concept"])
    print()
    print(initial_image_prompt["final_prompt"])
    images = generate_initial_image(initial_image_prompt["final_prompt"])
    
    return prompt_concept, initial_image_prompt, images
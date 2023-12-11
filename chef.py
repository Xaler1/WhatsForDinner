from openai import OpenAI
from keys import openai_key
import requests
from PIL import Image
import spices

recipes_prompt = """You are a helpful cooking assistant. 
The user will send you a list of ingredients as well as some other parameters.
Your job is to come up with appropriate recipes for the user to cook.
Return the recipes in step-by-step detail and a recipe name.
You MUST use json formatting in your response.
Follow this schema:
{
    "recipes": [
        {
            "recipe_name": "string",
            "steps": [
                "string",
                "string",
                ...
            ]
        },
        {
        ...
        }
    ]
}
You MUST follow this exact schema.
The top level object must be a dictionary with a key "recipes" that maps to a list of recipes.
Make sure that the steps are enumerated. 
"""

valid_spices_prompt = """You are a helpful cooking assistant. 
The user will send you a list of spices.
Your job is to identify the real spices in the list and return it in a comma separated list.
"""

class Chef:
    def __init__(self):
        self.client = OpenAI(api_key=openai_key)


    def get_suggestions(self, ingredients, cuisine, difficulty, meal, spice_list, number=3):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": recipes_prompt},
                {"role": "user", "content":  f"Give me {number} {difficulty} {cuisine} recipes in step-by-step detail for the following ingredients for {meal}: {ingredients}\nSpices: {spice_list}"},
            ]
        )
        return response.choices[0].message.content

    
    def get_valid_spices(self, img_path, output_path, interm_path):
        spices.find_label_bounds(img_path, output_path, interm_path, confidence=50, overlap=30)
        # note: prevalidated_spice_list does not include commas bc the results end up being more accurate
        prevalidated_spice_list = spices.find_spice_text(interm_path)
        
        # validate the spices
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": valid_spices_prompt},
                {"role": "user", "content":  f"Extract real seasonings from this list: {prevalidated_spice_list}"},
            ]
        )
        return (response.choices[0].message.content).split(", ")
        

    def get_dish_image(self, dish_name, img_file):
        prompt = f"A highly detailed and realistic picture of a dish called '{dish_name}' on a table. Looks delicious and freshly cooked"
        img_response = self.client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            n=1,
            size=f"512x512"
        )
        image_url = img_response.data[0].url
        img_data = requests.get(image_url).content
        with open(img_file, 'wb') as handler:
            handler.write(img_data)

        rgb_pil_image = Image.open(img_file)
        rgb_pil_image.save(img_file)

    



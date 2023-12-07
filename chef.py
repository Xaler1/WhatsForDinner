from openai import OpenAI
from keys import openai_key
import requests
from PIL import Image

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
Do not include step numbers in the steps.
"""

class Chef:
    def __init__(self):
        self.client = OpenAI(api_key=openai_key)


    def get_suggestions(self, ingredients, cuisine, difficulty, meal, number=3):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": recipes_prompt},
                {"role": "user", "content":  f"Give me {number} {difficulty} {cuisine} recipes in step-by-step detail for the following ingredients for {meal}: {ingredients}"},
            ]
        )
        return response.choices[0].message.content

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



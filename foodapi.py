print("This is API part of the code")
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
import json
import requests
# Define the API endpoint
url = "https://api.openai.com/v1/engines/davinci-codex/completions"

# Define the headers for the API request
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer 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"
}

# Ask the user for the level of difficulty of the recipe (easy, medium, hard) and assign it a variable
difficulty = input("What level of difficulty would you like your recipe to be? (easy, intermediate, master) ")

# Ask the user for the type of cuisine of the recipe (Thai, Italian, Mexican) and assign it a variable
cuisine = input("What type of cuisine would you like your recipe to be? (Thai, Italian, Mexican, American, Indian, Chinese, ...) ")

# Define the data for the API request with the user's input
data = {
    "prompt": "Given me 10 '{difficulty}' level '{cuisine}' recipes in step-by-step detail for the following list of ingredients: '{{}}'",
    "max_tokens": 60
}

# Make the API request
response = requests.post(url, headers=headers, data=json.dumps(data))

# Print the response
print(response.json())


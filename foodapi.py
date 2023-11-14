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

# Define the data for the API request
data = {
    "prompt": "Suggest 5 recipes with the following ingredients: '{}'",
    "max_tokens": 60
}

# Make the API request
response = requests.post(url, headers=headers, data=json.dumps(data))

# Print the response
print(response.json())


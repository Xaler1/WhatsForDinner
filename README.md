# WhatsForDinner

## Installation instructions
### DE-ViT
This has some very specific library requirements, so the exact steps might need to be adapted based on your system.
A virtual environment is a must. CUDA is a hard requirement. Based on your CUDA version pytorch might need to be reinstalled.
Getting xFormers to work is a challenge. Primarily meant for Linux, but can work on Windows with some workarounds.
> 1. Follow the installation instructions on the DE-ViT [repository](https://github.com/mlzxy/devit)
> 2. Follow their checkpoint download [instructions](https://github.com/mlzxy/devit/blob/main/Downloads.md) 
> 3. Move the devit folder into the root of this repository (i.e should be next to the main.py)

### Our project
We would recommend using a separate virtual environment for this part, as in my experiences the different library
dependencies lead to conflicts or weird behaviour.
> 1. Install the requirements.txt file
> 2. Create an [openai](https://platform.openai.com/api-keys) account and get an api key
> 3. Insert the openai api key into the keys.py file
> 4. Create a roboflow account and get an api key
> 5. Insert the roboflow api key into the keys.py file
> 6. Create a google cloud account and setup [google cloud vision](https://cloud.google.com/vision/docs/setup)
> 7. Generate an auth file, save it to the same directory as main.py and then insert the filename into the keys.py file


## Running the code
> 1. Run the vision.py file and leave it running in the background
> 2. Start the front-end using ``streamlit run main.py``
> 3. The website will be automatically opened in your browser



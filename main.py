import os

import streamlit as st

# Setup page
st.set_page_config(layout="wide")
st.title("What's for dinner?")
st.subheader("Don't know what to make for dinner? Let us help you with some suggestions!")

with st.spinner("Loading modules..."):
    from streamlit import session_state as state
    import random
    from chef import Chef
    import os.path as osp
    import json
    from time import sleep



# Assign a random id for the user to keep images separate
if "user_id" not in st.session_state:
    user_id = random.randint(0, 10000)
else:
    user_id = st.session_state["user_id"]


# Load the model
if "chef" not in st.session_state:
    state["chef"] = Chef()
    state["new_fridge_img"] = False
    state["new_spice_img"] = False
    state["img_made"] = False

fridge_input = f"./input/{user_id}.jpg"
fridge_output = f"./output/{user_id}.jpg"
ingredients_output = f"./output/{user_id}.txt"
spices_input = f"./output/{user_id}_spice_in.jpg"
spice_output = f"./output/{user_id}_spice_out.jpg"
labels_output = f"./output/{user_id}_labels.jpg"
new_dish_file = f"./output/new_dish_{user_id}.jpg"

if "user_id" not in st.session_state:
    state["user_id"] = user_id
    for file in [fridge_input, fridge_output, ingredients_output, spices_input, spice_output, labels_output, new_dish_file]:
        try:
            os.remove(file)
        except:
            pass

def new_img_uploaded():
    state["new_fridge_img"] = True
    state["img_made"] = False
    if "ingredients" in state:
        del state["ingredients"]
    if "recommendations" in state:
        del state["recommendations"]
    if "img_gen" in state:
        del state["img_gen"]
    try:
        os.remove(fridge_output)
    except:
        pass
    try:
        os.remove(ingredients_output)
    except:
        pass

def second_img_uploaded():
    state["new_spice_img"] = True
    if "spices" in state:
        del state["spices"]


# Uploading a new image
st.write("Upload an image of your fridge and your spice cabinet to get started!")
uploaded_file_1 = st.file_uploader("Choose image of your fridge", type=["jpg", "jpeg", "png"], on_change=new_img_uploaded, key="fridge_img")
uploaded_file_2 = st.file_uploader("Choose image of your spice cabinet", type=["jpg", "jpeg", "png"], on_change=second_img_uploaded, key="spice_img")
if uploaded_file_1 is not None and uploaded_file_2 is not None and state["new_fridge_img"] and state["new_spice_img"]:
    with st.spinner("Rummaging through your fridge...\nThis may take around half a minute"):
        with open(fridge_input, 'wb') as f:
            f.write(uploaded_file_1.getvalue())
        with open(spices_input, 'wb') as f:
            f.write(uploaded_file_2.getvalue())
        while not osp.exists(ingredients_output):
            sleep(1)
        with open(ingredients_output, "r") as f:
            ingredients = f.read().split("&")
            ingredient_counts = {}
            for ingredient in ingredients:
                if ingredient not in ingredient_counts:
                    ingredient_counts[ingredient] = 0
                ingredient_counts[ingredient] += 1
            result = "\n"
            for ingredient, count in ingredient_counts.items():
                result += f"{ingredient} ({count})\n"
            state["ingredients"] = result
        spices = state["chef"].get_valid_spices(spices_input, spice_output, labels_output)
        state["spices"] = spices
        st.balloons()

    state["img_made"] = True
    state["new_fridge_img"] = False
    state["new_spice_img"] = False
    
# If an image has been uploaded and annotated then show the ingredients and allow further steps
if state["img_made"]:
    with open(fridge_output, 'rb') as file:
        st.download_button(
            label="Download Annotated Image of Fridge",
            data=file,
            file_name="annotated_fridge.jpg",
            mime="image/jpeg",
        )
    with open(spice_output, 'rb') as file:
        st.download_button(
            label="Download Annotated Image of Spice Cabinet",
            data=file,
            file_name="annotated_spice.jpg",
            mime="image/jpeg",
        )
    with st.expander("Show Annotated Image", expanded=False):
        st.image(fridge_output, caption="Annotated Image of Fridge", use_column_width=True)
        st.image(spice_output, caption="Annotated Image of Spice Cabinet", use_column_width=True)

    if "ingredients" in state and "spices" in state:
        st.divider()
        st.write("The ingredients we found in your fridge are:")
        st.text(state["ingredients"])
        
        st.write("The spices we found in your fridge are:")
        spices = ", ".join(state["spices"])
        st.write(spices)


        st.divider()
        col1, col2, col3 = st.columns(3)

        with col1:
            cuisine = st.selectbox("What cuisine?", ["American", "Chinese", "Indian", "Italian", "Japanese", "Mexican", "Thai"])

        with col2:
            difficulty = st.selectbox("What difficulty?", ["Easy", "Medium", "Hard"])

        with col3:
            meal = st.selectbox("What type of meal?", ["Breakfast", "Lunch", "Dinner", "Snack"])

        if st.button("Generate new recommendations"):
            if "img_gen" in state:
                del state["img_gen"]
            with st.spinner("Thinking of recipes..."):
                recommendations = state["chef"].get_suggestions(state["ingredients"], cuisine, difficulty, meal, state["spices"])
                recommendations = json.loads(recommendations)["recipes"]
                st.session_state["recommendations"] = recommendations

if "recommendations" in st.session_state:
    st.divider()
    st.write("Here are some suggested recipes:")
    tabs = st.tabs([recipe["recipe_name"] for recipe in st.session_state["recommendations"]])
    for i, recipe in enumerate(st.session_state["recommendations"]):
        with tabs[i]:
            st.write("Steps:")
            for j, step in enumerate(recipe["steps"]):
                st.write(step)

            if st.button("Imagine what this would look like", key=f"img_gen_btn_{i}"):
                with st.spinner("Generating image..."):
                    state["chef"].get_dish_image(recipe["recipe_name"], new_dish_file)
                    state["img_gen"] = True
                    state["img_gen_name"] = recipe["recipe_name"]
    st.divider()

if "img_gen" in st.session_state:
    st.write(f"Here is what a {state['img_gen_name']} could look like:")
    with open(new_dish_file, 'rb') as file:
        st.download_button(
            label="Download Generated Image",
            data=file,
            file_name="output.jpg",
            mime="image/jpeg",
        )
    st.image(new_dish_file, caption="Generated Image", use_column_width=False)
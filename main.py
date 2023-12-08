import streamlit as st

# Setup page
st.set_page_config(layout="wide")
st.title("What's for dinner?")
st.subheader("Don't know what to make for dinner? Let us help you with some suggestions!")

with st.spinner("Loading modules..."):
    from streamlit import session_state as state
    import random
    from vision import VegetableVision
    from chef import Chef
    import os.path as osp
    import json



# Assign a random id for the user to keep images separate
if "user_id" not in st.session_state:
    state["user_id"] = random.randint(0, 100)

# Load the model
if "vision" not in st.session_state:
    with st.spinner("Loading model..."):
        # get full path to the prototypes
        category_space = osp.join(osp.dirname(__file__), "ycb_prototypes.pth")
        state["vision"] = VegetableVision(category_space=category_space, threshold=0.5)
        state["chef"] = Chef()

    state["new_fridge_img"] = False
    state["new_spice_img"] = False
    state["img_made"] = False

img_file = f"./output/input_{state['user_id']}.jpg"
output_file = f"./output/output_{state['user_id']}.jpg"
img_file_2 = f"./output/input_{state['user_id']}_2.jpg"
output_file_2 = f"./output/output_{state['user_id']}_2.jpg"
output_file_3 = f"./output/output_{state['user_id']}_3.jpg"
new_dish_file = f"./output/new_dish_{state['user_id']}.jpg"

def new_img_uploaded():
    state["new_fridge_img"] = True
    state["img_made"] = False
    if "ingredients" in state:
        del state["ingredients"]
    if "recommendations" in state:
        del state["recommendations"]
    if "img_gen" in state:
        del state["img_gen"]

def second_img_uploaded():
    state["new_spice_img"] = True
    if "spices" in state:
        del state["spices"]

# Uploading a new image
st.write("Upload an image of your fridge to get started!")
uploaded_file_1 = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"], on_change=new_img_uploaded, label_visibility="collapsed")
uploaded_file_2 = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"], on_change=second_img_uploaded, label_visibility="collapsed")
if uploaded_file_1 is not None and uploaded_file_2 is not None and state["new_fridge_img"] and state["new_spices_img"]:
    with st.spinner("Rummaging through your fridge...\nThis may take around half a minute"):
        with open(img_file, 'wb') as f:
            f.write(uploaded_file_1.getvalue())
        with open(img_file_2, 'wb') as f:
            f.write(uploaded_file_2.getvalue())
        ingredients = state["vision"].get_ingredients(img_file, output_file)
        state["ingredients"] = list(set(ingredients))
        spices = state["chef"].get_valid_spices(img_file_2, output_file_2, output_file_3)
        state["spices"] = spices
        st.balloons()

    state["img_made"] = True
    state["new_fridge_img"] = False
    state["new_spice_img"] = False
    
# If an image has been uploaded and annotated then show the ingredients and allow further steps
if state["img_made"]:
    with open(output_file, 'rb') as file:
        st.download_button(
            label="Download Annotated Image of Fridge",
            data=file,
            file_name="output.jpg",
            mime="image/jpeg",
        )
    with open(output_file_2, 'rb') as file:
        st.download_button(
            label="Download Annotated Image of Spice Cabinet",
            data=file,
            file_name="output_2.jpg",
            mime="image/jpeg",
        )
    with st.expander("Show Annotated Image", expanded=False):
        st.image(output_file, caption="Annotated Image of Fridge", use_column_width=True)
        st.image(output_file_2, caption="Annotated Image of Spice Cabinet", use_column_width=True)

    if "ingredients" in state and "spices" in state:
        st.divider()
        st.write("The ingredients we found in your fridge are:")

        ingredients = ", ".join(state["ingredients"])
        st.write(ingredients)
        
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
            with st.spinner("Thinking of recipes..."):
                recommendations = state["chef"].get_suggestions(ingredients, cuisine, difficulty, meal, spices)
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
                st.write(f"{j+1}. {step}")

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
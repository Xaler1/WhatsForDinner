from google.oauth2 import service_account
from google.cloud import vision
from roboflow import Roboflow
import io
import cv2

def vconcat_resize(img_list, interpolation = cv2.INTER_CUBIC): 
    # take minimum width 
    w_min = min(img.shape[1] for img in img_list) 
    # 640 x 480 pixels works well in most cases
      
    # resizing images 
    im_list_resize = [cv2.resize(img, (w_min, int(img.shape[0] * w_min / img.shape[1])), 
                                 interpolation = interpolation) 
                      for img in img_list] 
    # return final image 
    return cv2.vconcat(im_list_resize) 

def find_label_bounds(img_path, output_path, interm_path, confidence=50, overlap=30):
    # product label extraction api
    rf = Roboflow(api_key="QeZ7cX1ZRKz0bSXLurGZ")
    project = rf.workspace().project("product-lable-extraction")
    model = project.version(1).model
    
    original_image = cv2.imread(img_path)
    temp_image = original_image.copy()
    
    # infer on a local image
    prediction_data = model.predict(img_path, confidence=confidence, overlap=overlap).json()
    
    cropped_images = []
    for prediction in prediction_data["predictions"]:
        # only use detail class for labels
        if prediction["class"] != "Detail":
            continue
        x = prediction['x']
        y = prediction['y']
        width = prediction['width']
        height = prediction['height']
        # removes labels that are too small
        if width < 40 or height < 15:
            continue

        cropped_images.append(original_image[y - height//2 : y + height//2,  x - width//2 : x + width//2])
        cv2.rectangle(temp_image, (x - width//2, y - height//2), (x + width//2, y + height//2), (0, 255, 0), 2)

    # write annotated image
    cv2.imwrite(output_path, temp_image)
    
    # create a vertically stacked image of the cropped images for google OCR to read
    stacked_image = vconcat_resize(cropped_images)
    
    # write the stacked image for find_spice_text
    cv2.imwrite(interm_path, stacked_image)

def find_spice_text(stacked_img_path):
    # create the client interface to access the Google Cloud Vision API
    credentials = service_account.Credentials.from_service_account_file(
        filename="spice-recognition-23db7ec653e6.json",
        scopes=["https://www.googleapis.com/auth/cloud-platform"])
    client = vision.ImageAnnotatorClient(credentials=credentials)
    # load the input image as a raw binary file
    with io.open(stacked_img_path, "rb") as f:
        byteImage = f.read()
    
    # create an image object from the binary file and then make a request
    # to the Google Cloud Vision API to OCR the input image
    image = vision.Image(content=byteImage)
    response = client.text_detection(image=image)
    
    # check to see if there was an error when making a request to the API
    if response.error.message:
        raise Exception(
            "{}\nFor more info on errors, check:\n"
            "https://cloud.google.com/apis/design/errors".format(
                response.error.message))

    # return the OCR results
    return response.text_annotations[0].description.replace("\n", " ")
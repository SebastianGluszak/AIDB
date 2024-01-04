# Machine learning models for use in database querying
from google.cloud import vision
from PIL import Image
from io import BytesIO

# Model for detecting all cars within images
# Input: path to image file
# Output: list of lists containing the four vertices of the bounding box for which a car was detected
def detect_cars(client, image):
    with open(image, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content = content)

    objects = client.object_localization(image = image).localized_object_annotations
    vertices = []

    for object_ in objects:
        if object_.name == "Car" or object_.name == "Truck":
            box = []
            for vertex in object_.bounding_poly.normalized_vertices:
                box.append((vertex.x, vertex.y))
            vertices.append(box)
    
    return vertices

# Method for cropping specified regions from an image
# Input: image to crop from, list of locations for crop regions
# Output: list of cropped images
def get_cropped_images(image, vertices):
    cropped_images = []
    image = Image.open(image)
    width, height = image.size

    for box in vertices:
        left = box[0][0] * width
        top = box[0][1] * height
        right = box[2][0] * width
        bottom = box[3][1] * height
        cropped_image = image.crop((left, top, right, bottom))
        buffer = BytesIO()
        cropped_image.save(buffer, format = "PNG")
        content = buffer.getvalue()
        cropped_images.append(content)

    return cropped_images

# Method for converting rgb color value to closest generalized color
# Input: tuple of rgb values
# Output: closest general color name
def get_color_name(rgb):
    colors = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "magenta": (255, 0, 255),
        "cyan": (0, 255, 255),
        "black": (0, 0, 0),
        "white": (255, 255, 255)
    }

    min_distance = float("inf")
    closest_color = None

    for color, value in colors.items():
        distance = sum([(i - j) ** 2 for i, j in zip(rgb, value)])
        if distance < min_distance:
            min_distance = distance
            closest_color = color

    return closest_color

# Model for identifying dominant color
# Input: image
# Output: dominant color of image
def detect_dominant_color(client, images):
    dominant_colors = []

    for image in images:
        image = vision.Image(content = image)
        response = client.image_properties(image = image)
        props = response.image_properties_annotation
        dominant_color = ()
        dominant_color_score = 0

        for color in props.dominant_colors.colors:
            if color.score > dominant_color_score:
                dominant_color_score = color.score
                dominant_color = (color.color.red, color.color.green, color.color.blue)
        
        dominant_colors.append(get_color_name(dominant_color))

    return dominant_colors

vision_client = vision.ImageAnnotatorClient()
image_path = 'traffic_light.jpg'
cars = detect_cars(vision_client, image_path)
colors = detect_dominant_color(vision_client, get_cropped_images(image_path, cars))

print(colors)
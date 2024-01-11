from google.cloud import vision
from PIL import Image
from io import BytesIO

VISION_CLIENT = vision.ImageAnnotatorClient()

def detect_cars(row):
    global VISION_CLIENT
    traffic_id = row[0]
    image_id = row[1]
    image_path = f"images/Traffic_{image_id}.jpg"
    
    with open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content = content)

    objects = VISION_CLIENT.object_localization(image = image).localized_object_annotations
    output_rows = []

    for object_ in objects:
        if object_.name == "Car" or object_.name == "Truck":
            min_x = float("inf")
            max_x = -float("inf")
            min_y = float("inf")
            max_y = -float("inf")

            for vertex in object_.bounding_poly.normalized_vertices:
                max_x = max(max_x, float(vertex.x))
                max_y = max(max_y, float(vertex.y))
                min_x = min(min_x, float(vertex.x))
                min_y = min(min_y, float(vertex.y))

            output_row = {"traffic_id": traffic_id, "image_id": image_id, "min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y}
            output_rows.append(output_row)

    return output_rows

def get_cropped_image(image_id, left, right, top, bottom):
    image_path = f"images/Traffic_{image_id}.jpg"
    image = Image.open(image_path)
    width, height = image.size

    left *= width
    right *= width
    top *= height
    bottom *= height

    cropped_image = image.crop((left, top, right, bottom))
    buffer = BytesIO()
    cropped_image.save(buffer, format = "PNG")
    content = buffer.getvalue()

    return content

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

def detect_color(row):
    global VISION_CLIENT
    traffic_id = row[0]
    image_id = row[1]
    car_id = row[2]
    min_x = row[3]
    max_x = row[4]
    min_y = row[5]
    max_y = row[6]

    cropped_image = get_cropped_image(image_id, min_x, max_x, min_y, max_y)

    image = vision.Image(content = cropped_image)
    response = VISION_CLIENT.image_properties(image = image)
    properties = response.image_properties_annotation
    dominant_color = ()
    dominant_color_score = 0

    for color in properties.dominant_colors.colors:
        if color.score > dominant_color_score:
            dominant_color_score = color.score
            dominant_color = (color.color.red, color.color.green, color.color.blue)
    
    dominant_color = get_color_name(dominant_color)
    output = {"traffic_id": traffic_id, "image_id": image_id, "car_id": car_id, "color": dominant_color}

    return [output]
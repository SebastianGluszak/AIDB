from database import AIDB
from models import detect_cars, detect_color
import json
import glob
import re

# Load in config file
config_file = 'config.json'
with open(config_file, 'r') as file:
    config = json.load(file)

# Load in base table data
base_data = [
    {
        "tablename": "traffic_table",
        "data": []
    }
]

traffic_images = glob.glob("images/*")
traffic_images.sort()
number_pattern = re.compile(r'\d+')

for traffic_image in traffic_images:
    image_id = int(number_pattern.findall(traffic_image)[0])
    base_data[0]["data"].append({"image_id": image_id})

# Load in ML model functions
model_api = {"car_detection": detect_cars, "color_detection": detect_color}

# Construct AIDB
aidb = AIDB(config, base_data, model_api)

# Query database
print(aidb.query('SELECT color_table.color, car_table.min_x FROM color_table, car_table').all())
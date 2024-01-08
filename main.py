# Main file for running AIDB sytem 

from database import aidb
from models import detect_cars, detect_dominant_color
import json
import os

# Load in necessary aidb construction parameters
config_file = 'config.json'
with open(config_file, 'r') as file:
    config = json.load(file)

base_data = [
    {
        "tablename": "traffic_table",
        "data": [{"image_path": "images/base/traffic_1.jpg"}, {"image_path": "images/base/traffic_2.jpg"}, {"image_path": "images/base/traffic_3.jpg"}, {"image_path": "images/base/traffic_4.jpg"}]
    }
]

model_api = {"car_detection": detect_cars, "color_analysis": detect_dominant_color}

# Construct AIDB
db = aidb(config, base_data, model_api)

# Execute SQL queries
# result = db.execute("SELECT car_table.vertices FROM car_table")
result = db.execute("SELECT color_table.color FROM color_table")

print(result.all())
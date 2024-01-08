# Main file for running AIDB sytem 

from database import aidb
from models import detect_cars, detect_dominant_color
import json
import glob

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

traffic_images = glob.glob("images/base/*")
traffic_images.sort()
for traffic_image in traffic_images:
    base_data[0]["data"].append({"image_path": traffic_image})

# Load in model api lookup table
model_api = {"car_detection": detect_cars, "color_analysis": detect_dominant_color}

# Construct AIDB
db = aidb(config, base_data, model_api)

# Execute SQL queries
result_one = db.execute("SELECT color_table.id, color_table.traffic_id, color_table.car_id, color_table.color FROM color_table WHERE color_table.color == 'yellow'")
result_two = db.execute("SELECT color_table.id, color_table.traffic_id, color_table.car_id, color_table.color FROM color_table WHERE color_table.color == 'red'")

print(result_one.all())
print(result_two.all())
print(f"Number of cache hits: {db.cache_hits}")
from database import AIDB
from models import detect_cars, detect_color
import json
import glob
import re
import timeit

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

traffic_images = glob.glob("images/*")[:100]
traffic_images.sort()
number_pattern = re.compile(r'\d+')

for traffic_image in traffic_images:
    image_id = int(number_pattern.findall(traffic_image)[0])
    base_data[0]["data"].append({"image_id": image_id})

# Load in ML model functions
model_api = {"car_detection": detect_cars, "color_detection": detect_color}

# Construct AIDB
aidb = AIDB(config, base_data, model_api)

# Example approximate average query
approximate_query_time = timeit.timeit(stmt = lambda: print(aidb.approximate_average('car_table.min_x', 20)), number  = 1)

# Example exact query
exact_query_time = timeit.timeit(stmt = lambda: print(aidb.query('SELECT color_table.image_id FROM color_table WHERE color_table.color == "cyan"').all()), number = 1)

# Example exact query with cached results from previous queries
cached_query_time = timeit.timeit(stmt = lambda: print(aidb.query('SELECT color_table.image_id FROM color_table WHERE color_table.color == "red"').all()), number = 1)

# Query time results
print(f"Approximate query time: {approximate_query_time}")
print(f"Exact query time: {exact_query_time}")
print(f"Cached query time: {cached_query_time}")
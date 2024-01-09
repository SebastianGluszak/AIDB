# Main file for running AIDB sytem 

from database import aidb
from models import detect_cars, detect_dominant_color
import json
import glob
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

traffic_images = glob.glob("images/*")[:5]
traffic_images.sort()
for traffic_image in traffic_images:
    base_data[0]["data"].append({"image_path": traffic_image})

# Load in model api lookup table
model_api = {"car_detection": detect_cars, "color_analysis": detect_dominant_color}

# Construct AIDB
db = aidb(config, base_data, model_api)

# Execute exact SQL queries
query_one = "SELECT color_table.id, color_table.traffic_id, color_table.car_id, color_table.color FROM color_table WHERE color_table.color == 'yellow'"
query_two = "SELECT color_table.id, color_table.traffic_id, color_table.car_id, color_table.color FROM color_table WHERE color_table.color == 'red'"    

print(query_one)
time_query_one = timeit.timeit(stmt = lambda: print(db.execute_exact(query_one).all()), number = 1)
print(query_two)
time_query_two = timeit.timeit(stmt = lambda: print(db.execute_exact(query_two).all()), number = 1)

print(f"Time query one: {time_query_one}")
print(f"Time query two: {time_query_two}")

# Execute Approximate SQL queries
query_three = "SELECT COUNT(color_table.color) FROM color_table WHERE color_table.color == 'black'"

print(query_three)
time_query_exact = timeit.timeit(stmt = lambda: print(db.execute_exact(query_three).all()), number = 1)
# time_query_approx = timeit.timeit(stmt = lambda: print(db.execute_approximate(query_three).all()), number = 1)
print(f"Time query exact: {time_query_exact}")
# print(f"Time query approx: {time_query_approx}")

# Execute nested SQL query
query_four = "SELECT car_table.id FROM car_table WHERE car_table.id IN (SELECT color_table.car_id FROM color_table WHERE color_table.color == 'black')"
print(query_four)
time_query_nested = timeit.timeit(stmt = lambda: print(db.execute_exact(query_four).all()), number = 1)
print(f"Time query nested: {time_query_nested}")

# Execute approximate nested SQL query
query_five = "SELECT traffic_table.id FROM traffic_table WHERE traffic_table.id IN (SELECT color_table.traffic_id FROM color_table WHERE color_table.color == 'black')"
print(query_five)
time_query_approx_nested = timeit.timeit(stmt = lambda: print(db.execute_exact(query_five).all()), number = 1)
print(f"Time query approx nested: {time_query_approx_nested}")

# Show number of cache hits
print(f"Number of cache hits: {db.cache_hits}")
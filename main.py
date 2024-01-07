# Main file for running AIDB sytem 

from database import aidb
from models import detect_cars, detect_dominant_color
import json

# Load in configuration settings
config_file = 'config.json'
with open(config_file, 'r') as file:
    config = json.load(file)

# Construct AIDB
db = aidb(config)

# Connect ML models
db.connect_model("car_detection", detect_cars)
db.connect_model("color_analysis", detect_dominant_color)

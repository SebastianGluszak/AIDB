# Main file for running AIDB sytem 

from database import aidb
import json

config_file = 'config.json'
with open(config_file, 'r') as file:
    config = json.load(file)

db = aidb(config)
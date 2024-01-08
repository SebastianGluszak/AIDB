# Database sytem class handling storage of all necessary data
# Includes querying functionality

from sqlalchemy import create_engine, ForeignKey, MetaData, Table, Column, Integer, String, text
import re

class aidb():
    engine = create_engine("sqlite+pysqlite:///:memory", echo = True)
    metadata = MetaData()
    base_tables = {}
    output_tables = {}
    model_mappings = {}
    model_api = {}

    def __init__(self, config):
        # Create the tables here
        self.build_tables(config)
        # Add models and model mappings
        self.setup_models(config)
        # Create the caching tables
        self.build_cache(config)
        # Load all tables into memory
        self.metadata.create_all(self.engine)

    def build_table(self, schema):
        data_type_mapper = {"Integer": Integer, "String": String}
        tablename = schema["tablename"]
        columns = schema["columns"]

        primary_column = columns["primary"]
        foreign_columns = columns["foreign"]
        regular_columns = columns["regular"]

        table = Table(
            tablename,
            self.metadata,
            Column(primary_column["name"], data_type_mapper[primary_column["data_type"]], primary_key = True),
            *(Column(foreign_column["name"], ForeignKey(foreign_column["foreign_key"])) for foreign_column in foreign_columns),
            *(Column(regular_column["name"], data_type_mapper[regular_column["data_type"]]) for regular_column in regular_columns)
        )

        return table

    # Function used to create sqlalchemy tables using config file
    # Input: JSON data containing base and output table schemas
    # Output: No output, builds and deploys base and output tables for database
    def build_tables(self, config):
        table_schemas = config["table_schemas"]
        
        for schema in table_schemas["base"]:
            base_table = self.build_table(schema)
            self.base_tables[base_table.name] = base_table

        for schema in table_schemas["output"]:
            output_table = self.build_table(schema)
            self.output_tables[output_table.name] = output_table

    # Function to create cache tables for caching mechanisms
    # Input: JSON data containing ML models and input columns for respective models
    # Output: No output, builds and deploys caching tables for database
    def build_cache(self, config):
        pass

    # Function to add ML models and add model mappings
    # Input: JSON data containing models and model mappings
    # Output: No output, configures internal model mappings
    def setup_models(self, config):
            self.model_mappings = config["model_mappings"]["mappings"]
            for tablename in self.base_tables:
                self.model_mappings[tablename + '.id'] = []
            for model in config["model_mappings"]["models"]:
                self.model_api[model] = None

    # Function to map model names to the corresponding ML model api
    # Input: Model name and corresponding model api function
    # Output: No output, maps the model name to api
    def connect_model(self, model_name, model_function):
        self.model_api[model_name] = model_function

    # Function to execute sql query to database
    # Input: SQL query text
    # Output: Query output
    def execute(self, query):
        selected_columns = self.get_selected_columns(query)
        dependencies = self.get_dependencies(selected_columns)
        for dependency in dependencies:
            # Check if cached data
            # Else run ML model and upload data to corresponding table
            pass
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            for row in result:
                print(row)
    
    # Function to extract selected columns in an sql query
    # Input: SQL query text
    # Output: List of selected columns
    def get_selected_columns(self, query):
        pattern = r"SELECT\s+(.*?)\s+FROM"
        match = re.search(pattern, query, re.IGNORECASE)
        
        if match:
            columns = match.group(1).split(',')
            columns = [col.strip() for col in columns]
            return columns
        else:
            return []
    
    # Function to traverse all columns that selected columns are dependent on
    # Input: List of selected columns
    # Output: List of selected columns and all columns that selected columns are dependent on
    def get_dependencies(self, columns):
        queue = [column for column in columns]
        traversal = []

        while len(queue) != 0:
            curr = queue.pop()
            for dependency in self.model_mappings[curr]:
                queue.append(dependency["input"])
                traversal.append((dependency["input"], curr, dependency["model"]))
        
        traversal.reverse()
        return traversal
        
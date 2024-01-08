# Database sytem class handling storage of all necessary data
# Includes querying functionality

from sqlalchemy import create_engine, ForeignKey, MetaData, Table, Column, Integer, String, text, select, insert
import re

class aidb():
    engine = create_engine("sqlite+pysqlite:///:memory", echo = True)
    metadata = MetaData()
    base_tables = {}
    output_tables = {}
    model_mappings = {}
    model_api = {}

    def __init__(self, config, base_data, model_api):
        # Create the tables here
        self.build_tables(config)
        # Add models and model mappings
        self.setup_models(config, model_api)
        # Create the caching tables
        self.build_cache(config)
        # Load all tables into memory
        self.metadata.create_all(self.engine)
        # Insert base table data
        self.upload_base_data(base_data)

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
    def setup_models(self, config, model_api):
            self.model_mappings = config["model_mappings"]["mappings"]
            for tablename in self.base_tables:
                self.model_mappings[tablename + '.id'] = []
            self.model_api = model_api

    # Function to upload base data to base tables
    # Input: Base tablename and List of object rows of base table data
    # Output: No output, uploads data to the specified base table
    def upload_base_data(self, data):
        for table in data:
            tablename = table["tablename"]
            table_data = table["data"]
            stmt = insert(self.base_tables[tablename]).values(table_data)
            with self.engine.connect() as conn:
                conn.execute(stmt)
                conn.commit()

    # Function to execute sql query to database
    # Input: SQL query text
    # Output: Query output
    def execute(self, query):
        selected_columns = self.get_selected_columns(query)
        dependencies = self.get_dependencies(selected_columns)
        
        for dependency in dependencies:
            input_col, output_col, model_name = dependency
            input_table = input_col.split('.')[0]
            output_table = output_col.split('.')[0]

            if input_table in self.base_tables:
                stmt = select(self.base_tables[input_table])
            else:
                stmt = select(self.output_tables[input_table])

            with self.engine.connect() as conn:
                output_rows = []
                result = conn.execute(stmt)
                for row in result:
                    output = self.model_api[model_name](row)
                    output_rows += output

            stmt = insert(self.output_tables[output_table]).values(output_rows)
            with self.engine.connect() as conn:
                conn.execute(stmt)
                conn.commit()

        with self.engine.connect() as conn:
            result = conn.execute(text(query))
        
        return result
    
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
            if curr in self.model_mappings:
                for dependency in self.model_mappings[curr]:
                    queue.append(dependency["input"])
                    traversal.append((dependency["input"], curr, dependency["model"]))
        
        traversal.reverse()
        return traversal
        
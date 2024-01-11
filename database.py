from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Boolean, Float, select, insert, ForeignKey, text
from graph import ModelNode
import re

class AIDB():
    engine = create_engine("sqlite+pysqlite:///:memory", echo = True)
    metadata = MetaData()
    base_tablenames = set()
    tables = {} 
    models = {}
    column_dependencies = {}
    model_tree = None
    cache = {}

    def __init__(self, config, base_data, model_api):
        self._build_tables(config)
        self._upload_data(base_data)
        self._setup_models(config, model_api)

    def _build_table_helper(self, schema):
        data_type_mapper = {"Integer": Integer, "String": String, "Boolean": Boolean, "Float": Float}
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

    def _build_tables(self, config):
        table_schemas = config["table_schemas"]

        for schema in table_schemas:
            table = self._build_table_helper(schema)
            self.tables[table.name] = table
            if schema["is_base"] == True:
                self.base_tablenames.add(table.name) 

        self.metadata.create_all(self.engine)
    
    def _upload_data(self, data):
        for table in data:
            tablename = table["tablename"]
            table_data = table["data"]
            insert_statement = insert(self.tables[tablename]).values(table_data)

            with self.engine.connect() as conn:
                conn.execute(insert_statement)
                conn.commit()

    def _setup_models(self, config, model_api):
        models = config["models"]

        for model in models:
            for model_output in model["outputs"]:
                self.column_dependencies[model_output] = model["inputs"]
            self.models[model["name"]] = {"api": model_api[model["name"]], "inputs": model["inputs"], "outputs": model["outputs"]}
            self.cache[model["name"]] = set()

        base_columns = set()
        for base_tablename in self.base_tablenames:
            base_table = self.tables[base_tablename]
            for column in base_table.c:
                base_columns.add(str(column))
        
        self.model_tree = ModelNode(base_columns)

        queue = [self.model_tree]
        while len(queue) != 0:
            curr = queue.pop(0)
            for modelname, model in self.models.items():
                if set(model["inputs"]).issubset(curr.columns):
                    explored_columns = {column for column in curr.columns}
                    for column in model["outputs"]:
                        explored_columns.add(column)
                    if len(explored_columns) > len(curr.columns):
                        neighbor = ModelNode(explored_columns)
                        queue.append(neighbor)
                        curr.add_neighbor(neighbor, modelname)

    def _get_column_dependencies(self, columns):
        queue = [column for column in columns]
        traversal = {column for column in columns}
        
        while len(queue) != 0:
            curr = queue.pop()
            if curr in self.column_dependencies:
                for dependency in self.column_dependencies[curr]:
                    if dependency not in traversal:
                        queue.append(dependency)
                        traversal.add(dependency)

        return traversal
    
    def _get_model_dependencies(self, columns):
        queue = [(self.model_tree, [])]

        while len(queue) != 0:
            curr_node, curr_models = queue.pop(0)
            if columns.issubset(curr_node.columns):
                return curr_models
            for edge in curr_node.neighbors:
                queue.append((edge.target, curr_models + [edge.model]))
        
        return []

    def query(self, sql_text):
        pattern = r'\b\w+\.\w+\b'  
        selected_columns = re.findall(pattern, sql_text)
        column_dependencies = self._get_column_dependencies(selected_columns)
        model_dependencies = self._get_model_dependencies(column_dependencies)

        for model in model_dependencies:
            inputs, outputs, name = self.models[model]["inputs"], self.models[model]["outputs"], model
            input_columns = [self.tables[column.split('.')[0]].c[column.split('.')[1]] for column in inputs]
            select_statement = select(*(column for column in input_columns))

            with self.engine.connect() as conn:
                output_rows = []
                result = conn.execute(select_statement)
                for row in result:
                    if tuple(row) not in self.cache[name]:
                        output = self.models[name]["api"](row)
                        output_rows += output
                        self.cache[name].add(tuple(row))
            
            for column in outputs:
                output_table = column.split('.')[0]
                break

            if len(output_rows) != 0:
                insert_statement = insert(self.tables[output_table]).values(output_rows)
                
                with self.engine.connect() as conn:
                    conn.execute(insert_statement)
                    conn.commit()
        
        with self.engine.connect() as conn:
            result = conn.execute(text(sql_text))
        
        return result

    def approximate_query(self, sql_text):
        pass
class ModelNode():
    def __init__(self, columns):
        self.columns = columns
        self.neighbors = []
    
    def add_neighbor(self, neighbor, model):
        self.neighbors.append(ModelEdge(neighbor, model))

class ModelEdge():
    def __init__(self, target, model):
        self.target = target
        self.model = model
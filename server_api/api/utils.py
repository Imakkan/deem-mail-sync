class EmailCommand:

    def __init__(self, function, context, model):
        self.function = function
        self.context = context
        self.model = model

    def has_arguments(self):
        return self.model is not None

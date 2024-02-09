class InformativeException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)
        self.message = msg

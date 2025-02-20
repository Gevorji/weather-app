class OpenweathermapApiHTTPResponseError(Exception):
    def __init__(self, code, phrase):
        self.phrase = phrase
        self.code = code



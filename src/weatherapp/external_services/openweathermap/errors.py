class OpenweathermapApiError(Exception):
    pass

class OpenweathermapApiHTTPResponseError(OpenweathermapApiError):
    def __init__(self, code, phrase):
        self.phrase = phrase
        self.code = code

class OpenWeathermapApiConnectionTimeoutError(OpenweathermapApiError):
    pass

from rest_framework.exceptions import APIException

class SimpleError(APIException):
    status_code = 400

    def __init__(self, detail):
        super().__init__(detail={"error": detail})

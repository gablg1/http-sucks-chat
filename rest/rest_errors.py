import json

def error(status_code, description):
    return json.dumps({'errors': {'status_code': status_code, 'description': description}}), status_code

def bad_request():
    return error(400, 'Bad Request: The request cannot be fulfilled due to bad syntax')

def unauthorized():
    return error(401, 'Unauthorized: Authentication credentials missing or incorrect')

def forbidden():
    return error(403, 'Forbidden: You do not have permission to perform this request')

def not_found():
    return error(404, 'Not Found: The resource you requested could not be found')

def internal_server_error():
    return error(500, 'Internal Server Error')
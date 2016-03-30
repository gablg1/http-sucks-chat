"""
Defines some of the commonly used errors returned by the REST
protocol.
"""

import json

def error(status_code, description):
    """ 
    Returns a general error message, given a status code and a description.

    :param status_code: The HTTP status code, e.g., 404
    :param description: The description corresponding to that error, e.g., Not Found

    :return: A JSON containing the status_code and description (following the rules
             defined by JSON API [http://jsonapi.org/]) and the status_code
    """
    return json.dumps({'errors': {'status_code': status_code, 'description': description}}), status_code

def bad_request():
    """
    Returns the Bad Request error message. Typically, this happens because the
    parameters passed in to a HTTP request cannot be parsed (either because
    the format is incorrect, or because the required parameters are lacking).
    """
    return error(400, 'Bad Request: The request cannot be fulfilled due to bad syntax')

def unauthorized():
    """
    Returns the Unauthorized error message. Typically, this happens because 
    authentication failed.
    """
    return error(401, 'Unauthorized: Authentication credentials missing or incorrect')

def forbidden():
    """
    Returns the Forbidden error message. This should be returned if a user
    tries to do something they do not have permissions to; e.g., deleting a
    user account that is not their own.
    """
    return error(403, 'Forbidden: You do not have permission to perform this request')

def not_found():
    """
    Returns the Not Found error message. Typically, this is issued when any
    resource was not found by the server. This could be, for instance, if the
    user attempts to send a message to a user that does not exist.
    """
    return error(404, 'Not Found: The resource you requested could not be found')

def internal_server_error():
    return error(500, 'Internal Server Error')
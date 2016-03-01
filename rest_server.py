from flask import Flask, request
from chat_server import ChatServer
from chat_db import UserKeyError
from chat_db import GroupExists
from chat_db import GroupDoesNotExist
from chat_db import UsernameDoesNotExist
from chat_db import UsernameExists
from chat_db import UserNotLoggedInError
import bson
from bson import json_util
import json

from functools import wraps

def check_authorization(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        session_token = request.authorization.password

        try:
            args[0].username_for_session_token(session_token)
        # !# For some reason, this won't catch UserNotLoggedInError. Anybody?
        except UserNotLoggedInError:
            return json.dumps({'errors': {'status_code': 403, 'title': 'Forbidden: You do not have access to perform this request'}}), 403
        return f(*args, **kwargs)
    return wrapper

class RESTServer(ChatServer):
    ################
    ## INIT: ROUTING
    ################

    def __init__(self, host, port):
        ChatServer.__init__(self, host, port)
        self.app = Flask("HTTPServer")

        # Login/Logout routes
        self.app.add_url_rule("/login", view_func=self.handle_login, methods=['POST'])
        self.app.add_url_rule("/logout", view_func=self.handle_logout, methods=['POST'])

        # User routes
        self.app.add_url_rule("/users", view_func=self.handle_create_user, methods=['POST'])
        self.app.add_url_rule("/users", view_func=self.handle_get_users, methods=['GET'])
        self.app.add_url_rule("/users/<user_id>", view_func=self.handle_delete_user, methods=['DELETE'])

        # Group routes
        self.app.add_url_rule("/groups", view_func=self.handle_get_groups, methods=['GET'])
        self.app.add_url_rule("/groups", view_func=self.handle_create_group, methods=['POST'])
        self.app.add_url_rule("/groups/<group_id>/users", view_func=self.handle_add_user_to_group, methods=['POST'])
        # self.app.add_url_rule("/groups/<group_id>", view_func=self.handle_delete_group, methods=['DELETE'])

        # Messaging routes
        self.app.add_url_rule("/users/<user_id>/messages", view_func=self.handle_send_user, methods=['POST'])
        self.app.add_url_rule("/users/<user_id>/messages", view_func=self.handle_fetch, methods=['GET'])
        self.app.add_url_rule("/groups/<group_id>", view_func=self.handle_send_group, methods=['POST'])

    ###########
    ## USERS ##
    ###########  
      
    def handle_login(self):
        username = request.authorization.username
        password = request.authorization.password

        success, token = self.login(username, password)
        if success:
            return json.dumps({'data': {'user': {'session_token': token, 'username': username}}})
        else:
            return json.dumps({'errors': {'status': 403, 'title': 'Forbidden: Could not authenticate password.'}})

    @check_authorization
    def handle_logout(self):
        session_token = request.authorization.password

        try:
            username = self.username_for_session_token(session_token)
            self.logout(username)

            return json.dumps({'data': {'user': {'session_token': session_token}}}), 200

        except UserKeyError:
            return json.dumps({'errors': {'status_code': 500, 'title': 'Internal Server Error'}}), 500

    def handle_create_user(self):
        try:
            username = request.json['username']
            password = request.json['password']
        except ValueError:
            return json.dumps({'errors': {'status_code': 400, 'title': 'Bad Request: Could not process JSON'}}), 400

        try:
            self.create_account(username, password)
        except UsernameExists:
            return json.dumps({'errors': {'status_code': 409, 'title': 'Conflict: Username taken'}}), 409

        return json.dumps({'data': {'user': {'username': username}}}), 201

    @check_authorization
    def handle_delete_user(self, user_id):
        session_token = request.authorization.password

        try:
            session_username = self.username_for_session_token(session_token)
            if (session_username != user_id):
                return json.dumps({'errors': {'status_code': 403, 'title': 'Forbidden: You do not have permission to perform this request'}}), 403
            
            self.logout(user_id)
            self.delete_account(user_id)

            return json.dumps({'data': {'user': {'username': user_id}}}), 200

        except UserKeyError:
            return json.dumps({'errors': {'status_code': 403, 'title': 'Forbidden: You do not have permission to perform this request'}}), 403

    @check_authorization
    def handle_get_users(self):
        wildcard = request.args.get('wildcard')

        if wildcard is None:
            wildcard = '*'

        try:
            users = self.get_users(wildcard)
        except:
            return json.dumps({'errors': {'status_code': 500, 'title': 'Internal Server Error'}})

        return json.dumps({'data': {'users': users}}, default=json_util.default)

    ############
    ## GROUPS ##
    ############

    @check_authorization
    def handle_create_group(self):
        try:
            group_name = request.json['data']['group_name']
        except ValueError:
            return json.dumps({'errors': {'status_code': 400, 'title':'Bad Request: Cannot process JSON'}}), 400
        
        try:
            self.create_group(group_name)
        except GroupExists:
            return json.dumps({'errors': {'status_code': 200, 'title': 'Group ID Taken: The ID chosen already exists.'}}), 200

        return json.dumps({'data': {'group_id': group_name}}), 200

    @check_authorization
    def handle_add_user_to_group(self, group_id):
        try:
            username = request.json['data']['username']
        except ValueError:
            return json.dumps({'errors': {'status_code': 400, 'title': 'Bad Request: Cannot process JSON'}}), 400

        try:
            self.add_user_to_group(username, group_id)
        except GroupDoesNotExist:
            return json.dumps({'errors': {'status_code': 404, 'title': 'Not Found: The requested group does not exist'}}), 404
        except UsernameDoesNotExist:
            return json.dumps({'errors': {'status_code': 404, 'title': 'Not Found: The requested username does not exist'}}), 404

        return json.dumps({'data': {'group_id': group_id, 'username': username}}), 201

    @check_authorization
    def handle_get_groups(self):
        wildcard = request.args.get('wildcard')

        if wildcard is None:
            wildcard = '*'

        try:
            groups = [group['name'] for group in self.get_groups(wildcard)]
        except:
            return json.dumps({'errors': {'status_code': 500, 'title': 'Internal Server Error'}}), 500

        return json.dumps({'data': {'groups': groups}})

    ###############
    ## MESSSAGES ##
    ###############

    @check_authorization
    def handle_send_user(self, user_id):
        session_token = request.authorization.password

        try:
            message = request.json['data']['message']
        except ValueError:
            return json.dumps({'errors': {'status_code': 400, 'title':'Bad Request: Cannot process JSON'}}), 400

        try:
            self.send_or_queue_message(session_token, message, user_id)
        except UserKeyError:
            return json.dumps({'errors': {'status_code': 404, 'title': 'Not Found: Username not found'}})

        return json.dumps({'data': {'user_id': user_id, 'message': message}}), 201
    
    @check_authorization
    def handle_send_group(self, group_id):
        session_token = request.authorization.password

        try:
            message = request.json['data']['message']
        except ValueError:
            return json.dumps({'errors': {'status_code': 400, 'title':'Bad Request: Cannot process JSON'}}), 400

        try:
            self.send_message_to_group(session_token, message, group_id)
            return json.dumps({'data': {'group_id': group_id, 'message': message}}), 201
        except GroupDoesNotExist:
            return json.dumps({'errors': {'status_code': 404, 'title': 'Not Found: Group not found'}})

    @check_authorization
    def handle_fetch(self, user_id):
        try:
            messages = self.get_user_queued_messages(user_id)
            self.clear_user_message_queue(user_id)
        except UserKeyError:
            return json.dumps({'errors': {'status_code': 404, 'title': 'Not found: The requested user does not exist'}}), 404
        except:
            return json.dumps({'errors': {'status_code': 500, 'title': 'Internal Server Error'}}), 500

        return json.dumps({'data': {'messages': messages}})

    ##########
    ## MISC ##
    ##########
    @check_authorization
    def is_online(self, user_id):
        return False

    def serve_forever(self):
        self.app.run(port = self.port)
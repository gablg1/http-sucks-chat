from flask import Flask, request
from chat_server import ChatServer
import json

class RESTServer(ChatServer):
    def __init__(self, host, port):
        ChatServer.__init__(self, host, port)
        self.app = Flask("HTTPServer")
        self.app.add_url_rule("/login", view_func=self.handle_login, methods=['POST'])
        self.app.add_url_rule("/logout", view_func=self.handle_logout, methods=['POST'])
        self.app.add_url_rule("/users", view_func=self.handle_users_online, methods=['GET'])
        self.app.add_url_rule("/users", view_func=self.handle_register, methods=['POST'])
        self.app.add_url_rule("/users/<user_id>", view_func=self.handle_send_user, methods=['POST'])
        self.app.add_url_rule("/users/<user_id>", view_func=self.handle_fetch, methods=['GET'])
        self.app.add_url_rule("/groups/<group_id>", view_func=self.handle_send_group, methods=['POST'])
        self.app.add_url_rule("/groups", view_func=self.handle_create_group, methods=['POST'])
        self.app.add_url_rule("/groups/<group_id>/users", view_func=self.handle_add_user_to_group, methods=['POST'])

    def handle_login(self):
        success, token = self.login(request.authorization.username, request.authorization.password)
        if success:
            return json.dumps({'session_token': token})
        else:
            return json.dumps({'errors': {'status': 403, 'title': 'Forbidden: Could not authenticate password.'}})

    def handle_logout(self):
        session_token = request.authorization.password

        if session_token in self.logged_in_users:
            try:
                user = self.logged_in_users[session_token]
                del self.logged_in_users[user['session_token']]
                user['logged_in'] = False
                user['session_token'] = None
                user['sock'] = None
                return json.dumps({'data': {'session_token': session_token}}), 200
            except UserKeyError:
                return json.dumps({'errors': {'status_code': 500, 'title': 'Internal Server Error'}}), 500
        else:
            return json.dumps({'errors': {'status_code': 404, 'title': 'Not Found: Could not found associated session token.'}}), 404

    def handle_register(self):
        r = request.json
        self.create_account(r['username'], r['password'])

        return json.dumps({'data': {'username': r['username']}}), 201
        # this needs error handling!!!

    def handle_send_user(self, user_id):
        message = request.json['data']['message']
        self.send_message_to_user(message, user_id)

        return json.dumps({'data': {'user_id': user_id, 'message': message}}), 201

    def handle_send_group(self, group_id):
        message = request.json['data']['message']
        self.send_message_to_group(message, group_id)

        return json.dumps({'data': {'group_id': group_id, 'message': message}}), 201

    def handle_create_group(self):
        group_id = request.json['data']['group_id']
        print group_id
        self.create_group(group_id)

        return json.dumps({'data': {'group_id': group_id}})

    def handle_add_user_to_group(self, group_id):
        username = request.json['data']['username']
        print username
        self.add_user_to_group(username, group_id)

        return json.dumps({'data': {'group_id': group_id, 'username': username}}), 201
        # return json.dumps({'dummy':'yeah'})

    def handle_users_online(self):
        return json.dumps({'data': {'users': self.users_online()}})

    def handle_fetch(self, user_id):
        print user_id
        print self.get_user_queued_messages(user_id)
        return json.dumps({'data': {'messages': self.get_user_queued_messages(user_id)}})

    def is_online(self, user_id):
        return False

    def serve_forever(self):
        self.app.run(port=self.port)





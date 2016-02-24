import cmd

class ChatClient(cmd.Cmd):
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.prompt = '> '
        self.intro = 'Welcome to the HTTP Sucks Chat!'

        cmd.Cmd.__init__(self)

    def do_login(self, username):
        self.login(username)

    def do_send(self, body):
        group_id, message = body.split(' ', 1)
        self.sendToGroup(group_id, message)

    def do_fetch(self, useless):
        print self.fetch()

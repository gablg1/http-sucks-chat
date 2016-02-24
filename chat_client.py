import cmd

class ChatClient(cmd.Cmd):
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.prompt = '> '
        self.intro = 'Welcome to the HTTP Sucks Chat!'

        cmd.Cmd.__init__(self)

    def do_login(self, username):
        print username

    def do_send(self, message):
        self.send(message)

    def do_fetch(self, useless):
        print self.fetch()

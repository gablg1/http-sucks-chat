# rdtp-chat
Chat system developed for CS 262 to demonstrate that HTTP/REST sucks. We handcrafted RDTP, a wire protocol to substitute HTTP. And it is better.

## Dependencies and Installation

This application runs on Python 2.7, and it has the following dependencies:

* MongoDB (`brew install mongo` and `pip install pymongo`)
* Python's Requests API (`pip install requests`)
* Flask (`pip install flask`)

It has been tested on Ubuntu 14.04 (running on VMWare) and on Mac OS X El Capitan.
Support is likely on other systems, but installation may be slightly more
cumbersome.

## User Interface and Usage

Since this is a systems course, of course we are going to do a command line
application. To run the server:

`python server.py <REST|RDTP>`

And to run the client:

`python client.py <REST|RDTP>`

Reasonably, only use the REST client if also using the REST server, and vice-versa.

### List of Commands

The following commands can be understood by our application:

* `register <username> <password>`
* `login <username> <password>`
* `logout`
* `create_group <group_name>`
* `join_group <group_name>`
* `add_user_to_group <username> <group_name>`
* `send <username> <message>`
* `send_group <group_name> <message>`
* `fetch`
* `delete_account`

The behavior is clear from the command's names. Alternatively, there is a
`help` utility in the command line that will briefly describe the commands.

### Real-Time Conversation

Due to the restrictive nature of the REST architecture, real-time conversations
would require constant polling. We have therefore decided to not allow this
type of interaction in the REST version. To receive messages, users must enter
the `fetch` command while logged in.

In the RDTP version, we allow for real-time conversations by using a thread 
that keeps listening on messages from other users.

## Design Structure

The code for `client.py` and `server.py` is obviously shared between the two
protocols. However, the interfaces of `ChatServer` and `ChatClient`
provide some abstraction for the server and client, which is shared between
protocols. `ChatServer` uses `ChatDB` for interaction with an underlying instance
of MongoDB.

Each protocol implements a subclass of `ChatServer` and a subclass of `ChatClient`.
Therefore we have classes `RDTPServer`, `RESTServer`, `RDTPClient` and `RESTClient`.
They implement methods that will call the operations defined by `ChatServer` or
`ChatClient`. The calls in `ChatServer` will depend mostly on `ChatDB`, the database
instance which currently is implemented with `MongoDB`. The calls in `ChatClient`
will mostly rely on Python's `cmd.Cmd` library.

In REST, the `Requests` and `Flask` libraries are used for communication through
HTTP. The usages are documented in `RESTServer` and `RESTClient`.

## Documentation

Documentation was generated using `pydoc` and exported to the `documentation/` folder of this repository. The main files are `chat.html`, `client.html`, `rdtp.html`, `rest.html`, and `server.html`. Each of these files links to others that describe the code in further detail.

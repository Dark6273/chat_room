import socket
from threading import Thread
from time import sleep

import database
from modules import security

HOST = "127.0.0.1"
PORT = 15000
LISTEN = 2
BUFFER_SIZE = 1024


class Server:
    server = None
    maximum_connection: int = None
    connections: dict = {}

    def __init__(self, host: str = "127.0.0.1", port: int = 12345, listen: int = 1, maximum_connection: int = 10):
        self.activate_tcp_server(host, port, listen)
        self.maximum_connection = maximum_connection

    def activate_tcp_server(self, host, port, listen):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((host, port))
            self.server.listen(listen)
            print("TCP server successfully activated on address: %s:%s" % (host, port))
            database.add_log("TCP server successfully activated on address: %s:%s" % (host, port))
        except Exception as e:
            self.server.close()
            database.add_log(str(e), "critical", "core")
            raise e

        self.listen()

    def listen(self):
        try:
            while True:
                client, addr = self.server.accept()
                print(f'Got connection from {addr}')
                database.add_log(f'Got connection from {addr}')

                Thread(target=self.login_or_register_client, args=(client, addr)).start()
        except KeyboardInterrupt:
            self.__del__()
        except Exception as e:
            database.add_log(str(e), "warning", "core")
            print(e)

    def login_or_register_client(self, client, addr):
        message = client.recv(BUFFER_SIZE).decode('utf-8')

        if message.startswith('Registration'):
            self.register(client, addr, message)

        elif message.startswith('Login'):
            self.login(client, message)

        else:
            client.send("Invalid command, connection is closed!".encode('utf-8'))
            client.close()

    def register(self, client, addr, message):
        _, username, password = message.split()
        database.add_log(f"username: {username}", "debug", "Registering")
        user = database.create_new_user(username, password)

        if not user:
            msg = "Username is already registered, please try again.".encode("utf-8")
            database.add_log(f"username already taken!, username: {username}", "debug", "Registering")
        else:
            msg = "Registration successful. please try to login".encode("utf-8")
            database.add_log(f"Registration successful. username: {username}", "debug", "Registering")

        client.send(msg)
        self.login_or_register_client(client, addr)

    def login(self, client, message):
        _, username = message.split()

        if self.connections.get(username):
            client.send("Username already activated, server automatically remove previous connection".encode("utf-8"))
            self.connections[username]['client'].close()
            self.connections.pop(username)

        user = database.login_user(username)

        if not user:
            msg = "User not found. connection was closed".encode("utf-8")
            database.add_log("User not found. connection was closed", "debug", "Login")
            client.send(msg)
            client.close()
            return

        key = security.generate_key().hex()
        client.send(f"Key {key}".encode("utf-8"))
        cipher = security.AESCipher(key, True)
        self.connections[username] = {
            "client": client,
            "cipher": cipher
        }

        msg = client.recv(1024)
        username = cipher.decrypt_text(msg).replace("Hello ", "")
        self.broadcast(f"{username} join the chat room.")
        sleep(0.1)

        client.send(cipher.encrypt_text(f"Hi {username}, welcome to the chat room."))
        self.handle_command(client, username, cipher)

    def handle_command(self, client, username, cipher):
        command = None
        while True:
            encrypted_text = client.recv(BUFFER_SIZE)
            message = cipher.decrypt_text(encrypted_text)

            if message == "Please send the list of attendees.":
                command = "user-list"
                response = "Here is the list of attendees:\n"
                response += ",".join(self.connections.keys())

                encrypted_text = cipher.encrypt_text(response)
                client.send(encrypted_text)

            elif message.startswith("Public message,"):
                command = "public-message"
                data = message.split("\r\n")
                message_len = data[0].replace("Public message, length=", "").replace(":", "")
                message_body = data[1]

                database.add_message(message=message_body, sender=username)
                response = f"Public message from {username}, length: {message_len}\r\n{message_body}"
                self.broadcast(response)

            elif message.startswith("Private message,"):
                command = "private-message"
                data = message.split("\r\n")
                message_body = data[1]
                data = data[0].split(" to ")
                message_len = data[0].replace("Private message, length=", "")
                targets = data[1].replace(":", "").split(",")

                database.add_message(message=message_body, sender=username, receivers=targets)
                response = f"Private message, length: {message_len} from {username} to {','.join(targets)}:\r\n{message_body}"

                for target in targets:
                    self.send_private_message(response, target)

            elif message.startswith("Bye."):
                self.connections.pop(username)
                client.send(cipher.encrypt_text("close!"))
                client.close()

                self.broadcast(f"{username} left the chat room.")
                database.add_log(f"{username} left the chat room", "info", "handle_command")
                return

            database.add_log(f"Received message from <{username}> with command: <{command}>", "info", "handle_command")

    def send_private_message(self, message, to):
        try:
            message = self.connections[to]['cipher'].encrypt_text(message)
            self.connections[to]['client'].send(message)
        except Exception as e:
            database.add_log(f"{e}", "error", "private_message")

    def broadcast(self, message):
        for user, connection in self.connections.items():
            try:
                msg = connection['cipher'].encrypt_text(message)
                connection['client'].send(msg)
            except Exception as e:
                database.add_log(f"{e}", "error", "broadcast")

    def __del__(self):
        database.add_log("Server closed", "info", "core")
        self.server.close()


def main():
    Server(HOST, PORT, LISTEN)


if __name__ == "__main__":
    main()

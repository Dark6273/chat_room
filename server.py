import socket
from threading import Thread
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

        client.send(cipher.encrypt_text(f"Hi {username}, welcome to the chat room."))
        self.handle_command(client, username, cipher)

    def handle_command(self, client, username, cipher):
        while True:
            encrypted_text = client.recv(BUFFER_SIZE)
            message = cipher.decrypt_text(encrypted_text)

            if message == "Please send the list of attendees.":
                print(self.connections)
                response = "Here is the list of attendees:\n"
                response += ",".join(self.connections.keys())
                print(response)

                encrypted_text = cipher.encrypt_text(response)
                client.send(encrypted_text)

            elif message.startswith("Public message,"):
                data = message.split("\r\n")
                message_len = data[0].replace("Public message, length=", "").replace(":", "")
                message_body = data[1]

                response = f"Public message from {username}, length: {message_len}\r\n{message_body}"
                self.broadcast(response)

            elif message.startswith("Private message,"):
                data = message.split("\r\n")
                message_body = data[1]
                data = data[0].split(" to ")
                message_len = data[0].replace("Private message, length=", "")
                targets = data[1].replace(":", "").split(",")

                response = f"Private message, length: {message_len} from {username} to {','.join(targets)}:\r\n{message_body}"

                for target in targets:
                    self.send_private_message(response, target)

            elif message.startswith("Bye."):
                self.connections.pop(username)
                client.close()

                self.broadcast(f"{username} left the chat room.")
                return

    def send_private_message(self, message, to):
        try:
            message = self.connections[to]['cipher'].encrypt_text(message)
            self.connections[to]['client'].send(message)
        except:
            ...

    def broadcast(self, message):
        for connection in self.connections.values():
            try:
                message = connection['cipher'].encrypt_text(message)
                connection['client'].send(message)
            except:
                ...

    def __del__(self):
        self.server.close()


def main():
    Server(HOST, PORT, LISTEN)


if __name__ == "__main__":
    main()

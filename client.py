import socket
from modules import security
from threading import Thread


class Client:
    cipher = None
    username = None
    socket = None

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.connect()

    def connect(self):
        sock = socket.socket()
        sock.connect((self.host, self.port))
        self.socket = sock
        self.login_or_register()

    def login_or_register(self):
        login = input("login or register ? ").lower()

        if login == "register":
            username = input("Enter your username: ")
            password = input("Enter your password: ")
            self.socket.send(f"Registration {username} {password}".encode("utf-8"))

            response = self.socket.recv(1024).decode("utf-8")
            print(response)

        elif login == "login":
            username = input("Enter your username: ")
            self.socket.send(f"Login {username}".encode("utf-8"))

            response = self.socket.recv(1024).decode("utf-8")

            if response.startswith("User not found"):
                print(response)
                self.socket.close()
                exit(0)

            if not response.startswith("Key"):
                response = self.socket.recv(1024).decode('utf-8')

            _, key = response.split(" ")
            print(key)
            self.cipher = security.AESCipher(key, True)

            msg = self.cipher.encrypt_text(f"Hello {username}")
            self.socket.send(msg)
            self.username = username

            self.handel_connection()
        else:
            print("Invalid command")
            self.login_or_register()

    def handel_connection(self):
        Thread(target=self.get_message).start()

        while True:
            command = input("Enter command: ").lower()

            if command == "\help":
                self.board()

            elif command == "users":
                msg = self.cipher.encrypt_text("Please send the list of attendees.")
                self.socket.send(msg)

            elif command == "public":
                message = input("Enter your message: ")
                length = len(message)

                msg = self.cipher.encrypt_text(f"Public message, length={length}:\r\n{message}")
                self.socket.send(msg)

            elif command == "private":
                message = input("Enter your message: ")
                length = len(message)
                targets = input("Enter your targets to form -> <user1, user2>\n")

                msg = self.cipher.encrypt_text(f"Private message, length={length} to {targets}:\r\n{message}")
                self.socket.send(msg)

            elif command == "bye":
                self.socket.send(self.cipher.encrypt_text("Bye."))
                self.socket.close()
            else:
                print("Wrone input")

    def board(self):
        board = """
command list ->
Users -> show list of activated users in chat room
Public -> send public message to chat room
Private -> send private message to chat
Bye -> exit from chat room
"""
        print(board)

    def get_message(self):
        while True:
            data = self.socket.recv(1024)

            if data:
                message = self.cipher.decrypt_text(data)
                print(message)

    def __del__(self):
        self.socket.close()


if __name__ == '__main__':
    client = Client('127.0.0.1', 15000)

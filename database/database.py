from datetime import datetime

from .models import User, UserMessage, Log, Message
from mongoengine import errors


def add_log(message: str, tag: str = 'info', section: str = None):
    Log(message=message, tag=tag, section=section).save()


def create_new_user(username: str, password: str, first_name: str = None, last_name: str = None) -> User | None:
    try:
        user = User(username=username, password=password, first_name=first_name, last_name=last_name)
        user.save()
        add_log(f"user created successfully, user_id: {user.id}")
        return user
    except errors.NotUniqueError:
        add_log("creat user failed, username already exists")
        return None


def login_user(username: str) -> User | None:
    user = User.objects(username=username).first()

    if not user:
        add_log(f"user does not exist, username: {username}")
        return None

    add_log(f"user successfully logged in, username: {username}")
    user.update(last_login=datetime.now())
    return user


def add_message(message: str, sender: str, receivers: list = None):
    sender = User.objects(username=sender).first()

    if receivers:
        rs = list()
        for receiver in receivers:
            rs.append(User.objects(username=receiver).first())

        msg = UserMessage(message=message, sender=sender, receiver=rs)
        msg.save()
        add_log(f"message created successfully, sender: {sender.id}, receiver: {rs}")
        return

    msg = Message(message=message, sender=sender)
    msg.save()
    add_log(f"message created successfully, sender: {sender.id}")

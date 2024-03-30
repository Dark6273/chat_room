from datetime import datetime
from mongoengine import *

connect('test')


class Log(Document):
    TAG_CHOICES = [
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
        ('debug', 'Debug'),
        ('info', 'Info')
    ]

    timestamp = DateTimeField(default=datetime.now)
    section = StringField(null=True)
    message = StringField(required=True)
    tag = StringField(choices=TAG_CHOICES)


class User(Document):
    first_name = StringField(null=True)
    last_name = StringField(null=True)
    username = StringField(unique=True, required=True)
    password = StringField(required=True)
    created_at = DateTimeField(default=datetime.now)
    last_login = DateTimeField(default=datetime.now)
    chats = ListField(ObjectIdField())
    groups = ListField(ObjectIdField())

    def __str__(self):
        return self.username


class BaseMessage(Document):
    sender = ReferenceField(User, required=True)
    message = StringField(required=True)
    created_at = DateTimeField(default=datetime.now)

    meta = {'allow_inheritance': True}

    def __str__(self):
        return self.message


class UserMessage(BaseMessage):
    receiver = ListField(ReferenceField(User))

    def __str__(self):
        return f"from: {self.sender}, to: {self.receiver}, message: {self.message[:10]}"


class Message(BaseMessage):
    def __str__(self):
        return f"from: {self.sender}, message: {self.message[:10]}"


if __name__ == '__main__':
    # user = User(first_name='dark', last_name='knight', username='dark6273', password='1234')
    # user.save()
    user = User.objects[0]
    print(user)

    # message = UserMessage(sender=user, receiver=user, message='hello world')
    # message.save()
    # message = UserMessage.objects[0]
    # print(message)
    message = Message(sender="dark", message="hello world")
    message.save()



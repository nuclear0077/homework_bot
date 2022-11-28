class MyBotException(Exception):
    pass


class UnexpectedAnswer(MyBotException):
    pass


class NotHomeWork(MyBotException):
    pass


class WrongAnswer(MyBotException):
    pass


class NotForSendingError(MyBotException):
    pass

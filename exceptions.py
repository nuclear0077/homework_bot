# кстати поковырял RequestException там такой же принцип!) 
class MyBotException(Exception):
    pass


class UnexpectedAnswer(MyBotException):
    pass


class NotHomeWork(MyBotException):
    pass


class WrongAnswer(MyBotException):
    pass
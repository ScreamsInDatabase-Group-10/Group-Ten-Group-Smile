from textual.message import Message

class LogoutMessage(Message):
    def __init__(self) -> None:
        super().__init__()
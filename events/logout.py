from textual.message import Message

# Dummy class for logout message
class LogoutMessage(Message):
    def __init__(self) -> None:
        super().__init__()
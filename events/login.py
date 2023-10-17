from textual.message import Message
from app_types import UserRecord

# Login success message
class LoginMessage(Message):
    def __init__(self, user: UserRecord) -> None:
        self.user = user
        super().__init__()
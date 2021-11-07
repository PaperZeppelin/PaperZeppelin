from enum import Enum

class Permissions(Enum):
    CREATE_INSTANT_INVITE: int = 0
    KICK_MEMBERS: int = 1
    BAN_MEMBERS: int = 2
    ADMINISTRATOR: int = 3
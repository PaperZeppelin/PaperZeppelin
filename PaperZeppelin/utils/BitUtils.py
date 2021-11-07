from enums.Permissions import Permissions


def has(bitset: str, permission: Permissions) -> bool:
    if int(bitset) & (1 << permission.value):
        return True
    else:
        return False
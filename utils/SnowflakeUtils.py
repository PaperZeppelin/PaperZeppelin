import datetime

DISCORD_EPOCH = 1420070400000


def timestamp_from_snowflake(snowflake: int) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(
        int((snowflake + DISCORD_EPOCH) >> 20) / 1000
    ).replace(tzinfo=None)

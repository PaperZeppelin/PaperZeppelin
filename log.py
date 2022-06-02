import logging

ANSII_CODE = "\x1b["


class LogStyles:
    RESET = "0"
    NORMAL = "0"
    BOLD = "1"
    DIMMED = "2"
    ITALIC = "3"
    UNDERLINE = "4"
    INVERSE = "5"
    STRIKETHROUGH = "6"
    BLACK = "7"


class LogForeGround:
    BLACK = "30"
    RED = "31"
    GREEN = "32"
    YELLOW = "33"
    BLUE = "34"
    MAGENTA = "35"
    CYAN = "36"
    LIGHT_GRAY = "37"


class LogBackGround:
    BLACK_BG = "40"
    RED_BG = "41"
    GREEN_BG = "42"
    YELLoW_BG = "43"
    BLUE_BG = "44"
    MAGENTA_BG = "45"
    CYAN_BG = "46"
    LIGHT_GRAY_BG = "47"


class LogColours:
    @staticmethod
    def colour(
        *,
        style: int | None = "0",
        foreground: int | None = "0",
        background: int | None = "0",
    ) -> str:
        """
        Builder method, builds a colour string
        """
        return f"{ANSII_CODE}{style};{foreground};{background}m"

    @staticmethod
    def reset() -> str:
        return LogColours.colour()


class Formatter(logging.Formatter):
    format = "%(asctime)s :: %(name)s :: %(levelname)s :: %(message)s"
    formats = {
        logging.DEBUG: LogColours.colour() + format + LogColours.reset(),
        logging.INFO: LogColours.colour(foreground=LogForeGround.BLUE)
        + format
        + LogColours.reset(),
        logging.WARNING: LogColours.colour(foreground=LogForeGround.YELLOW)
        + format
        + LogColours.reset(),
        logging.ERROR: LogColours.colour(foreground=LogForeGround.RED)
        + format
        + LogColours.reset(),
        logging.CRITICAL: LogColours.colour(
            style=LogStyles.BOLD, foreground=LogForeGround.RED
        )
        + format
        + LogColours.reset(),
    }

    def format(self, record: logging.LogRecord) -> str:
        fmt = logging.Formatter(self.formats.get(record.levelno))
        return fmt.format(record=record)


class BotLogger:
    """
    Reduced logger class for ease of use
    """

    def __init__(self, name: str, level: int):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        ch = logging.StreamHandler()
        ch.setLevel(level)  # Debug if DEV else Info
        ch.setFormatter(Formatter())
        self.logger.addHandler(ch)

    def debug(self, message, *args, exc_info: None | bool | BaseException = None):
        self.logger.debug(message, *args, exc_info=exc_info)

    def info(self, message, *args, exc_info: None | bool | BaseException = None):
        self.logger.info(message, *args, exc_info=exc_info)

    def warning(self, message, *args, exc_info: None | bool | BaseException = None):
        self.logger.warning(message, *args, exc_info=exc_info)

    def error(self, message, *args, exc_info: None | bool | BaseException = None):
        self.logger.error(message, *args, exc_info=exc_info)

    def critical(self, message, *args, exc_info: None | bool | BaseException = None):
        self.logger.critical(message, *args, exc_info=exc_info)

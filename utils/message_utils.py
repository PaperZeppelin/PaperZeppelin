from attr import has
import yaml
import typing

lang: typing.Union[dict, None] = None


def build(key: str, **kwargs) -> str:
    """Builds a message"""
    # TODO support embeds: fields/descriptions/titles/footers
    try:
        built = lang[key].format(**kwargs)
    except KeyError as e:  # two possible ways, build was called before `load` or key does not exist
        return key  # not found; return the key instead of erroring out
        # TODO implement exit strategy = return key or error out
    return built


def load(file: str = "lang/en_US.yaml") -> dict:
    """Loads the language file and returns it"""
    global lang
    with open(file, encoding="utf-8") as f:
        lang = yaml.safe_load(f)
    return lang

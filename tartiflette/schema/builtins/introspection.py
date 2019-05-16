import os

from typing import Any, Dict, Optional


def bake(schema_name: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Adds the introspection SDL.
    :param schema_name: schema name to link with
    :param config: configuration of the introspection
    :type schema_name: str
    :type config: Optional[Dict[str, Any]]
    :return: the SDL related to the introspection
    :rtype: str
    """
    # pylint: disable=unused-argument
    with open(
        os.path.join(os.path.dirname(__file__), "introspection.sdl")
    ) as file:
        return file.read()

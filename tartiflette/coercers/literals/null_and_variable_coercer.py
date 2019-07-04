from typing import Any, Callable, Optional

from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.language.ast import NullValueNode, VariableNode
from tartiflette.utils.values import is_invalid_value


def null_and_variable_coercer_wrapper(coercer: Callable) -> Callable:
    """
    Factorization of the treatment making it possible to coerce a NullValueNode
    or a VariableNode.
    :param coercer: the pre-computed coercer to use on the value if not a
    NullValueNode neither a VariableNode
    :type coercer: Callable
    :return: the wrapped coercer
    :rtype: Callable
    """

    async def wrapper(
        node, ctx: Optional[Any], *args, variables=None, **kwargs
    ):
        if not node:
            return UNDEFINED_VALUE

        if isinstance(node, NullValueNode):
            return None

        if isinstance(node, VariableNode):
            if not variables:
                return UNDEFINED_VALUE

            value = variables.get(node.name.value, UNDEFINED_VALUE)
            if is_invalid_value(value):
                return UNDEFINED_VALUE

            # TODO: check this
            # if value is None and is_non_null_type(schema_type):
            #     return UNDEFINED_VALUE
            return value

        return await coercer(node, ctx, *args, variables=variables, **kwargs)

    return wrapper

from typing import Any, Callable, Dict, Optional, Union

from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.language.ast import NullValueNode


async def non_null_coercer(
    node: Union["ValueNode", "VariableNode"],
    ctx: Optional[Any],
    inner_coercer: Callable,
    *args,
    variables: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Any:
    """
    Checks if the value is NullValueNode and will raise an error if its the
    case or will try to coerce it.
    :param node: the AST node to treat
    :param ctx: context passed to the query execution
    :param inner_coercer: the pre-computed coercer to use on the value
    :param variables: the variables used in the GraphQL request
    :type node: Union[ValueNode, VariableNode]
    :type ctx: Optional[Any]
    :type inner_coercer: Callable
    :type variables: Optional[Dict[str, Any]]
    :return: the computed value
    :rtype: Any
    """
    if isinstance(node, NullValueNode):
        return UNDEFINED_VALUE

    return await inner_coercer(node, ctx, *args, variables=variables, **kwargs)

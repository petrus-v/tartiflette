from typing import Any, Callable, Dict, Optional, Union

from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.language.ast import VariableNode


async def literal_directives_coercer(
    node: Union["ValueNode", "VariableNode"],
    ctx: Optional[Any],
    coercer: Callable,
    directives: Callable,
    *args,
    variables: Optional[Dict[str, Any]] = None,
    is_input_field: bool = False,
    **kwargs,
) -> Any:
    """
    Executes the directives on the coerced value.
    :param node: the AST node to treat
    :param ctx: context passed to the query execution
    :param coercer: pre-computed coercer to use on the value
    :param directives: the directives to execute
    :param variables: the variables used in the GraphQL request
    :param is_input_field: determines whether or not the node is an InputField
    :type node: Union[ValueNode, VariableNode]
    :type ctx: Optional[Any]
    :type coercer: Callable
    :type directives: Callable
    :type variables: Optional[Dict[str, Any]]
    :type is_input_field: bool
    :return: the computed value
    :rtype: Any
    """
    result = await coercer(node, ctx, *args, variables=variables, **kwargs)

    # TODO: hum?...
    if (
        not directives
        or result is UNDEFINED_VALUE
        or (isinstance(node, VariableNode) and not is_input_field)
    ):
        return result

    return await directives(result, ctx, *args, context_coercer=ctx, **kwargs)

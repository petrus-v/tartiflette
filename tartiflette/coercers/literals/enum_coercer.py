from typing import Any, Dict, Optional, Union

from tartiflette.coercers.literals.null_and_variable_coercer import (
    null_and_variable_coercer_wrapper,
)
from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.language.ast import EnumValueNode
from tartiflette.utils.coercer_way import CoercerWay


@null_and_variable_coercer_wrapper
async def enum_coercer(
    node: Union["ValueNode", "VariableNode"],
    ctx: Optional[Any],
    enum: "GraphQLEnumType",
    *args,
    variables: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Any:
    """
    Computes the value of an enum.
    :param node: the AST node to treat
    :param ctx: context passed to the query execution
    :param enum: the GraphQLEnumType instance of the enum
    :param variables: the variables used in the GraphQL request
    :type node: Union[ValueNode, VariableNode]
    :type ctx: Optional[Any]
    :type enum: GraphQLEnumType
    :type variables: Optional[Dict[str, Any]]
    :return: the computed value
    :rtype: Any
    """
    # pylint: disable=unused-argument
    if not isinstance(node, EnumValueNode):
        return UNDEFINED_VALUE

    try:
        enum_value = enum.get_enum_value(node.value)

        # TODO: do better
        return await enum_value.directives[CoercerWay.INPUT](
            node.value, ctx, *args, **kwargs
        )
    except KeyError:
        return UNDEFINED_VALUE

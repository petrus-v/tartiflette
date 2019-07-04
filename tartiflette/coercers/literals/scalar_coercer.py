from typing import Any, Dict, Optional, Union

from tartiflette.coercers.literals.null_and_variable_coercer import (
    null_and_variable_coercer_wrapper,
)
from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.utils.values import is_invalid_value


@null_and_variable_coercer_wrapper
async def scalar_coercer(
    node: Union["ValueNode", "VariableNode"],
    ctx: Optional[Any],
    scalar: "GraphQLScalarType",
    *args,
    variables: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Any:
    """
    Computes the value of a scalar.
    :param node: the AST node to treat
    :param ctx: context passed to the query execution
    :param scalar: the GraphQLScalarType instance of the scalar
    :param variables: the variables used in the GraphQL request
    :type node: Union[ValueNode, VariableNode]
    :type ctx: Optional[Any]
    :type scalar: GraphQLScalarType
    :type variables: Optional[Dict[str, Any]]
    :return: the computed value
    :rtype: Any
    """
    # pylint: disable=unused-argument
    try:
        value = scalar.parse_literal(node)
        if not is_invalid_value(value):
            return value
    except Exception:  # pylint: disable=broad-except
        pass
    return UNDEFINED_VALUE

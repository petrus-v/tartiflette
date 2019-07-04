from typing import Any, Optional

from tartiflette.coercers.common import CoercionResult, coercion_error
from tartiflette.coercers.inputs.null_coercer import null_coercer_wrapper
from tartiflette.utils.values import is_invalid_value


@null_coercer_wrapper
async def scalar_coercer(
    node: "Node",
    value: Any,
    ctx: Optional[Any],
    scalar: "GraphQLScalarType",
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    Computes the value of a scalar.
    :param node: the AST node to treat
    :param value: the raw value to compute
    :param ctx: context passed to the query execution
    :param scalar: the GraphQLScalarType instance of the scalar
    :param path: the path traveled until this coercer
    :type node: Node
    :type value: Any
    :type ctx: Optional[Any]
    :type scalar: GraphQLScalarType
    :type path: Optional[Path]
    :return: the coercion result
    :rtype: CoercionResult
    """
    # pylint: disable=unused-argument
    try:
        coerced_value = scalar.coerce_input(value)
        if is_invalid_value(coerced_value):
            return CoercionResult(
                errors=[
                    coercion_error(
                        f"Expected type < {scalar.name} >", node, path
                    )
                ]
            )
    except Exception as e:  # pylint: disable=broad-except
        return CoercionResult(
            errors=[
                coercion_error(
                    f"Expected type < {scalar.name} >",
                    node,
                    path,
                    sub_message=str(e),
                    original_error=e,
                )
            ]
        )
    return CoercionResult(value=coerced_value)

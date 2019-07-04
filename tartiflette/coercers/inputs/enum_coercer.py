from typing import Any, Optional

from tartiflette.coercers.common import CoercionResult, coercion_error
from tartiflette.coercers.inputs.null_coercer import null_coercer_wrapper
from tartiflette.utils.coercer_way import CoercerWay


@null_coercer_wrapper
async def enum_coercer(
    node: "Node",
    value: Any,
    ctx: Optional[Any],
    enum: "GraphQLEnumType",
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    Computes the value of an enum.
    :param node: the AST node to treat
    :param value: the raw value to compute
    :param ctx: context passed to the query execution
    :param enum: the GraphQLEnumType instance of the enum
    :param path: the path traveled until this coercer
    :type node: Node
    :type value: Any
    :type ctx: Optional[Any]
    :type enum: GraphQLEnumType
    :type path: Optional[Path]
    :return: the coercion result
    :rtype: CoercionResult
    """
    try:
        enum_value = enum.get_enum_value(value)

        # TODO: do better
        return CoercionResult(
            value=(
                await enum_value.directives[CoercerWay.INPUT](
                    value, ctx, *args, **kwargs
                )
            )
        )
    except Exception:  # pylint: disable=broad-except
        # TODO: try to compute a suggestion list of valid values depending
        # on the invalid value sent and returns it as error sub message
        return CoercionResult(
            errors=[
                coercion_error(f"Expected type < {enum.name} >", node, path)
            ]
        )

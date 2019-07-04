import asyncio

from typing import Any, Callable, Optional

from tartiflette.coercers.common import CoercionResult, Path
from tartiflette.coercers.inputs.null_coercer import null_coercer_wrapper


@null_coercer_wrapper
async def list_coercer(
    node: "Node",
    value: Any,
    ctx: Optional[Any],
    inner_coercer: Callable,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    Computes the value of a list.
    :param node: the AST node to treat
    :param value: the raw value to compute
    :param ctx: context passed to the query execution
    :param inner_coercer: the pre-computed coercer to use on each value in the
    list
    :param path: the path traveled until this coercer
    :type node: Node
    :type value: Any
    :type ctx: Optional[Any]
    :type inner_coercer: Callable
    :type path: Optional[Path]
    :return: the coercion result
    :rtype: CoercionResult
    """
    # pylint: disable=too-many-locals
    if isinstance(value, list):
        results = await asyncio.gather(
            *[
                inner_coercer(
                    node,
                    item_value,
                    ctx,
                    *args,
                    path=Path(path, index),
                    **kwargs,
                )
                for index, item_value in enumerate(value)
            ]
        )

        errors = []
        coerced_values = []
        for coerced_value, coerce_errors in results:
            if coerce_errors:
                errors.extend(coerce_errors)
            elif not errors:
                coerced_values.append(coerced_value)

        return CoercionResult(value=coerced_values, errors=errors)

    coerced_item_value, coerced_item_errors = await inner_coercer(
        node, value, ctx, *args, path=path, **kwargs
    )
    return CoercionResult(
        value=[coerced_item_value], errors=coerced_item_errors
    )

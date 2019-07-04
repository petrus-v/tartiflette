from typing import Any, Callable, Optional

from tartiflette.coercers.common import CoercionResult, coercion_error
from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.types.exceptions.tartiflette import MultipleException
from tartiflette.utils.errors import is_coercible_exception


async def input_directives_coercer(
    node: "Node",
    value: Any,
    ctx: Optional[Any],
    coercer: Callable,
    directives: Callable,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    Executes the directives on the coerced value.
    :param node: the AST node to treat
    :param value: the raw value to compute
    :param ctx: context passed to the query execution
    :param coercer: pre-computed coercer to use on the value
    :param directives: the directives to execute
    :param path: the path traveled until this coercer
    :type node: Node
    :type value: Any
    :type ctx: Optional[Any]
    :type coercer: Callable
    :type directives: Callable
    :type path: Optional[Path]
    :return: the coercion result
    :rtype: CoercionResult
    """
    # pylint: disable=too-many-locals
    coercion_result = await coercer(
        node, value, ctx, *args, path=path, **kwargs
    )

    if not directives or coercion_result is UNDEFINED_VALUE:
        return coercion_result

    value, errors = coercion_result
    if errors:
        return coercion_result

    try:
        return CoercionResult(
            value=await directives(
                value, ctx, *args, context_coercer=ctx, **kwargs
            )
        )
    except Exception as raw_exception:  # pylint: disable=broad-except
        return CoercionResult(
            errors=[
                coercion_error(
                    str(raw_exception),
                    node,
                    path,
                    original_error=(
                        raw_exception
                        if not is_coercible_exception(raw_exception)
                        else None
                    ),
                )
                for raw_exception in (
                    raw_exception.exceptions
                    if isinstance(raw_exception, MultipleException)
                    else [raw_exception]
                )
            ]
        )

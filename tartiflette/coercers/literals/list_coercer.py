from typing import Any, Callable, Dict, Optional, Union

from tartiflette.coercers.literals.null_and_variable_coercer import (
    null_and_variable_coercer_wrapper,
)
from tartiflette.coercers.literals.utils import is_missing_variable
from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.language.ast import ListValueNode
from tartiflette.utils.values import is_invalid_value


@null_and_variable_coercer_wrapper
async def list_coercer(
    node: Union["ValueNode", "VariableNode"],
    ctx: Optional[Any],
    is_non_null_item_type: bool,
    inner_coercer: Callable,
    *args,
    variables: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Any:
    """
    Computes the value of a list.
    :param node: the AST node to treat
    :param ctx: context passed to the query execution
    :param is_non_null_item_type: determines whether or not the inner value is
    nullable
    :param inner_coercer: the pre-computed coercer to use on each value in the
    list
    :param variables: the variables used in the GraphQL request
    :type node: Union[ValueNode, VariableNode]
    :type ctx: Optional[Any]
    :type is_non_null_item_type: bool
    :type inner_coercer: Callable
    :type variables: Optional[Dict[str, Any]]
    :return: the computed value
    :rtype: Any
    """
    # pylint: disable=too-many-locals
    if isinstance(node, ListValueNode):
        coerced_values = []
        for item_node in node.values:
            if is_missing_variable(item_node, variables):
                if is_non_null_item_type:
                    return UNDEFINED_VALUE
                coerced_values.append(None)
                continue

            item_value = await inner_coercer(
                item_node, ctx, *args, variables=variables, **kwargs
            )
            if is_invalid_value(item_value):
                return UNDEFINED_VALUE
            coerced_values.append(item_value)
        return coerced_values

    coerced_value = await inner_coercer(
        node, ctx, *args, variables=variables, **kwargs
    )
    if is_invalid_value(coerced_value):
        return UNDEFINED_VALUE
    return [coerced_value]

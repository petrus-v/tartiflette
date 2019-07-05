from functools import partial
from typing import Callable

from tartiflette.coercers.literals.list_coercer import list_coercer
from tartiflette.coercers.literals.non_null_coercer import non_null_coercer
from tartiflette.types.helpers.definition import (
    is_list_type,
    is_non_null_type,
    is_wrapping_type,
)


def get_literal_coercer(schema_type: "GraphQLType") -> Callable:
    """
    Computes and returns the literal coercer to use for the filled in schema
    type.
    :param schema_type: the schema type for which compute the coercer
    :type schema_type: GraphQLType
    :return: the computed coercer wrap with directives if defined
    :rtype: Callable
    """
    inner_type = schema_type
    wrapper_coercers = []
    while is_wrapping_type(inner_type):
        wrapped_type = inner_type.wrapped_type
        if is_list_type(inner_type):
            wrapper_coercers.append(
                partial(
                    list_coercer,
                    is_non_null_item_type=is_non_null_type(wrapped_type),
                )
            )
        elif is_non_null_type(inner_type):
            wrapper_coercers.append(non_null_coercer)
        inner_type = wrapped_type

    try:
        coercer = inner_type.literal_coercer
    except AttributeError:
        # TODO: shouldn't happen since its should be validated at
        # `validate_document` step
        coercer = lambda *args, **kwargs: None  # Not an InputType anyway...

    for wrapper_coercer in reversed(wrapper_coercers):
        coercer = partial(wrapper_coercer, inner_coercer=coercer)

    return coercer

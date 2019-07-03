import asyncio

from functools import partial
from typing import Any, Callable, Dict, Optional

from tartiflette.coercers.common import CoercionResult, Path, coercion_error
from tartiflette.coercers.literal import literal_directives_coercer
from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.types.exceptions.tartiflette import MultipleException
from tartiflette.types.helpers.definition import (
    get_wrapped_type,
    is_enum_type,
    is_input_object_type,
    is_list_type,
    is_non_null_type,
    is_scalar_type,
    is_wrapping_type,
)
from tartiflette.utils.coercer_way import CoercerWay
from tartiflette.utils.directives import wraps_with_directives
from tartiflette.utils.errors import is_coercible_exception
from tartiflette.utils.values import is_invalid_value


def null_coercer_wrapper(coercer: Callable) -> Callable:
    """
    Skips the node coercion if the value is `None` and directly returns it.
    :param coercer: the pre-computed coercer to use on the value
    :type coercer: Callable
    :return: the wrapped coercer
    :rtype: Callable
    """

    async def wrapper(node, value: Any, ctx: Optional[Any], *args, **kwargs):
        if value is None:
            return CoercionResult(value=None)

        return await coercer(node, value, ctx, *args, **kwargs)

    return wrapper


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


@null_coercer_wrapper
async def input_object_coercer(
    node: "Node",
    value: Any,
    ctx: Optional[Any],
    input_object: "GraphQLInputObjectType",
    input_field_coercers: Dict[str, Callable],
    literal_field_coercers: Dict[str, Callable],
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    Computes the value of an input object.
    :param node: the AST node to treat
    :param value: the raw value to compute
    :param ctx: context passed to the query execution
    :param input_object: the GraphQLInputObjectType instance of the input
    object
    :param input_field_coercers: a dictionary of pre-computed input coercer for
    each input fields
    :param literal_field_coercers: a dictionary of pre-computed literal coercer
    for each input fields
    :param path: the path traveled until this coercer
    :type node: Node
    :type value: Any
    :type ctx: Optional[Any]
    :type input_object: GraphQLInputObjectType
    :type input_field_coercers: Dict[str, Callable]
    :type literal_field_coercers: Dict[str, Callable]
    :type path: Optional[Path]
    :return: the coercion result
    :rtype: CoercionResult
    """
    # pylint: disable=too-many-locals
    if not isinstance(value, dict):
        return CoercionResult(
            errors=[
                coercion_error(
                    f"Expected type < {input_object.name} > to be an object",
                    node,
                    path,
                )
            ]
        )

    errors = []
    coerced_values = {}
    fields = input_object.arguments

    for field_name, field in fields.items():
        field_value = value.get(field_name, UNDEFINED_VALUE)
        if is_invalid_value(field_value):
            if field.default_value is not None:
                coerced_values[field_name] = await literal_field_coercers[
                    field_name
                ](field.default_value, ctx, *args, **kwargs)
            elif is_non_null_type(field.gql_type):
                errors.append(
                    coercion_error(
                        f"Field < {Path(path, field_name)} > of required type "
                        f"< {field.gql_type} > was not provided",
                        node,
                    )
                )
            continue

        coerced_field_value, coerced_field_errors = await input_field_coercers[
            field_name
        ](node, field_value, ctx, *args, path=Path(path, field_name), **kwargs)
        if coerced_field_errors:
            errors.extend(coerced_field_errors)
        elif not errors:
            coerced_values[field_name] = coerced_field_value

    for field_name in value:
        if field_name not in fields:
            # TODO: try to compute a suggestion list of valid fields
            # depending on the invalid field name returns it as
            # error sub message
            errors.append(
                coercion_error(
                    f"Field < {field_name} > is not defined by type "
                    f"< {input_object.name} >",
                    node,
                    path,
                )
            )

    return CoercionResult(value=coerced_values, errors=errors)


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


async def non_null_coercer(
    node: "Node",
    value: Any,
    ctx: Optional[Any],
    schema_type: "GraphQLType",
    inner_coercer: Callable,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    Checks if the value is `None` and will raise an error if its the case or
    will try to coerce it.
    :param node: the AST node to treat
    :param value: the raw value to compute
    :param ctx: context passed to the query execution
    :param schema_type: the schema type of the expected value
    :param inner_coercer: the pre-computed coercer to use on the value
    :param path: the path traveled until this coercer
    :type node: Node
    :type value: Any
    :type ctx: Optional[Any]
    :type schema_type: GraphQLType
    :type inner_coercer: Callable
    :type path: Optional[Path]
    :return: the coercion result
    :rtype: CoercionResult
    """
    if value is None:
        return CoercionResult(
            errors=[
                coercion_error(
                    f"Expected non-nullable type < {schema_type} > not to be "
                    "null",
                    node,
                    path,
                )
            ]
        )
    return await inner_coercer(node, value, ctx, *args, path=path, **kwargs)


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


def get_input_coercer(schema_type: "GraphQLType") -> Callable:
    """
    Computes and returns the input coercer to use for the filled in schema
    type.
    :param schema_type: the schema type for which compute the coercer
    :type schema_type: GraphQLType
    :return: the computed coercer wrap with directives if defined
    :rtype: Callable
    """
    wrapped_type = get_wrapped_type(schema_type)

    wrapped_type_directives = (
        getattr(wrapped_type, "directives_definition", None) or []
    )

    if is_scalar_type(wrapped_type):
        coercer = partial(scalar_coercer, scalar=wrapped_type)
    elif is_enum_type(wrapped_type):
        coercer = partial(enum_coercer, enum=wrapped_type)
    elif is_input_object_type(wrapped_type):
        coercer = partial(
            input_object_coercer,
            input_object=wrapped_type,
            input_field_coercers={
                name: partial(
                    input_directives_coercer,
                    coercer=get_input_coercer(argument.graphql_type),
                    directives=wraps_with_directives(
                        directives_definition=getattr(
                            argument, "directives_definition", None
                        )
                        or [],
                        directive_hook="on_post_input_coercion",
                    ),
                )
                for name, argument in wrapped_type.arguments.items()
            },
            literal_field_coercers={
                name: partial(
                    literal_directives_coercer,
                    coercer=argument.literal_coercer,
                    directives=wraps_with_directives(
                        directives_definition=getattr(
                            argument, "directives_definition", None
                        )
                        or [],
                        directive_hook="on_post_input_coercion",
                    ),
                    is_input_field=True,
                )
                for name, argument in wrapped_type.arguments.items()
            },
        )
    else:
        coercer = lambda *args, **kwargs: None  # Not an InputType anyway...

    if wrapped_type_directives:
        directives = wraps_with_directives(
            directives_definition=wrapped_type_directives,
            directive_hook="on_post_input_coercion",
        )
        if directives:
            coercer = partial(
                input_directives_coercer,
                coercer=coercer,
                directives=directives,
            )

    inner_type = schema_type
    wrapper_coercers = []
    while is_wrapping_type(inner_type):
        if is_list_type(inner_type):
            wrapper_coercers.append(list_coercer)
        elif is_non_null_type(inner_type):
            wrapper_coercers.append(
                partial(non_null_coercer, schema_type=inner_type)
            )
        inner_type = inner_type.wrapped_type

    for wrapper_coercer in reversed(wrapper_coercers):
        coercer = partial(wrapper_coercer, inner_coercer=coercer)

    return coercer

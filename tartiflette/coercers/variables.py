import asyncio

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from tartiflette.coercers.common import CoercionResult
from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.types.helpers.definition import (
    is_input_type,
    is_non_null_type,
)
from tartiflette.utils.errors import graphql_error_from_nodes


async def variable_coercer(
    executable_variable_definition: "ExecutableVariableDefinition",
    raw_variable_values: Dict[str, Any],
    ctx: Optional[Any],
    input_coercer: Callable,
    literal_coercer: Callable,
) -> Union["CoercionResult", "UNDEFINED_VALUE"]:
    """
    Computes the value of a variable.
    :param executable_variable_definition: the variable definition to treat
    :param raw_variable_values: the raw variables values to coerce
    :param ctx: context passed to the query execution
    :param input_coercer: callable to use to compute the variable value
    :param literal_coercer: callable to use to compute AST node into value
    :type executable_variable_definition: ExecutableVariableDefinition
    :type raw_variable_values: Dict[str, Any]
    :type ctx: Optional[Any]
    :type input_coercer: Callable
    :type literal_coercer: Callable
    :return: the computed value of the variable definition
    :rtype: Union[CoercionResult, UNDEFINED_VALUE]
    """
    # pylint: disable=too-many-locals
    var_name = executable_variable_definition.name
    var_type = executable_variable_definition.graphql_type

    if not is_input_type(var_type):
        definition_type = executable_variable_definition.definition.type
        return CoercionResult(
            errors=[
                graphql_error_from_nodes(
                    f"Variable < ${var_name} > expected value of type "
                    f"< {definition_type} > which cannot be used as "
                    "an input type.",
                    nodes=definition_type,
                )
            ]
        )

    has_value = var_name in raw_variable_values
    value = raw_variable_values.get(var_name, UNDEFINED_VALUE)
    default_value = executable_variable_definition.default_value

    if not has_value and default_value is not UNDEFINED_VALUE:
        # TODO: shouldn't we check if the coerced value is `UNDEFINED_VALUE`?
        # IMO, we should never have `UNDEFINED_VALUE`. If `literal_coercer`
        # returns `UNDEFINED_VALUE` then we missed a check on the `validate`
        # document function or an exception should have been raised instead.
        return CoercionResult(value=await literal_coercer(default_value, ctx))

    if (not has_value or value is None) and is_non_null_type(var_type):
        return CoercionResult(
            errors=[
                graphql_error_from_nodes(
                    (
                        f"Variable < ${var_name} > of non-null type "
                        f"< {var_type} > must not be null."
                    )
                    if has_value
                    else (
                        f"Variable < ${var_name} > of required type "
                        f"< {var_type} > was not provided."
                    ),
                    nodes=executable_variable_definition.definition,
                )
            ]
        )

    if has_value:
        coerced_value, coerce_errors = await input_coercer(value, ctx)
        if coerce_errors:
            for coerce_error in coerce_errors:
                # TODO: incase of error raised in directives, message will be added? Is it ok?
                coerce_error.message = (
                    f"Variable < ${var_name} > got invalid value "
                    f"< {value} >; {coerce_error.message}"
                )
            return CoercionResult(errors=coerce_errors)
        return CoercionResult(value=coerced_value)

    return UNDEFINED_VALUE


async def coerce_variables(
    executable_variable_definitions: List["ExecutableVariableDefinition"],
    raw_variable_values: Dict[str, Any],
    ctx: Optional[Any],
) -> Tuple[Dict[str, Any], List["TartifletteError"]]:
    """
    Returns the computed values of the variables.
    :param executable_variable_definitions: the variable definitions to treat
    :param raw_variable_values: the raw variables values to coerce
    :param ctx: context passed to the query execution
    :type executable_variable_definitions: List[ExecutableVariableDefinition]
    :type raw_variable_values: Dict[str, Any]
    :type ctx: Optional[Any]
    :return: the computed values of the variables
    :rtype: Tuple[Dict[str, Any], List["TartifletteError"]]
    """
    results = await asyncio.gather(
        *[
            executable_variable_definition.coercer(raw_variable_values, ctx)
            for executable_variable_definition in executable_variable_definitions
        ],
        return_exceptions=True,
    )

    coercion_errors: List["TartifletteError"] = []
    coerced_values: Dict[str, Any] = {}

    for executable_variable_definition, result in zip(
        executable_variable_definitions, results
    ):
        if result is UNDEFINED_VALUE:
            continue

        value, errors = result
        if errors:
            coercion_errors.extend(errors)
        else:
            coerced_values[executable_variable_definition.name] = value

    return coerced_values, coercion_errors

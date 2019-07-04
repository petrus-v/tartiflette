from typing import Any, Callable, Dict, Optional, Union

from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.language.ast import NullValueNode, VariableNode
from tartiflette.types.helpers.definition import is_non_null_type
from tartiflette.utils.errors import graphql_error_from_nodes
from tartiflette.utils.values import is_invalid_value


async def argument_coercer(
    argument_definition: "GraphQLArgument",
    node: Union["FieldNode", "DirectiveNode"],
    argument_node: Optional["ArgumentNode"],
    variable_values: Dict[str, Any],
    ctx: Optional[Any],
    directives: Callable,
) -> Any:
    """
    Computes the value of an argument.
    :param argument_definition: the argument definition to treat
    :param node: AST node linked to the argument
    :param argument_node: AST node representing the argument
    :param variable_values: the variables used in the GraphQL request
    :param ctx: context passed to the query execution
    :param directives: the directives to execute
    :type argument_definition: GraphQLArgument
    :type node: Union[FieldNode, DirectiveNode]
    :type argument_node: Optional[ArgumentNode]
    :type variable_values: Dict[str, Any]
    :type ctx: Optional[Any]
    :type directives: Callable
    :return: the computed value
    :rtype: Any
    """
    # pylint: disable=too-many-locals
    name = argument_definition.name
    arg_type = argument_definition.graphql_type

    if argument_node and isinstance(argument_node.value, VariableNode):
        variable_name = argument_node.value.name.value
        has_value = variable_values and variable_name in variable_values
        is_null = has_value and variable_values[variable_name] is None
    else:
        has_value = argument_node is not None
        is_null = argument_node and isinstance(
            argument_node.value, NullValueNode
        )

    coerced_value = UNDEFINED_VALUE
    if not has_value and argument_definition.default_value is not None:
        coerced_value = await argument_definition.literal_coercer(
            argument_definition.default_value, ctx, variables=variable_values
        )
    elif (not has_value or is_null) and is_non_null_type(arg_type):
        if is_null:
            raise graphql_error_from_nodes(
                f"Argument < {name} > of non-null type < {arg_type} > "
                "must not be null.",
                nodes=argument_node.value,
            )
        if argument_node and isinstance(argument_node.value, VariableNode):
            raise graphql_error_from_nodes(
                f"Argument < {name} > of required type < {arg_type} > "
                f"was provided the variable < ${variable_name} > which "
                "was not provided a runtime value.",
                nodes=argument_node.value,
            )
        raise graphql_error_from_nodes(
            f"Argument < {name} > of required type < {arg_type} > was "
            "not provided.",
            nodes=node,
        )
    elif has_value:
        if isinstance(argument_node.value, NullValueNode):
            coerced_value = None
        elif isinstance(argument_node.value, VariableNode):
            variable_name = argument_node.value.name.value
            coerced_value = variable_values[variable_name]
        else:
            value_node = argument_node.value
            coerced_value = await argument_definition.literal_coercer(
                value_node, ctx, variables=variable_values
            )
            if is_invalid_value(coerced_value):
                raise graphql_error_from_nodes(
                    f"Argument < {name} > has invalid value "
                    f"< {value_node} >.",
                    nodes=argument_node.value,
                )

    if not directives or coerced_value is UNDEFINED_VALUE:
        return coerced_value

    return await directives(
        node, argument_node, coerced_value, ctx, context_coercer=ctx
    )

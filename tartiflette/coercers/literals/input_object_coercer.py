from typing import Any, Dict, Optional, Union

from tartiflette.coercers.literals.null_and_variable_coercer import (
    null_and_variable_coercer_wrapper,
)
from tartiflette.coercers.literals.utils import is_missing_variable
from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.language.ast import ObjectValueNode
from tartiflette.utils.values import is_invalid_value


@null_and_variable_coercer_wrapper
async def input_object_coercer(
    node: Union["ValueNode", "VariableNode"],
    ctx: Optional[Any],
    input_object: "GraphQLInputObjectType",
    *args,
    variables: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Any:
    """
    Computes the value of an input object.
    :param node: the AST node to treat
    :param ctx: context passed to the query execution
    :param input_object: the GraphQLInputObjectType instance of the input
    object
    :param variables: the variables used in the GraphQL request
    :type node: Union[ValueNode, VariableNode]
    :type ctx: Optional[Any]
    :type input_object: GraphQLInputObjectType
    :type variables: Optional[Dict[str, Any]]
    :return: the computed value
    :rtype: Any
    """
    # pylint: disable=too-many-locals
    # TODO: tmp fix for cyclic imports
    from tartiflette.types.helpers.definition import is_non_null_type

    if not isinstance(node, ObjectValueNode):
        return UNDEFINED_VALUE

    field_nodes = {
        field_node.name.value: field_node for field_node in node.fields
    }
    input_fields = input_object.arguments

    coerced_object = {}
    for input_field_name, input_field in input_fields.items():
        if input_field_name not in field_nodes or is_missing_variable(
            field_nodes[input_field_name].value, variables
        ):
            if input_field.default_value is not None:
                input_field_node = input_field.default_value
            elif is_non_null_type(input_field.graphql_type):
                return UNDEFINED_VALUE
            else:
                continue
        else:
            input_field_node = field_nodes[input_field_name].value

        input_field_value = await input_field.literal_coercer(
            input_field_node, ctx, *args, variables=variables, **kwargs
        )
        if is_invalid_value(input_field_value):
            return UNDEFINED_VALUE
        coerced_object[input_field_name] = input_field_value
    return coerced_object

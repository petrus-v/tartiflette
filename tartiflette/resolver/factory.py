from functools import partial
from typing import Any, Callable, List, Optional, Union

from tartiflette.execution.types import build_resolve_info
from tartiflette.resolver.default import default_field_resolver
from tartiflette.types.helpers.get_directive_instances import (
    compute_directive_nodes,
)
from tartiflette.utils.coercer_way import CoercerWay
from tartiflette.utils.directives import wraps_with_directives
from tartiflette.utils.errors import located_error


def handle_field_error(
    raw_error: Exception,
    field_nodes: List["FieldNode"],
    path: "Path",
    return_type: "GraphQLOutputType",
    execution_context: "ExecutionContext",
) -> None:
    """
    Computes the raw error to a TartifletteError and add it to the execution
    context or bubble up the error if the field can't be null.
    :param raw_error: the raw exception to be treated
    :param field_nodes: AST nodes related to the resolved field
    :param path: the path traveled until this field
    :param return_type: GraphQLOutputType instance of the resolved field
    :param execution_context: instance of the query execution context
    :type raw_error: Exception
    :type field_nodes: List[FieldNode]
    :type path: Path
    :type return_type: GraphQLOutputType
    :type execution_context: ExecutionContext
    :rtype: None
    """
    # TODO: tmp fix for cyclic imports
    from tartiflette.types.helpers.definition import is_non_null_type

    error = located_error(raw_error, field_nodes, path.as_list())

    # If the field type is non-nullable, then it is resolved without any
    # protection from errors, however it still properly locates the error.
    if is_non_null_type(return_type):
        raise error

    # Otherwise, error protection is applied, logging the error and resolving
    # a null value for this field if one is encountered.
    execution_context.add_error(error)
    return None


async def complete_value_catching_error(
    execution_context: "ExecutionContext",
    field_nodes: List["FieldNode"],
    info: "ResolveInfo",
    path: "Path",
    result: Any,
    output_coercer: Callable,
    return_type: "GraphQLOutputType",
) -> Any:
    """
    Coerce the resolved field value or catch the resolver exception to add it
    to the execution context.
    :param execution_context: instance of the query execution context
    :param field_nodes: AST nodes related to the resolved field
    :param info: information related to the execution and the resolved field
    :param path: the path traveled until this resolver
    :param result: resolved field value
    :param output_coercer: pre-computed callable to coerce the result value
    :param return_type: GraphQLOutputType instance of the resolved field
    :type execution_context: ExecutionContext
    :type field_nodes: List[FieldNode]
    :type info: ResolveInfo
    :type path: Path
    :type result: Any
    :type output_coercer: Callable
    :type return_type: GraphQLOutputType
    :return: the coerced resolved field value
    :rtype: Any
    """
    try:
        if isinstance(result, Exception):
            raise result

        return await output_coercer(
            result=result,
            execution_context=execution_context,
            field_nodes=field_nodes,
            info=info,
            path=path,
        )
    except Exception as raw_exception:  # pylint: disable=broad-except
        return handle_field_error(
            raw_exception, field_nodes, path, return_type, execution_context
        )


async def resolve_field_value_or_error(
    execution_context: "ExecutionContext",
    field_definition: "GraphQLField",
    field_nodes: List["FieldNode"],
    resolver: Callable,
    source: Any,
    info: "ResolveInfo",
) -> Union[Exception, Any]:
    """
    Coerce the field's arguments and then try to resolve the field.
    :param execution_context: instance of the query execution context
    :param field_definition: GraphQLField instance of the resolved field
    :param field_nodes: AST nodes related to the resolved field
    :param resolver: callable to use to resolve the field
    :param source: default root value or field parent value
    :param info: information related to the execution and the resolved field
    :type execution_context: ExecutionContext
    :type field_definition: GraphQLField
    :type field_nodes: List[FieldNode]
    :type resolver: Callable
    :type source: Any
    :type info: ResolveInfo
    :return: the resolved field value
    :rtype: Union[Exception, Any]
    """
    # pylint: disable=too-many-locals
    # TODO: tmp fix for cyclic imports
    from tartiflette.coercers.arguments import coerce_arguments
    from tartiflette.types.helpers.definition import get_wrapped_type

    try:
        computed_directives = []
        for field_node in field_nodes:
            computed_directives.extend(
                compute_directive_nodes(
                    execution_context.schema,
                    field_node.directives,
                    execution_context.variable_values,
                )
            )

        resolver = wraps_with_directives(
            directives_definition=computed_directives,
            directive_hook="on_field_execution",
            func=resolver,
            is_resolver=True,
        )

        result = await resolver(
            source,
            await coerce_arguments(
                field_definition.arguments,
                field_nodes[0],
                execution_context.variable_values,
                execution_context.context,
            ),
            execution_context.context,
            info,
            context_coercer=execution_context.context,
        )

        # TODO: refactor this :)
        if not isinstance(result, Exception):
            rtype = get_wrapped_type(field_definition.graphql_type)
            if hasattr(rtype, "directives"):
                directives = rtype.directives.get(CoercerWay.OUTPUT)
                result = await directives(
                    result,
                    execution_context.context,
                    info,
                    context_coercer=execution_context.context,
                )
        return result
    except Exception as e:  # pylint: disable=broad-except
        return e


async def resolve_field(
    execution_context: "ExecutionContext",
    parent_type: "GraphQLObjectType",
    source: Any,
    field_nodes: List["FieldNode"],
    path: "Path",
    field_definition: "GraphQLField",
    resolver: Callable,
    output_coercer: Callable,
) -> Any:
    """
    Resolves the field value and coerce it before returning it.
    :param execution_context: instance of the query execution context
    :param parent_type: GraphQLObjectType of the field's parent
    :param source: default root value or field parent value
    :param field_nodes: AST nodes related to the resolved field
    :param path: the path traveled until this resolver
    :param field_definition: GraphQLField instance of the resolved field
    :param resolver: callable to use to resolve the field
    :param output_coercer: callable to use to coerce the resolved field value
    :type execution_context: ExecutionContext
    :type parent_type: GraphQLObjectType
    :type source: Any
    :type field_nodes: List[FieldNode]
    :type path: Path
    :type field_definition: GraphQLField
    :type resolver: Callable
    :type output_coercer: Callable
    :return: the coerced resolved field value
    :rtype: Any
    """
    info = build_resolve_info(
        execution_context, field_definition, field_nodes, parent_type, path
    )

    result = await resolve_field_value_or_error(
        execution_context,
        field_definition,
        field_nodes,
        resolver,
        source,
        info,
    )

    return await output_coercer(
        execution_context, field_nodes, info, path, result
    )


def get_field_resolver(
    field_definition: "GraphQLField",
    custom_default_resolver: Optional[Callable],
) -> Callable:
    """
    Computes and returns the resolver to use for the filled in field.
    :param field_definition: GraphQLField for which compute the resolver
    :param custom_default_resolver: callable that will replace the builtin
    default field resolver
    :type field_definition: GraphQLField
    :type custom_default_resolver: Optional[Callable]
    :return: the computed resolver for the field
    :rtype: Callable
    """
    # TODO: tmp fix for cyclic imports
    from tartiflette.coercers.output import get_output_coercer

    resolver = wraps_with_directives(
        directives_definition=field_definition.directives_definition,
        directive_hook="on_field_execution",
        func=(
            field_definition.raw_resolver
            or custom_default_resolver
            or default_field_resolver
        ),
        is_resolver=True,
    )

    return_type = field_definition.graphql_type

    return partial(
        resolve_field,
        field_definition=field_definition,
        resolver=resolver,
        output_coercer=partial(
            complete_value_catching_error,
            output_coercer=get_output_coercer(
                return_type, field_definition.type_resolver
            ),
            return_type=return_type,
        ),
    )

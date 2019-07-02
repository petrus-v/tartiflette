from typing import Any, Dict, List, Optional


class ResolveInfo:
    """
    Class containing the information related to a resolved field.
    """

    __slots__ = (
        "field_name",
        "field_nodes",
        "return_type",
        "parent_type",
        "path",
        "schema",
        "fragments",
        "root_value",
        "operation",
        "variable_values",
    )

    def __init__(
        self,
        field_name: str,
        field_nodes: List["FieldNodes"],
        return_type: "GraphQLOutputType",
        parent_type: "GraphQLObjectType",
        path: "Path",
        schema: "GraphQLSchema",
        fragments: Dict[str, "FragmentDefinitionNode"],
        root_value: Optional[Any],
        operation: "OperationDefinitionNode",
        variable_values: Optional[Dict[str, Any]],
    ):
        """
        :param field_name: name of the resolved field
        :param field_nodes: AST nodes related to the resolved field
        :param return_type: GraphQLOutputType instance of the resolved field
        :param parent_type: GraphQLObjectType of the field's parent
        :param path: the path traveled until this resolver
        :param schema: the GraphQLSchema schema instance linked to the engine
        :param fragments: the dictionary of fragment definition AST node
        contained in the request
        :param root_value: an initial value corresponding to the root type
        being executed
        :param operation: the AST operation definition node to execute
        :param variable_values: the variables used in the GraphQL request
        :type field_name: str
        :type field_nodes: List[FieldNodes]
        :type return_type: GraphQLOutputType
        :type parent_type: GraphQLObjectType
        :type path: Path
        :type schema: GraphQLSchema
        :type fragments: Dict[str, FragmentDefinitionNode]
        :type root_value: Optional[Any]
        :type operation: OperationDefinitionNode
        :type variable_values: Optional[Dict[str, Any]]
        """
        # pylint: disable=too-many-arguments,too-many-locals
        self.field_name = field_name
        self.field_nodes = field_nodes
        self.return_type = return_type
        self.parent_type = parent_type
        self.path = path
        self.schema = schema
        self.fragments = fragments
        self.root_value = root_value
        self.operation = operation
        self.variable_values = variable_values


def build_resolve_info(
    execution_context: "ExecutionContext",
    field_definition: "GraphQLField",
    field_nodes: List["FieldNode"],
    parent_type: "GraphQLObjectType",
    path: "Path",
) -> "ResolveInfo":
    """
    Builds & returns a ResolveInfo instance.
    :param execution_context: instance of the query execution context
    :param field_definition: GraphQLField instance of the resolved field
    :param field_nodes: AST nodes related to the resolved field
    :param parent_type: GraphQLObjectType of the field's parent
    :param path: the path traveled until this resolver
    :type execution_context: ExecutionContext
    :type field_definition: GraphQLField
    :type field_nodes: List[FieldNode]
    :type parent_type: GraphQLObjectType
    :type path: Path
    :return: a ResolveInfo instance
    :rtype: ResolveInfo
    """
    return ResolveInfo(
        field_definition.name,
        field_nodes,
        field_definition.graphql_type,
        parent_type,
        path,
        execution_context.schema,
        execution_context.fragments,
        execution_context.root_value,
        execution_context.operation,
        execution_context.variable_values,
    )

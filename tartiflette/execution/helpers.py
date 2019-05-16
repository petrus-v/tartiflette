from tartiflette.utils.errors import graphql_error_from_nodes


def get_field_definition(
    schema: "GraphQLSchema", parent_type: "GraphQLObjectType", field_name: str
) -> "GraphQLField":
    """
    This method looks up the field on the given type definition.
    It has special casing for the two introspection fields, __schema
    and __typename. __typename is special because it can always be
    queried as a field, even in situations where no other fields
    are allowed, like on a Union. __schema could get automatically
    added to the query type, but that would require mutating type
    definitions, which would cause issues.
    :param schema: the GraphQLSchema schema instance linked to the engine
    :param parent_type: GraphQLObjectType of the field's parent
    :param field_name: field name to retrieve
    :type schema: GraphQLSchema
    :type parent_type: GraphQLObjectType
    :type field_name: str
    :return: the GraphQLField instance
    :rtype: GraphQLField
    """
    try:
        parent_field = schema.get_field_by_name(f"{parent_type}.{field_name}")
        if parent_field is not None:
            return parent_field
    except Exception:  # pylint: disable=broad-except
        pass
    return None

    # TODO: should we implement something here?
    # if field_name == SchemaMetaFieldDefinition.name and parent_type is schema.query_type:
    #     return SchemaMetaFieldDefinition
    # if field_name == TypeMetaFieldDef.name and parent_type is schema.query_type:
    #     return TypeMetaFieldDef
    # if field_name == TypeNameMetaFieldDef.name:
    #     return TypeNameMetaFieldDef


def get_operation_root_type(
    schema: "GraphQLSchema", operation: "OperationDefinitionNode"
) -> "GraphQLObjectType":
    """
    Extracts the root type of the operation from the schema.
    :param schema: the GraphQLSchema schema instance linked to the engine
    :param operation: AST operation definition node from which retrieve the
    root type
    :type schema: GraphQLSchema
    :type operation: OperationDefinitionNode
    :return: the GraphQLObjectType instance related to the operation definition
    :rtype: GraphQLObjectType
    """
    operation_type = operation.operation_type
    if operation_type == "query":
        try:
            return schema.find_type(schema.query_type)
        except KeyError:
            raise graphql_error_from_nodes(
                "Schema does not define the required query root type.",
                nodes=operation,
            )
    if operation_type == "mutation":
        try:
            return schema.find_type(schema.mutation_type)
        except KeyError:
            raise graphql_error_from_nodes(
                "Schema is not configured for mutations.", nodes=operation
            )
    if operation_type == "subscription":
        try:
            return schema.find_type(schema.subscription_type)
        except KeyError:
            raise graphql_error_from_nodes(
                "Schema is not configured for subscriptions.", nodes=operation
            )
    raise graphql_error_from_nodes(
        "Can only have query, mutation and subscription operations.",
        nodes=operation,
    )

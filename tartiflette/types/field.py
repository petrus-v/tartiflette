from typing import Any, Callable, Dict, List, Optional, Union

from tartiflette.resolver.factory import get_field_resolver
from tartiflette.types.helpers.get_directive_instances import (
    compute_directive_nodes,
)
from tartiflette.types.type import GraphQLType
from tartiflette.utils.directives import wraps_with_directives


class GraphQLField:
    """
    Definition of a GraphQL field.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        name: str,
        gql_type: Union["GraphQLList", "GraphQLNonNull", str],
        arguments: Optional[Dict[str, "GraphQLArgument"]] = None,
        resolver: Optional[Callable] = None,
        description: Optional[str] = None,
        directives: Optional[List["DirectiveNode"]] = None,
        schema: Optional["GraphQLSchema"] = None,
    ) -> None:
        self.schema = schema
        self.name = name
        self.gql_type = gql_type
        self.arguments = arguments or {}
        self.description = description or ""

        # Directives
        self.directives = directives
        self.directives_definition: Optional[List[Dict[str, Any]]] = None
        self.introspection_directives: Optional[Callable] = None

        # Resolvers
        self.raw_resolver = resolver
        self.resolver: Optional[Callable] = None
        self.type_resolver: Optional[Callable] = None
        self.subscribe: Optional[Callable] = None

        # Introspection attributes
        self.isDeprecated = False  # pylint: disable=invalid-name

    def __eq__(self, other: Any) -> bool:
        """
        Returns True if `other` instance is identical to `self`.
        :param other: object instance to compare to `self`
        :type other: Any
        :return: whether or not `other` is identical to `self`
        :rtype: bool
        """
        return self is other or (
            isinstance(other, GraphQLField)
            and self.name == other.name
            and self.gql_type == other.gql_type
            and self.arguments == other.arguments
            and self.description == other.description
            and self.resolver == other.resolver
            and self.directives == other.directives
        )

    def __repr__(self) -> str:
        """
        Returns the representation of a GraphQLField instance.
        :return: the representation of a GraphQLField instance
        :rtype: str
        """
        return (
            "GraphQLField(name={!r}, gql_type={!r}, arguments={!r}, "
            "resolver={!r}, description={!r}, directives={!r})".format(
                self.name,
                self.gql_type,
                self.arguments,
                self.resolver,
                self.description,
                self.directives,
            )
        )

    def __str__(self) -> str:
        """
        Returns a human-readable representation of the field.
        :return: a human-readable representation of the field
        :rtype: str
        """
        return self.name

    # Introspection Attribute
    @property
    def kind(self) -> str:
        try:
            return self.gql_type.kind
        except AttributeError:
            pass
        return "FIELD"

    # Introspection Attribute
    @property
    def type(self) -> Union[str, "GraphQLType"]:
        if isinstance(self.gql_type, GraphQLType):
            return self.gql_type
        return self.schema.find_type(self.gql_type)

    # Introspection Attribute
    @property
    def args(self) -> List["GraphQLArgument"]:
        return list(self.arguments.values())

    @property
    def graphql_type(self) -> Union[str, "GraphQLType"]:
        if isinstance(self.gql_type, GraphQLType):
            return self.gql_type
        return self.schema.find_type(self.gql_type)

    def bake(
        self,
        schema: "GraphQLSchema",
        custom_default_resolver: Optional[Callable],
    ) -> None:
        """
        Bakes the GraphQLField and computes all the necessary stuff for
        execution.
        :param schema: the GraphQLSchema schema instance linked to the engine
        :param custom_default_resolver: callable that will replace the builtin
        default_resolver
        :type schema: GraphQLSchema
        :type custom_default_resolver: Optional[Callable]
        """
        self.schema = schema

        # Directives
        # TODO: we should be able to remove it when `get_field_resolver`
        # wouldn't need it anymore
        self.directives_definition = compute_directive_nodes(
            schema, self.directives
        )
        self.introspection_directives = wraps_with_directives(
            directives_definition=self.directives_definition,
            directive_hook="on_introspection",
        )

        for argument in self.arguments.values():
            argument.bake(schema)

        # Resolvers
        self.resolver = get_field_resolver(self, custom_default_resolver)

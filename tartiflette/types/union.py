from typing import Any, Callable, Dict, List, Optional, Set

from tartiflette.types.helpers.get_directive_instances import (
    compute_directive_nodes,
)
from tartiflette.types.type import GraphQLType
from tartiflette.utils.directives import wraps_with_directives


class GraphQLUnionType(GraphQLType):
    """
    Definition of a GraphQL union.
    """

    def __init__(
        self,
        name: str,
        gql_types: List[str],
        description: Optional[str] = None,
        directives: Optional[List["DirectiveNode"]] = None,
        schema: Optional["GraphQLSchema"] = None,
    ) -> None:
        super().__init__(schema)
        self.name = name
        self.gql_types = gql_types
        self.description = description
        self._possible_types: List["GraphQLType"] = []
        self._possible_types_set: Set[str] = set()
        self._fields: Dict[str, "GraphQLField"] = {}

        # Directives
        # TODO: we should be able to rename it to `self.directives` when
        # `coercion_output` will be properly managed
        self._directives = directives
        self.introspection_directives: Optional[Callable] = None
        # TODO: souldn't union have `self._directives_implementations` too?

    def __eq__(self, other: Any) -> bool:
        """
        Returns True if `other` instance is identical to `self`.
        :param other: object instance to compare to `self`
        :type other: Any
        :return: whether or not `other` is identical to `self`
        :rtype: bool
        """
        return self is other or (
            isinstance(other, GraphQLUnionType)
            and self.name == other.name
            and self.gql_types == other.gql_types
            and self.description == other.description
            # and self.directives == other.directives  # TODO: un-comment it
        )

    def __repr__(self) -> str:
        """
        Returns the representation of a GraphQLUnionType instance.
        :return: the representation of a GraphQLUnionType instance
        :rtype: str
        """
        return (
            "GraphQLUnionType(name={!r}, gql_types={!r}, "
            "description={!r}, directives={!r})".format(
                self.name, self.gql_types, self.description, self._directives
            )
        )

    def __str__(self) -> str:
        """
        Returns a human-readable representation of the union.
        :return: a human-readable representation of the union
        :rtype: str
        """
        return self.name

    # Introspection Attribute
    @property
    def kind(self) -> str:
        return "UNION"

    # Introspection Attribute
    @property
    def possibleTypes(  # pylint: disable=invalid-name
        self
    ) -> List["GraphQLType"]:
        return self._possible_types

    def add_field(self, value: "GraphQLField") -> None:
        if value.name == "__typename":
            self._fields[value.name] = value

    def find_field(self, name: str) -> "GraphQLField":
        return self._fields[name]

    def is_possible_type(self, gql_type: "GraphQLType") -> bool:
        """
        Determines if a GraphQLType is a possible types for the union.
        :param gql_type: the GraphQLType to check
        :type gql_type: GraphQLType
        :return: whether or not the GraphQLType is a possible type
        :rtype: bool
        """
        return gql_type.name in self._possible_types_set

    def bake(self, schema: "GraphQLSchema") -> None:
        """
        Bakes the GraphQLUnionType and computes all the necessary stuff for
        execution.
        :param schema: the GraphQLSchema schema instance linked to the engine
        :type schema: GraphQLSchema
        """
        super().bake(schema)

        for gql_type_name in self.gql_types:
            schema_type = schema.find_type(gql_type_name)
            self._possible_types.append(schema_type)
            self._possible_types_set.add(gql_type_name)

        # Directives
        self.introspection_directives = wraps_with_directives(
            directives_definition=compute_directive_nodes(
                schema, self._directives
            ),
            directive_hook="on_introspection",
        )

    def bake_fields(self, custom_default_resolver: Optional[Callable]) -> None:
        """
        Bakes union's fields.
        :param custom_default_resolver: callable that will replace the builtin
        default_resolver
        :type custom_default_resolver: Optional[Callable]
        """
        for field in self._fields.values():
            field.bake(self.schema, custom_default_resolver)

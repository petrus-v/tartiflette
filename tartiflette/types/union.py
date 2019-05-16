from typing import Any, Dict, List, Optional, Set

from tartiflette.types.helpers.get_directive_instances import (
    compute_directive_nodes,
)
from tartiflette.types.type import GraphQLType
from tartiflette.utils.directives import wraps_with_directives


class GraphQLUnionType(GraphQLType):
    """
    Union Type Definition

    When a field can return one of a heterogeneous set of types, a Union
    type is used to describe what types are possible as well as providing
    a function to determine which type is actually used when the field
    if resolved.
    """

    def __init__(
        self,
        name: str,
        gql_types: List[str],
        description: Optional[str] = None,
        schema: Optional["GraphQLSchema"] = None,
        directives: Optional[List[Dict[Any, Any]]] = None,
    ) -> None:
        super().__init__(name=name, description=description, schema=schema)
        self.gql_types = gql_types
        self._possible_types = []
        self._possible_types_set: Set[str] = set()
        self._directives = directives
        self._fields = {}

    def __repr__(self) -> str:
        return "{}(name={!r}, gql_types={!r}, description={!r})".format(
            self.__class__.__name__,
            self.name,
            self.gql_types,
            self.description,
        )

    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other) and self.gql_types == other.gql_types

    def is_possible_type(self, gql_type: "GraphQLType") -> bool:
        """
        Determines if a GraphQLType is a possible types for the union.
        :param gql_type: the GraphQLType to check
        :type gql_type: GraphQLType
        :return: whether or not the GraphQLType is a possible type
        :rtype: bool
        """
        return gql_type.name in self._possible_types_set

    # Introspection Attribute
    @property
    def kind(self) -> str:
        return "UNION"

    @property
    def is_union(self) -> bool:
        return True

    # Introspection Attribute
    @property
    def possibleTypes(  # pylint: disable=invalid-name
        self
    ) -> List[GraphQLType]:
        return self._possible_types

    def bake(self, schema: "GraphQLSchema") -> None:
        super().bake(schema)

        for gql_type_name in self.gql_types:
            schema_type = schema.find_type(gql_type_name)
            self._possible_types.append(schema_type)
            self._possible_types_set.add(gql_type_name)

        self._introspection_directives = wraps_with_directives(
            directives_definition=compute_directive_nodes(
                self._schema, self._directives
            ),
            directive_hook="on_introspection",
        )

    def add_field(self, value: "GraphQLField") -> None:
        if value.name == "__typename":
            self._fields[value.name] = value

    def find_field(self, name: str) -> "GraphQLField":
        return self._fields[name]

    def bake_fields(self, custom_default_resolver):
        for field in self._fields.values():
            try:
                field.bake(self._schema, self, custom_default_resolver)
            except AttributeError:
                pass

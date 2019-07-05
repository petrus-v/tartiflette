from typing import Any, Callable, Dict, List, Optional

from tartiflette.types.helpers.get_directive_instances import (
    compute_directive_nodes,
)
from tartiflette.types.type import GraphQLType
from tartiflette.utils.coercer_way import CoercerWay
from tartiflette.utils.directives import wraps_with_directives


class GraphQLInterfaceType(GraphQLType):
    """
    Definition of a GraphQL interface.
    """

    def __init__(
        self,
        name: str,
        fields: Dict[str, "GraphQLField"],
        description: Optional[str] = None,
        directives: Optional[List["DirectiveNode"]] = None,
        schema: Optional["GraphQLSchema"] = None,
    ) -> None:
        super().__init__(schema)
        self.name = name
        self._fields = fields
        self.description = description
        self._possible_types: List["GraphQLObjectType"] = []

        # Directives
        # TODO: we should be able to rename it to `self.directives` when
        # `coercion_output` will be properly managed
        self._directives = directives
        self.introspection_directives: Optional[Callable] = None
        self._directives_implementations: Dict[int, Callable] = {}

    def __eq__(self, other: Any) -> bool:
        """
        Returns True if `other` instance is identical to `self`.
        :param other: object instance to compare to `self`
        :type other: Any
        :return: whether or not `other` is identical to `self`
        :rtype: bool
        """
        return self is other or (
            isinstance(other, GraphQLInterfaceType)
            and self.name == other.name
            and self._fields == other._fields  # TODO: ugly?
            and self.description == other.description
            # and self.directives == other.directives  # TODO: un-comment it
        )

    def __repr__(self) -> str:
        """
        Returns the representation of a GraphQLInterfaceType instance.
        :return: the representation of a GraphQLInterfaceType instance
        :rtype: str
        """
        return (
            "GraphQLInterfaceType(name={!r}, fields={!r}, "
            "description={!r}, directives={!r})".format(
                self.name, self._fields, self.description, self._directives
            )
        )

    def __str__(self) -> str:
        """
        Returns a human-readable representation of the interface.
        :return: a human-readable representation of the interface
        :rtype: str
        """
        return self.name

    # Introspection Attribute
    @property
    def kind(self) -> str:
        return "INTERFACE"

    # Introspection Attribute
    @property
    def possibleTypes(  # pylint: disable=invalid-name
        self
    ) -> List["GraphQLObjectType"]:
        return self._possible_types

    # Introspection Attribute?
    @property
    def fields(self) -> List["GraphQLField"]:
        try:
            return [
                self._fields[field_name]
                for field_name in self._fields
                if not field_name.startswith("__")
            ]
        except (AttributeError, TypeError):
            pass
        return []

    @property
    def directives(self) -> Dict[int, Callable]:
        # TODO: we should be able to remove this when `coercion_output` will be
        # properly managed
        return self._directives_implementations

    def find_field(self, name: str) -> "GraphQLField":
        return self._fields[name]

    def bake(self, schema: "GraphQLSchema") -> None:
        """
        Bakes the GraphQLInterfaceType and computes all the necessary stuff for
        execution.
        :param schema: the GraphQLSchema schema instance linked to the engine
        :type schema: GraphQLSchema
        """
        super().bake(schema)

        # Directives
        directives_definition = compute_directive_nodes(
            schema, self._directives
        )
        self._directives_implementations = {
            CoercerWay.OUTPUT: wraps_with_directives(
                directives_definition=directives_definition,
                directive_hook="on_pre_output_coercion",
            )
        }
        self.introspection_directives = wraps_with_directives(
            directives_definition=directives_definition,
            directive_hook="on_introspection",
        )

    def bake_fields(self, custom_default_resolver: Optional[Callable]) -> None:
        """
        Bakes interface's fields.
        :param custom_default_resolver: callable that will replace the builtin
        default_resolver
        :type custom_default_resolver: Optional[Callable]
        """
        for field in self._fields.values():
            field.bake(self.schema, custom_default_resolver)

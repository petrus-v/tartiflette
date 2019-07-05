from typing import Any, Callable, Dict, List, Optional

from tartiflette.types.helpers.get_directive_instances import (
    compute_directive_nodes,
)
from tartiflette.types.type import GraphQLType
from tartiflette.utils.coercer_way import CoercerWay
from tartiflette.utils.directives import wraps_with_directives


class GraphQLObjectType(GraphQLType):
    """
    Definition of a GraphQL object.
    """

    def __init__(
        self,
        name: str,
        fields: Dict[str, "GraphQLField"],
        interfaces: Optional[List[str]] = None,
        description: Optional[str] = None,
        directives: Optional[List["DirectiveNode"]] = None,
        schema: Optional["GraphQLSchema"] = None,
    ) -> None:
        super().__init__(name=name, description=description, schema=schema)
        self._fields = fields
        self.interfaces_names = interfaces or []
        self.interfaces: List["GraphQLInterfaceType"] = []

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
            isinstance(other, GraphQLObjectType)
            and self.name == other.name
            and self._fields == other._fields  # TODO: ugly?
            and self.interfaces_names == other.interfaces_names
            and self.description == other.description
            # and self.directives == other.directives  # TODO: un-comment it
        )

    def __repr__(self) -> str:
        """
        Returns the representation of a GraphQLObjectType instance.
        :return: the representation of a GraphQLObjectType instance
        :rtype: str
        """
        return (
            "GraphQLObjectType(name={!r}, fields={!r}, "
            "interfaces={!r}, description={!r}, directives={!r})".format(
                self.name,
                self._fields,
                self.interfaces_names,
                self.description,
                self._directives,
            )
        )

    # Introspection Attribute
    @property
    def kind(self) -> str:
        return "OBJECT"

    # Introspection Attribute
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

    def add_field(self, value: "GraphQLField") -> None:
        self._fields[value.name] = value

    def find_field(self, name: str) -> "GraphQLField":
        return self._fields[name]

    def bake(self, schema: "GraphQLSchema") -> None:
        """
        Bakes the GraphQLObjectType and computes all the necessary stuff for
        execution.
        :param schema: the GraphQLSchema schema instance linked to the engine
        :type schema: GraphQLSchema
        """
        super().bake(schema)

        self.interfaces = []
        for interface_name in self.interfaces_names:
            interface = schema.find_type(interface_name)
            self.interfaces.append(interface)
            interface.possibleTypes.append(self)  # TODO: ugly!

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
        Bakes object's fields.
        :param custom_default_resolver: callable that will replace the builtin
        default_resolver
        :type custom_default_resolver: Optional[Callable]
        """
        for field in self._fields.values():
            field.bake(self.schema, custom_default_resolver)

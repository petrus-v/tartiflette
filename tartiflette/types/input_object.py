from typing import Any, Dict, List, Optional, Union

from tartiflette.types.helpers.get_directive_instances import (
    compute_directive_nodes,
)
from tartiflette.types.type import GraphQLType
from tartiflette.utils.coercer_way import CoercerWay
from tartiflette.utils.directives import wraps_with_directives


class GraphQLInputObjectType(GraphQLType):
    """Input Object Type Definition
    Input Object Type Definition

    An input object defines a structured collection of fields which may be
    supplied to a field argument.

    Using `NonNull` will ensure that a value must be provided by the query
    """

    def __init__(
        self,
        name: str,
        fields: Dict[str, "GraphQLArgument"],
        description: Optional[str] = None,
        schema: Optional["GraphQLSchema"] = None,
        directives: Optional[
            List[Dict[str, Union[str, Dict[str, Any]]]]
        ] = None,
    ) -> None:
        super().__init__(name=name, description=description, schema=schema)
        self._fields = fields
        self._input_fields: List["GraphQLArgument"] = list(
            self._fields.values()
        )
        self._directives = directives
        self.directives_definition = None
        self._directives_implementations = {}

    def __repr__(self) -> str:
        return "{}(name={!r})".format(self.__class__.__name__, self.name)

    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other) and self._fields == other._fields

    @property
    def arguments(self) -> Dict[str, "GraphQLArgument"]:
        return self._fields

    # Introspection Attribute
    @property
    def kind(self) -> str:
        return "INPUT_OBJECT"

    # Introspection Attribute
    @property
    def inputFields(  # pylint: disable=invalid-name
        self
    ) -> List["GraphQLArgument"]:
        return self.input_fields

    def bake(self, schema: "GraphQLSchema") -> None:
        super().bake(schema)
        self.directives_definition = compute_directive_nodes(
            self._schema, self._directives
        )
        self._directives_implementations = {
            CoercerWay.INPUT: wraps_with_directives(
                directives_definition=self.directives_definition,
                directive_hook="on_post_input_coercion",
            )
        }

        self._introspection_directives = wraps_with_directives(
            directives_definition=self.directives_definition,
            directive_hook="on_introspection",
        )

        for arg in self._fields.values():
            arg.bake(self._schema)

    @property
    def input_fields(self):
        return self._input_fields

    @property
    def directives(self):
        return self._directives_implementations

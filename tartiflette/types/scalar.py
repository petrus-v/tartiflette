from typing import Any, Dict, List, Optional, Union

from tartiflette.types.helpers.get_directive_instances import (
    compute_directive_nodes,
)
from tartiflette.types.type import GraphQLType
from tartiflette.utils.coercer_way import CoercerWay
from tartiflette.utils.directives import wraps_with_directives


class GraphQLScalarType(GraphQLType):
    """
    Scalar Type Definition

    The leaf values of any request and input values to arguments are
    Scalars (or Enums which are special Scalars) and are defined with a name
    and a series of functions used to convert to and from the request or SDL.

    Example: see the default Int, String or Boolean scalars.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        directives: Optional[
            List[Dict[str, Union[str, Dict[str, Any]]]]
        ] = None,
        schema: Optional["GraphQLSchema"] = None,
    ) -> None:
        super().__init__(name=name, description=description, schema=schema)
        self.coerce_output = None
        self.coerce_input = None
        self.parse_literal = None
        self._directives = directives
        self.directives_definition = None
        self._directives_implementations = {}

    def __repr__(self) -> str:
        return "{}(name={!r}, description={!r})".format(
            self.__class__.__name__, self.name, self.description
        )

    def __eq__(self, other: Any) -> bool:
        # TODO: Comparing function pointers is not ideal here...
        return (
            super().__eq__(other)
            and self.coerce_output == other.coerce_output
            and self.coerce_input == other.coerce_input
            and self.parse_literal == other.parse_literal
        )

    # Introspection Attribute
    @property
    def kind(self) -> str:
        return "SCALAR"

    def bake(self, schema):
        super().bake(schema)
        self.directives_definition = compute_directive_nodes(
            self._schema, self._directives
        )
        self._directives_implementations = {
            CoercerWay.OUTPUT: wraps_with_directives(
                directives_definition=self.directives_definition,
                directive_hook="on_pre_output_coercion",
            ),
            CoercerWay.INPUT: wraps_with_directives(
                directives_definition=self.directives_definition,
                directive_hook="on_post_input_coercion",
            ),
        }

        self._introspection_directives = wraps_with_directives(
            directives_definition=self.directives_definition,
            directive_hook="on_introspection",
        )

    @property
    def directives(self):
        return self._directives_implementations

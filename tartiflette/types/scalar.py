from functools import partial
from typing import Any, Dict, List, Optional, Union

from tartiflette.coercers.inputs.directives_coercer import (
    input_directives_coercer,
)
from tartiflette.coercers.inputs.scalar_coercer import (
    scalar_coercer as input_scalar_coercer,
)
from tartiflette.coercers.literals.directives_coercer import (
    literal_directives_coercer,
)
from tartiflette.coercers.literals.scalar_coercer import (
    scalar_coercer as literal_scalar_coercer,
)
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
        # Directives
        self._directives = directives
        self._directives_implementations = {}
        self.directives_definition = None

        # Coercers
        self.coerce_output = None
        self.coerce_input = None
        self.parse_literal = None
        self.input_coercer = None
        self.literal_coercer = None

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

    @property
    def directives(self):
        return self._directives_implementations

    def bake(self, schema: "GraphQLSchema") -> None:
        super().bake(schema)

        # Directives
        self.directives_definition = compute_directive_nodes(
            self._schema, self._directives
        )
        self._introspection_directives = wraps_with_directives(
            directives_definition=self.directives_definition,
            directive_hook="on_introspection",
        )
        post_input_coercion_directives = wraps_with_directives(
            directives_definition=self.directives_definition,
            directive_hook="on_post_input_coercion",
        )
        self._directives_implementations = {
            CoercerWay.OUTPUT: wraps_with_directives(
                directives_definition=self.directives_definition,
                directive_hook="on_pre_output_coercion",
            ),
            CoercerWay.INPUT: post_input_coercion_directives,
        }

        # Coercers
        self.input_coercer = partial(
            input_directives_coercer,
            coercer=partial(input_scalar_coercer, scalar_type=self),
            directives=post_input_coercion_directives,
        )
        self.literal_coercer = partial(
            literal_directives_coercer,
            coercer=partial(literal_scalar_coercer, scalar_type=self),
            directives=post_input_coercion_directives,
        )

from functools import partial
from typing import Any, Callable, Dict, List, Optional

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
    Definition of a GraphQL scalar.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        directives: Optional[List["DirectiveNode"]] = None,
        schema: Optional["GraphQLSchema"] = None,
    ) -> None:
        super().__init__(schema)
        self.name = name
        self.description = description

        # Directives
        # TODO: rename it into `self.directives` when removing the @property
        self._directives = directives
        self._directives_implementations: Dict[int, Callable] = {}
        self.introspection_directives: Optional[Callable] = None

        # Coercers
        self.coerce_output: Optional[Callable] = None
        self.coerce_input: Optional[Callable] = None
        self.parse_literal: Optional[Callable] = None
        self.input_coercer: Optional[Callable] = None
        self.literal_coercer: Optional[Callable] = None

    def __eq__(self, other: Any) -> bool:
        """
        Returns True if `other` instance is identical to `self`.
        :param other: object instance to compare to `self`
        :type other: Any
        :return: whether or not `other` is identical to `self`
        :rtype: bool
        """
        # TODO: comparing function pointers isn't ideal
        return self is other or (
            isinstance(other, GraphQLScalarType)
            and self.name == other.name
            and self.description == other.description
            and self.directives == other.directives
            and self.coerce_output == other.coerce_output
            and self.coerce_input == other.coerce_input
            and self.parse_literal == other.parse_literal
        )

    def __repr__(self) -> str:
        """
        Returns the representation of a GraphQLScalarType instance.
        :return: the representation of a GraphQLScalarType instance
        :rtype: str
        """
        return "GraphQLScalarType(name={!r}, description={!r})".format(
            self.name, self.description
        )

    def __str__(self) -> str:
        """
        Returns a human-readable representation of the scalar.
        :return: a human-readable representation of the scalar
        :rtype: str
        """
        return self.name

    # Introspection Attribute
    @property
    def kind(self) -> str:
        return "SCALAR"

    @property
    def directives(self) -> Dict[int, Callable]:
        # TODO: we should be able to remove this when `coercion_output` will be
        # properly managed
        return self._directives_implementations

    def bake(self, schema: "GraphQLSchema") -> None:
        """
        Bakes the GraphQLScalarType and computes all the necessary stuff for
        execution.
        :param schema: the GraphQLSchema schema instance linked to the engine
        :type schema: GraphQLSchema
        """
        super().bake(schema)

        # Directives
        directives_definition = compute_directive_nodes(
            schema, self._directives
        )
        self.introspection_directives = wraps_with_directives(
            directives_definition=directives_definition,
            directive_hook="on_introspection",
        )
        self._directives_implementations = {
            CoercerWay.OUTPUT: wraps_with_directives(
                directives_definition=directives_definition,
                directive_hook="on_pre_output_coercion",
            )
        }
        post_input_coercion_directives = wraps_with_directives(
            directives_definition=directives_definition,
            directive_hook="on_post_input_coercion",
        )

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

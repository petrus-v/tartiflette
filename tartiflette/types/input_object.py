from functools import partial
from typing import Any, Callable, Dict, List, Optional

from tartiflette.coercers.inputs.directives_coercer import (
    input_directives_coercer,
)
from tartiflette.coercers.inputs.input_object_coercer import (
    input_object_coercer as input_input_object_coercer,
)
from tartiflette.coercers.literals.directives_coercer import (
    literal_directives_coercer,
)
from tartiflette.coercers.literals.input_object_coercer import (
    input_object_coercer as literal_input_object_coercer,
)
from tartiflette.types.helpers.get_directive_instances import (
    compute_directive_nodes,
)
from tartiflette.types.type import GraphQLType
from tartiflette.utils.directives import wraps_with_directives


class GraphQLInputObjectType(GraphQLType):
    """
    Definition of a GraphQL input object.
    """

    def __init__(
        self,
        name: str,
        fields: Dict[str, "GraphQLInputField"],
        description: Optional[str] = None,
        directives: Optional[List["DirectiveNode"]] = None,
        schema: Optional["GraphQLSchema"] = None,
    ) -> None:
        super().__init__(name=name, description=description, schema=schema)
        self._fields = fields
        self._input_fields: List["GraphQLInputField"] = list(
            self._fields.values()
        )

        # Directives
        self.directives = directives

        # Coercers
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
        return self is other or (
            isinstance(other, GraphQLInputObjectType)
            and self.name == other.name
            and self._fields == other._fields  # TODO: ugly?
            and self.description == other.description
            and self.directives == other.directives
        )

    def __repr__(self) -> str:
        """
        Returns the representation of a GraphQLInputObjectType instance.
        :return: the representation of a GraphQLInputObjectType instance
        :rtype: str
        """
        return (
            "GraphQLInputObjectType(name={!r}, fields={!r}, description={!r}, "
            "directives={!r})".format(
                self.name, self._fields, self.description, self.directives
            )
        )

    # Introspection Attribute
    @property
    def kind(self) -> str:
        return "INPUT_OBJECT"

    # Introspection Attribute
    @property
    def inputFields(  # pylint: disable=invalid-name
        self
    ) -> List["GraphQLInputField"]:
        return self._input_fields

    # Introspection Attribute?
    @property
    def arguments(self) -> Dict[str, "GraphQLInputField"]:
        return self._fields

    def bake(self, schema: "GraphQLSchema") -> None:
        """
        Bakes the GraphQLInputObject and computes all the necessary stuff for
        execution.
        :param schema: the GraphQLSchema schema instance linked to the engine
        :type schema: GraphQLSchema
        """
        super().bake(schema)

        # Directives
        directives_definition = compute_directive_nodes(
            schema, self.directives
        )
        self._introspection_directives = wraps_with_directives(
            directives_definition=directives_definition,
            directive_hook="on_introspection",
        )
        post_input_coercion_directives = wraps_with_directives(
            directives_definition=directives_definition,
            directive_hook="on_post_input_coercion",
        )

        # Coercers
        self.input_coercer = partial(
            input_directives_coercer,
            coercer=partial(
                input_input_object_coercer, input_object_type=self
            ),
            directives=post_input_coercion_directives,
        )
        self.literal_coercer = partial(
            literal_directives_coercer,
            coercer=partial(
                literal_input_object_coercer, input_object_type=self
            ),
            directives=post_input_coercion_directives,
        )

        for input_field in self._fields.values():
            input_field.bake(schema)

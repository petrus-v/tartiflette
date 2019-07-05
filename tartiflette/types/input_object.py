from functools import partial
from typing import Any, Dict, List, Optional, Union

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
        fields: Dict[str, "GraphQLInputField"],
        description: Optional[str] = None,
        schema: Optional["GraphQLSchema"] = None,
        directives: Optional[
            List[Dict[str, Union[str, Dict[str, Any]]]]
        ] = None,
    ) -> None:
        super().__init__(name=name, description=description, schema=schema)
        self._fields = fields
        self._input_fields: List["GraphQLInputField"] = list(
            self._fields.values()
        )

        # Directives
        self._directives = directives
        self._directives_implementations = {}
        self.directives_definition = None

        # Coercers
        self.input_coercer = None
        self.literal_coercer = None

    def __repr__(self) -> str:
        return "{}(name={!r})".format(self.__class__.__name__, self.name)

    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other) and self._fields == other._fields

    @property
    def arguments(self) -> Dict[str, "GraphQLInputField"]:
        return self._fields

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
            CoercerWay.INPUT: post_input_coercion_directives
        }

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
            input_field.bake(self._schema)

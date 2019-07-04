from functools import partial
from typing import Any, Dict, List, Optional, Union

from tartiflette.coercers.inputs.compute import get_input_coercer
from tartiflette.coercers.inputs.directives_coercer import (
    input_directives_coercer,
)
from tartiflette.coercers.literals.compute import get_literal_coercer
from tartiflette.coercers.literals.directives_coercer import (
    literal_directives_coercer,
)
from tartiflette.types.helpers.get_directive_instances import (
    compute_directive_nodes,
)
from tartiflette.types.type import GraphQLType
from tartiflette.utils.directives import wraps_with_directives


class GraphQLInputField:
    """
    Definition of a GraphQL input field.
    """

    def __init__(
        self,
        name: str,
        gql_type: Union[str, GraphQLType],
        default_value: Optional[Any] = None,
        description: Optional[str] = None,
        directives: Optional[List[Dict[str, Optional[dict]]]] = None,
        schema=None,
    ) -> None:
        self._schema = schema
        self._type = {}
        self.name = name
        self.gql_type = gql_type
        self.default_value = default_value
        self.description = description

        # Directives
        self._directives = directives
        self._introspection_directives = None
        self.directives_definition = None

        # Coercers
        self.input_coercer = None
        self.literal_coercer = None

    def __repr__(self) -> str:
        return (
            "{}(name={!r}, gql_type={!r}, "
            "default_value={!r}, description={!r}, directives={!r})".format(
                self.__class__.__name__,
                self.name,
                self.gql_type,
                self.default_value,
                self.description,
                self.directives,
            )
        )

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: Any) -> bool:
        return self is other or (
            type(self) is type(other)
            and self.name == other.name
            and self.gql_type == other.gql_type
            and self.default_value == other.default_value
            and self.directives == other.directives
        )

    @property
    def schema(self) -> "GraphQLSchema":
        return self._schema

    @property
    def graphql_type(self) -> "GraphQLType":
        return (
            self.gql_type
            if isinstance(self.gql_type, GraphQLType)
            else self.schema.find_type(self.gql_type)
        )

    # Introspection Attribute
    @property
    def type(self) -> dict:
        return self._type

    @property
    def is_required(self) -> bool:
        if not isinstance(self.gql_type, GraphQLType):
            return False
        return self.gql_type.is_not_null and self.default_value is None

    @property
    def defaultValue(self) -> Any:  # pylint: disable=invalid-name
        return self.default_value

    @property
    def is_list_type(self) -> bool:
        if not isinstance(self.gql_type, str):
            return self.gql_type.is_list or self.gql_type.contains_a_list
        return False

    @property
    def directives(self) -> List[Dict[str, Any]]:
        return self.directives_definition

    @property
    def introspection_directives(self):
        return self._introspection_directives

    def bake(self, schema: "GraphQLSchema") -> None:
        self._schema = schema

        if isinstance(self.gql_type, GraphQLType):
            self._type = self.gql_type
        else:
            self._type["name"] = self.gql_type
            self._type["kind"] = self._schema.find_type(self.gql_type).kind

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

        # Coercers
        self.input_coercer = partial(
            input_directives_coercer,
            coercer=get_input_coercer(self.graphql_type),
            directives=post_input_coercion_directives,
        )
        self.literal_coercer = partial(
            literal_directives_coercer,
            coercer=get_literal_coercer(self.graphql_type),
            directives=post_input_coercion_directives,
            is_input_field=True,
        )

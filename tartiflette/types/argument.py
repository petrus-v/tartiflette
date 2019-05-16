from functools import partial
from typing import Any, Dict, List, Optional, Union

from tartiflette.coercers.arguments import argument_coercer
from tartiflette.coercers.literal import get_literal_coercer
from tartiflette.types.helpers.get_directive_instances import (
    compute_directive_nodes,
)
from tartiflette.types.type import GraphQLType
from tartiflette.utils.directives import wraps_with_directives


class GraphQLArgument:
    """
    Argument Definition

    Arguments are used for:
      - GraphQLField resolvers
      - GraphQLInputObject fields
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
        self.name = name
        self.gql_type = gql_type
        self.default_value = default_value
        self.description = description
        self._type = {}
        self._schema = schema
        self._directives = directives
        self.literal_coercer = None
        self.coercer = None

        # Introspection Attribute
        self.directives_definition = None
        self._introspection_directives = None

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
    def directives(self) -> List[Dict[str, Any]]:
        return self.directives_definition

    @property
    def introspection_directives(self):
        return self._introspection_directives

    @property
    def is_required(self) -> bool:
        if not isinstance(self.gql_type, GraphQLType):
            return False
        return self.gql_type.is_not_null and self.default_value is None

    @property
    def defaultValue(self) -> Any:  # pylint: disable=invalid-name
        return self.default_value

    def bake(self, schema: "GraphQLSchema") -> None:
        self._schema = schema
        self.directives_definition = compute_directive_nodes(
            self._schema, self._directives
        )

        self._introspection_directives = wraps_with_directives(
            directives_definition=self.directives_definition,
            directive_hook="on_introspection",
        )

        if isinstance(self.gql_type, GraphQLType):
            self._type = self.gql_type
        else:
            self._type["name"] = self.gql_type
            self._type["kind"] = self._schema.find_type(self.gql_type).kind

        self.literal_coercer = get_literal_coercer(self.graphql_type)
        self.coercer = partial(
            argument_coercer,
            directives=wraps_with_directives(
                directives_definition=self.directives_definition,
                directive_hook="on_argument_execution",
            ),
        )

    @property
    def is_list_type(self) -> bool:
        if not isinstance(self.gql_type, str):
            return self.gql_type.is_list or self.gql_type.contains_a_list
        return False

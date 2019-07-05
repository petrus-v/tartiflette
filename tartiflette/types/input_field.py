from functools import partial
from typing import Any, Callable, Dict, List, Optional, Union

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
        gql_type: Union["GraphQLList", "GraphQLNonNull", str],
        default_value: Optional["ValueNode"] = None,
        description: Optional[str] = None,
        directives: Optional[List["DirectiveNode"]] = None,
        schema: Optional["GraphQLSchema"] = None,
    ) -> None:
        self.schema = schema
        self._type: Union["GraphQLType", Dict[str, Any]] = {}
        self.name = name
        self.gql_type = gql_type
        self.default_value = default_value
        self.description = description

        # Directives
        self.directives = directives
        self.introspection_directives: Optional[Callable] = None

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
            isinstance(other, GraphQLInputField)
            and self.name == other.name
            and self.gql_type == other.gql_type
            and self.default_value == other.default_value
            and self.description == other.description
            and self.directives == other.directives
        )

    def __repr__(self) -> str:
        """
        Returns the representation of a GraphQLInputField instance.
        :return: the representation of a GraphQLInputField instance
        :rtype: str
        """
        return (
            "GraphQLInputField(name={!r}, gql_type={!r}, default_value={!r}, "
            "description={!r}, directives={!r})".format(
                self.name,
                self.gql_type,
                self.default_value,
                self.description,
                self.directives,
            )
        )

    def __str__(self) -> str:
        """
        Returns a human-readable representation of the input field.
        :return: a human-readable representation of the input field
        :rtype: str
        """
        return self.name

    # Introspection Attribute
    @property
    def type(self) -> Union["GraphQLType", Dict[str, Any]]:
        return self._type

    # Introspection Attribute?
    @property
    def defaultValue(self) -> Any:  # pylint: disable=invalid-name
        return self.default_value

    @property
    def graphql_type(self) -> "GraphQLType":
        return (
            self.gql_type
            if isinstance(self.gql_type, GraphQLType)
            else self.schema.find_type(self.gql_type)
        )

    def bake(self, schema: "GraphQLSchema") -> None:
        """
        Bakes the GraphQLInputField and computes all the necessary stuff for
        execution.
        :param schema: the GraphQLSchema schema instance linked to the engine
        :type schema: GraphQLSchema
        """
        self.schema = schema

        if isinstance(self.gql_type, GraphQLType):
            self._type = self.gql_type
        else:
            self._type["name"] = self.gql_type
            self._type["kind"] = schema.find_type(self.gql_type).kind

        # Directives
        directives_definition = compute_directive_nodes(
            schema, self.directives
        )
        self.introspection_directives = wraps_with_directives(
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
            coercer=get_input_coercer(self.graphql_type),
            directives=post_input_coercion_directives,
        )
        self.literal_coercer = partial(
            literal_directives_coercer,
            coercer=get_literal_coercer(self.graphql_type),
            directives=post_input_coercion_directives,
            is_input_field=True,
        )

from typing import Any, Optional, Union

from tartiflette.types.type import GraphQLType


class GraphQLList(GraphQLType):
    """
    Definition of a GraphQL list container.
    """

    def __init__(
        self,
        gql_type: Union["GraphQLNonNull", str],
        description: Optional[str] = None,
        schema: Optional["GraphQLSchema"] = None,
    ) -> None:
        super().__init__(name=None, description=description, schema=schema)
        self.gql_type = gql_type

    def __eq__(self, other: Any) -> bool:
        """
        Returns True if `other` instance is identical to `self`.
        :param other: object instance to compare to `self`
        :type other: Any
        :return: whether or not `other` is identical to `self`
        :rtype: bool
        """
        return self is other or (
            isinstance(other, GraphQLList)
            and self.name == other.name  # TODO: useless isn't?
            and self.gql_type == other.gql_type
            and self.description == other.description
        )

    def __repr__(self) -> str:
        """
        Returns the representation of a GraphQLList instance.
        :return: the representation of a GraphQLList instance
        :rtype: str
        """
        return "GraphQLList(gql_type={!r}, description={!r})".format(
            self.gql_type, self.description
        )

    def __str__(self) -> str:
        """
        Returns a human-readable representation of the list type.
        :return: a human-readable representation of the list type
        :rtype: str
        """
        return "[{!s}]".format(self.gql_type)

    # Introspection Attribute
    @property
    def ofType(self) -> "GraphQLType":
        return self.wrapped_type

    # Introspection Attribute?
    @property
    def kind(self) -> str:
        return "LIST"

    @property
    def wrapped_type(self) -> "GraphQLType":
        return (
            self.gql_type
            if isinstance(self.gql_type, GraphQLType)
            else self.schema.find_type(self.gql_type)
        )

from typing import Any, Optional


class GraphQLType:
    """
    Definition of a GraphQL type.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional["GraphQLSchema"] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.schema = schema

    def __eq__(self, other: Any) -> bool:
        """
        Returns True if `other` instance is identical to `self`.
        :param other: object instance to compare to `self`
        :type other: Any
        :return: whether or not `other` is identical to `self`
        :rtype: bool
        """
        return self is other or (
            type(self) is type(other)
            and self.name == other.name
            and self.description == other.description
        )

    def __repr__(self) -> str:
        """
        Returns the representation of a GraphQLType instance.
        :return: the representation of a GraphQLType instance
        :rtype: str
        """
        return "{}(name={!r}, description={!r})".format(
            self.__class__.__name__, self.name, self.description
        )

    def __str__(self) -> str:
        """
        Returns a human-readable representation of the type.
        :return: a human-readable representation of the type
        :rtype: str
        """
        return "{!s}".format(self.name)

    # Introspection Attribute
    @property
    def ofType(self) -> None:  # pylint: disable=invalid-name
        return None

    # Introspection Attribute?
    @property
    def kind(self) -> str:
        return "TYPE"

    def bake(self, schema: "GraphQLSchema") -> None:
        """
        Bakes the GraphQLType and computes all the necessary stuff for
        execution.
        :param schema: the GraphQLSchema schema instance linked to the engine
        :type schema: GraphQLSchema
        """
        self.schema = schema

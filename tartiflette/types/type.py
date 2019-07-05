from typing import Any, Optional


class GraphQLType:
    """
    Definition of a GraphQL type.
    """

    def __init__(self, schema: Optional["GraphQLSchema"] = None) -> None:
        self.schema = schema

    def __eq__(self, other: Any) -> bool:
        """
        Returns True if `other` instance is identical to `self`.
        :param other: object instance to compare to `self`
        :type other: Any
        :return: whether or not `other` is identical to `self`
        :rtype: bool
        """
        return self is other or type(self) is type(other)

    def __repr__(self) -> str:
        """
        Returns the representation of a GraphQLType instance.
        :return: the representation of a GraphQLType instance
        :rtype: str
        """
        return "{}()".format(self.__class__.__name__)

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

from functools import partial
from typing import Any, Callable, Dict, List, Optional, Union

from tartiflette.coercers.inputs.directives_coercer import (
    input_directives_coercer,
)
from tartiflette.coercers.inputs.enum_coercer import (
    enum_coercer as input_enum_coercer,
)
from tartiflette.coercers.literals.directives_coercer import (
    literal_directives_coercer,
)
from tartiflette.coercers.literals.enum_coercer import (
    enum_coercer as literal_enum_coercer,
)
from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.types.helpers.get_directive_instances import (
    compute_directive_nodes,
)
from tartiflette.types.type import GraphQLType
from tartiflette.utils.coercer_way import CoercerWay
from tartiflette.utils.directives import wraps_with_directives


class GraphQLEnumValue:
    """
    Definition of a GraphQL enum value.
    """

    def __init__(
        self,
        value: str,
        description: Optional[str] = None,
        directives: Optional[List["DirectiveNode"]] = None,
    ) -> None:
        self.value = value
        self.description = description
        self.schema: Optional["GraphQLSchema"] = None

        # Introspection attributes
        self.isDeprecated: bool = False  # pylint: disable=invalid-name

        # Directives
        # TODO: we should be able to rename it to `self.directives` when
        # `coercion_output` will be properly managed
        self._directives = directives
        self._directives_implementations: Dict[int, Callable] = {}
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
            isinstance(other, GraphQLEnumValue)
            and self.value == other.value
            and self.description == other.description
            # and self.directives == other.directives  # TODO: un-comment it
        )

    def __repr__(self) -> str:
        """
        Returns the representation of a GraphQLEnumValue instance.
        :return: the representation of a GraphQLEnumValue instance
        :rtype: str
        """
        return (
            "GraphQLEnumValue(value={!r}, description={!r}, "
            "directives={!r})".format(
                self.value, self.description, self._directives
            )
        )

    def __str__(self) -> str:
        """
        Returns a human-readable representation of the enum value.
        :return: a human-readable representation of the enum value
        :rtype: str
        """
        return str(self.value)

    # Introspection Attribute
    @property
    def name(self) -> str:
        return self.value

    @property
    def directives(self) -> Dict[int, Callable]:
        # TODO: we should be able to remove this when `coercion_output` will be
        # properly managed
        return self._directives_implementations

    def bake(self, schema: "GraphQLSchema") -> None:
        """
        Bakes the GraphQLEnumValue and computes all the necessary stuff for
        execution.
        :param schema: the GraphQLSchema schema instance linked to the engine
        :type schema: GraphQLSchema
        """
        self.schema = schema

        # Directives
        directives_definition = compute_directive_nodes(
            schema, self._directives
        )
        self._directives_implementations = {
            CoercerWay.OUTPUT: wraps_with_directives(
                directives_definition=directives_definition,
                directive_hook="on_pre_output_coercion",
            )
        }
        self.introspection_directives = wraps_with_directives(
            directives_definition=directives_definition,
            directive_hook="on_introspection",
        )

        # Coercers
        self.input_coercer = wraps_with_directives(
            directives_definition=directives_definition,
            directive_hook="on_post_input_coercion",
        )
        self.literal_coercer = wraps_with_directives(
            directives_definition=directives_definition,
            directive_hook="on_post_input_coercion",
        )


class GraphQLEnumType(GraphQLType):
    """
    Definition of a GraphQL enum type.
    """

    def __init__(
        self,
        name: str,
        values: List["GraphQLEnumValue"],
        description: Optional[str] = None,
        directives: Optional[List["DirectiveNode"]] = None,
        schema: Optional["GraphQLSchema"] = None,
    ) -> None:
        super().__init__(schema)
        self.name = name
        self.values = values
        self.description = description
        self._value_map: Dict[str, "GraphQLEnumValue"] = {}

        # Directives
        # TODO: we should be able to rename it to `self.directives` when
        # `coercion_output` will be properly managed
        self._directives = directives
        self.introspection_directives: Optional[Callable] = None
        self._directives_implementations: Dict[int, Callable] = {}
        self._directives_executors: Dict[int, Callable] = {
            CoercerWay.OUTPUT: self._output_directives_executor
        }

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
            isinstance(other, GraphQLEnumType)
            and self.name == other.name
            and self.values == other.values
            and self.description == other.description
            # and self.directives == other.directives  # TODO: un-comment it
        )

    def __repr__(self) -> str:
        """
        Returns the representation of a GraphQLEnumType instance.
        :return: the representation of a GraphQLEnumType instance
        :rtype: str
        """
        return (
            "GraphQLEnumType(name={!r}, values={!r}, description={!r}, "
            "directives={!r})".format(
                self.name, self.values, self.description, self._directives
            )
        )

    def __str__(self) -> str:
        """
        Returns a human-readable representation of the enum type.
        :return: a human-readable representation of the enum type
        :rtype: str
        """
        return self.name

    # Introspection Attribute
    @property
    def kind(self) -> str:
        return "ENUM"

    # Introspection Attribute
    @property
    def enumValues(  # pylint: disable=invalid-name
        self
    ) -> List["GraphQLEnumValue"]:
        return self.values

    @property
    def directives(self) -> Dict[int, Callable]:
        # TODO: we should be able to remove this when `coercion_output` will be
        # properly managed
        return self._directives_executors

    def get_value(self, name: str) -> "GraphQLEnumValue":
        """
        Returns the GraphQLEnumValue instance of the enum value `name`.
        :param name: the name of the enum value to fetch
        :type name: str
        :return: the GraphQLEnumValue instance of the enum value `name`
        :rtype: GraphQLEnumValue
        """
        return self._value_map[name]

    def coerce_output(self, value: Any) -> Union[str, "UNDEFINED_VALUE"]:
        return (
            self._value_map[value].value
            if value in self._value_map
            else UNDEFINED_VALUE
        )

    async def _output_directives_executor(self, val, *args, **kwargs):
        if isinstance(val, list):
            return [
                await self._output_directives_executor(x, *args, **kwargs)
                for x in val
            ]

        # Cause this is called PRE coercion, call directives if val is in value_map
        if val in self._value_map:
            # Call value directives
            val = await self._value_map[val].directives[CoercerWay.OUTPUT](
                val, *args, **kwargs
            )

        # Call Type directives
        return await self._directives_implementations[CoercerWay.OUTPUT](
            val, *args, **kwargs
        )

    def bake(self, schema: "GraphQLSchema") -> None:
        """
        Bakes the GraphQLEnumType and computes all the necessary stuff for
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
            coercer=partial(input_enum_coercer, enum_type=self),
            directives=post_input_coercion_directives,
        )
        self.literal_coercer = partial(
            literal_directives_coercer,
            coercer=partial(literal_enum_coercer, enum_type=self),
            directives=post_input_coercion_directives,
        )

        for enum_value in self.values:
            enum_value.bake(schema)
            self._value_map[enum_value.name] = enum_value

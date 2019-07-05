from functools import partial
from typing import Any, Dict, List, Optional, Union

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
    Enums are special leaf values.
    `GraphQLEnumValue`s is a way to represent them.
    """

    def __init__(
        self,
        value: Any = None,
        description: Optional[str] = None,
        directives: Optional[
            List[Dict[str, Union[str, Dict[str, Any]]]]
        ] = None,
    ) -> None:
        self._schema = None
        self.value = value
        self.description = description

        # Introspection Attribute
        self.isDeprecated = False  # pylint: disable=invalid-name

        # Directives
        self._directives = directives
        self._directives_implementations = None
        self._introspection_directives = None
        self.directives_definition = None

        # Coercers
        self.input_coercer = None
        self.literal_coercer = None

    def __repr__(self) -> str:
        return "{}(value={!r}, description={!r})".format(
            self.__class__.__name__, self.value, self.description
        )

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other: Any) -> bool:
        return self is other or (
            type(self) is type(other) and self.value == other.value
        )

    # Introspection Attribute
    @property
    def name(self) -> str:
        return self.value

    @property
    def directives(self) -> List[Dict[str, Any]]:
        return self._directives_implementations

    @property
    def introspection_directives(self):
        return self._introspection_directives

    def bake(self, schema: "GraphQLSchema") -> None:
        self._schema = schema
        self.directives_definition = compute_directive_nodes(
            self._schema, self._directives
        )
        self._directives_implementations = {
            CoercerWay.OUTPUT: wraps_with_directives(
                directives_definition=self.directives_definition,
                directive_hook="on_pre_output_coercion",
            )
        }

        self._introspection_directives = wraps_with_directives(
            directives_definition=self.directives_definition,
            directive_hook="on_introspection",
        )

        self.input_coercer = wraps_with_directives(
            directives_definition=self.directives_definition,
            directive_hook="on_post_input_coercion",
        )
        self.literal_coercer = wraps_with_directives(
            directives_definition=self.directives_definition,
            directive_hook="on_post_input_coercion",
        )


class GraphQLEnumType(GraphQLType):
    """
    Enum Type Definition

    Some leaf values of requests and input values are Enums.
    GraphQL serializes Enum values as strings, however internally
    Enums can be represented by any kind of type, often integers.

    Note: If a value is not provided in a definition,
    the name of the enum value will be used as its internal value.
    """

    def __init__(
        self,
        name: str,
        values: List[GraphQLEnumValue],
        description: Optional[str] = None,
        schema: Optional["GraphQLSchema"] = None,
        directives: Optional[
            List[Dict[str, Union[str, Dict[str, Any]]]]
        ] = None,
    ) -> None:
        super().__init__(
            name=name,
            description=description,
            is_enum_value=True,
            schema=schema,
        )
        self.values = values
        self._value_map = {}

        # Directives
        self._directives = directives
        self._directives_implementations = {}
        self._directives_executors = {
            CoercerWay.OUTPUT: self._output_directives_executor
        }
        self.directives_definition = None

        # Coercers
        self.input_coercer = None
        self.literal_coercer = None

    def __repr__(self) -> str:
        return "{}(name={!r}, values={!r}, description={!r})".format(
            self.__class__.__name__, self.name, self.values, self.description
        )

    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other) and self.values == other.values

    def coerce_output(self, val: Any) -> str:
        if val in self._value_map:
            return self._value_map[val].value
        return UNDEFINED_VALUE

    def get_value(self, name: str) -> str:
        """
        Returns the value of the enum value `name`.
        :param name: the name of the enum value to fetch
        :type name: str
        :return: the value of the enum value `name`
        :rtype: str
        """
        return self._value_map[name].value

    def get_enum_value(self, name: str) -> "GraphQLEnumValue":
        """
        Returns the GraphQLEnumValue instance of the enum value `name`.
        :param name: the name of the enum value to fetch
        :type name: str
        :return: the GraphQLEnumValue instance of the enum value `name`
        :rtype: GraphQLEnumValue
        """
        return self._value_map[name]

    # Introspection Attribute
    @property
    def kind(self) -> str:
        return "ENUM"

    # Introspection Attribute
    @property
    def enumValues(  # pylint: disable=invalid-name
        self
    ) -> List[GraphQLEnumValue]:
        return self.values

    @property
    def directives(self):
        return self._directives_executors

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
            CoercerWay.OUTPUT: wraps_with_directives(
                directives_definition=self.directives_definition,
                directive_hook="on_pre_output_coercion",
            )
        }

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

        for value in self.values:
            value.bake(schema)
            self._value_map[value.name] = value

from typing import Any, Callable, Dict, Optional

from tartiflette import Directive


class DeprecatedDirective:
    """
    Built-in directive to indicate deprecated portions of a GraphQL service’s
    schema, such as deprecated fields on a type or deprecated enum values.
    """

    async def on_introspection(
        self,
        directive_args: Dict[str, Any],
        next_directive: Callable,
        introspected_element: Any,
        ctx: Optional[Dict[str, Any]],
        info: "ResolveInfo",
    ) -> Any:
        """
        Marks the introspected element as deprecated.
        :param directive_args: arguments passed to the directive
        :param next_directive: next directive to call
        :param introspected_element: current introspected element
        :param ctx: context passed to the query execution
        :param info: information related to the execution
        :type directive_args: Dict[str, Any]
        :type next_directive: Callable
        :type introspected_element: Any
        :type ctx: Optional[Dict[str, Any]]
        :type info: ResolveInfo
        :return: the deprecated introspected element
        :rtype: Any
        """
        introspected_element = await next_directive(
            introspected_element, ctx, info
        )

        setattr(introspected_element, "isDeprecated", True)
        setattr(
            introspected_element, "deprecationReason", directive_args["reason"]
        )

        return introspected_element


def bake(schema_name: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Links the directive to the appropriate schema and returns the SDL related
    to the directive.
    :param schema_name: schema name to link with
    :param config: configuration of the directive
    :type schema_name: str
    :type config: Optional[Dict[str, Any]]
    :return: the SDL related to the directive
    :rtype: str
    """
    # pylint: disable=unused-argument
    Directive("deprecated", schema_name=schema_name)(DeprecatedDirective())
    return """
    directive @deprecated(
        reason: String = "Deprecated"
    ) on FIELD_DEFINITION | ENUM_VALUE
    """

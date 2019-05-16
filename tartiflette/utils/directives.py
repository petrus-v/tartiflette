from functools import partial
from typing import Any, Callable, Dict, List, Optional, Union


async def default_argument_execution_directive(
    parent_node: Union["FieldNode", "DirectiveNode"],
    argument_node: "ArgumentNode",
    value: Any,
    *args,
    **kwargs,
) -> Any:
    """
    Default callable to use to wrap with directives on `on_argument_execution`
    hook name.
    :param parent_node: the parent AST node related to the executed argument
    :param argument_node: the AST argument node executed
    :param value: the coerced value of the argument
    :type parent_node: Union[FieldNode, DirectiveNode]
    :type argument_node: ArgumentNode
    :type value: Any
    :return: the coerced value of the argument
    :rtype: Any
    """
    # pylint: disable=unused-argument
    return value


async def default_directive_callable(value: Any, *args, **kwargs) -> Any:
    """
    Default callable to use to wrap with directives when the hook doesn't
    implements a specific callable.
    :param value: the coerced value
    :type value: Any
    :return: the coerced value
    :rtype: Any
    """
    # pylint: disable=unused-argument
    return value


_DEFAULT_HOOKS_CALLABLE = {
    "on_argument_execution": default_argument_execution_directive
}


async def directive_executor(
    directive_func: Callable,
    directive_arguments_coercer: Callable,
    wrapped_func: Callable,
    *args,
    context_coercer: Optional[Any] = None,
    **kwargs,
) -> Any:
    """
    Wraps the execution of directives in order to handle properly the fact that
    directive arguments can be a dictionary or a callable.
    :param directive_func: callable representing the directive implementation
    :param directive_arguments_coercer: callable to use to coerce directive
    arguments
    :param context_coercer: context passed to the query execution to use on
    argument coercion process
    :param wrapped_func: the inner callable to call after the directive
    :type directive_func: Callable
    :type directive_args: Callable
    :type wrapped_func: Callable
    :type context_coercer: Optional[Any]
    :return: the computed value
    :rtype: Any
    """
    return await directive_func(
        await directive_arguments_coercer(ctx=context_coercer),
        partial(wrapped_func, context_coercer=context_coercer),
        *args,
        **kwargs,
    )


async def resolver_executor(resolver: Callable, *args, **kwargs) -> Any:
    """
    Wraos the execution of the raw resolver in order to pop the
    `context_coercer` keyword arguments to avoid exception.
    :param resolver: callable to wrap
    :type resolver: Callable
    :return: resolved value
    :rtype: Any
    """
    kwargs.pop("context_coercer", None)
    return await resolver(*args, **kwargs)


def wraps_with_directives(
    directives_definition: List[Dict[str, Any]],
    directive_hook: str,
    func: Optional[Callable] = None,
    is_resolver: bool = False,
) -> Callable:
    """
    Wraps a callable with directives.
    :param directives_definition: directives to wrap with
    :param directive_hook: name of the hook to wrap with
    :param func: callable to wrap
    :param is_resolver: determines whether or not the wrapped func is a
    resolver
    :type directives_definition: List[Dict[str, Any]]
    :type directive_hook: str
    :type func: Optional[Callable]
    :type is_resolver: bool
    :return: wrapped callable
    :rtype: Callable
    """
    if func is None:
        func = _DEFAULT_HOOKS_CALLABLE.get(
            directive_hook, default_directive_callable
        )

    if is_resolver and not isinstance(func, partial):
        func = partial(resolver_executor, func)

    for directive in reversed(directives_definition):
        if directive_hook in directive["callables"]:
            func = partial(
                directive_executor,
                directive["callables"][directive_hook],
                directive["arguments_coercer"],
                func,
            )
    return func

from typing import Callable, Optional

from tartiflette.schema.registry import SchemaRegistry
from tartiflette.schema.schema import GraphQLSchema
from tartiflette.schema.transformer import schema_from_sdl

_SCHEMA_OBJECT_IDS = ["directives", "resolvers", "scalars", "subscriptions"]


class SchemaBakery:
    @staticmethod
    def _preheat(schema_name: str) -> GraphQLSchema:
        schema_info = SchemaRegistry.find_schema_info(schema_name)
        sdl = schema_info["sdl"]

        schema = schema_from_sdl(sdl, schema_name=schema_name)

        for object_ids in _SCHEMA_OBJECT_IDS:
            for obj in schema_info.get(object_ids, {}).values():
                obj.bake(schema)

        schema_info["inst"] = schema

        return schema

    @staticmethod
    def bake(
        schema_name: str, custom_default_resolver: Optional[Callable] = None
    ) -> GraphQLSchema:
        schema = SchemaBakery._preheat(schema_name)
        schema.bake(custom_default_resolver)
        return schema

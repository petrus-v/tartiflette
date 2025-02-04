import pytest

from tartiflette import Resolver, create_engine


@Resolver("Query.viewer", schema_name="test_issue79")
async def resolver_query_viewer(*_, **__):
    return {"name": "N1"}


_SDL = """
type User {
    name: String
}

type Query {
    viewer: User
}
"""


@pytest.fixture(scope="module")
async def ttftt_engine():
    return await create_engine(sdl=_SDL, schema_name="test_issue79")


@pytest.mark.asyncio
async def test_issue79(ttftt_engine):
    query = """
    fragment UnknownFields on UnknownType {
        name
    }

    query {
        viewer {
            ...UnknownFields
        }
    }
    """

    results = await ttftt_engine.execute(query)

    assert results == {
        "data": None,
        "errors": [
            {
                "message": "Unknown type < UnknownType >.",
                "path": None,
                "locations": [{"line": 2, "column": 5}],
            },
            {
                "message": "Undefined fragment < UnknownFields >.",
                "path": None,
                "locations": [{"line": 8, "column": 13}],
            },
        ],
    }

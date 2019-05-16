import asyncio

import pytest

from tartiflette import Resolver, Subscription, create_engine

_SDL = """
type Query {
  search(query: String!): [String!]
}

type Subscription {
  newSearch(query: String!): [String!]
  customSearch(query: String!): [String!]
}
"""

_SEARCHS = [
    ["Search #1"],
    ["Search #2"],
    ["Search #3"],
    ["Search #4"],
    ["Search #5"],
]


@pytest.fixture(scope="module")
async def ttftt_engine():
    @Subscription("Subscription.newSearch", schema_name="test_subscribe")
    @Subscription("Subscription.customSearch", schema_name="test_subscribe")
    async def subscription_new_search(*_, **__):
        for search in _SEARCHS:
            yield {"newSearch": search}
            await asyncio.sleep(0.01)

    @Resolver("Subscription.customSearch", schema_name="test_subscribe")
    async def resolver_subscription_custom_search(parent, args, ctx, info):
        return [f"{search} #c" for search in parent["newSearch"]]

    return await create_engine(sdl=_SDL, schema_name="test_subscribe")


@pytest.mark.asyncio
async def test_subscribe(ttftt_engine):
    i = 0
    async for result in ttftt_engine.subscribe(
        """
        subscription {
          newSearch(query: "A query")
        }
        """
    ):
        i += 1
        assert result == {"data": {"newSearch": [f"Search #{i}"]}}

    assert i == 5


@pytest.mark.asyncio
async def test_subscribe_aliases(ttftt_engine):
    i = 0
    async for result in ttftt_engine.subscribe(
        """
        subscription {
          aSearch: newSearch(query: "A query")
        }
        """
    ):
        i += 1
        assert result == {"data": {"aSearch": [f"Search #{i}"]}}

    assert i == 5


@pytest.mark.asyncio
async def test_subscribe_custom_search(ttftt_engine):
    i = 0
    async for result in ttftt_engine.subscribe(
        """
        subscription {
          customSearch(query: "A query")
        }
        """
    ):
        i += 1
        assert result == {"data": {"customSearch": [f"Search #{i} #c"]}}

    assert i == 5


@pytest.mark.asyncio
async def test_subscribe_custom_search_aliases(ttftt_engine):
    i = 0
    async for result in ttftt_engine.subscribe(
        """
        subscription {
          aSearch: customSearch(query: "A query")
        }
        """
    ):
        i += 1
        assert result == {"data": {"aSearch": [f"Search #{i} #c"]}}

    assert i == 5

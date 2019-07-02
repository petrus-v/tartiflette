import pytest

from tests.functional.reusable.pets.storage import find_object


async def resolve_query_version(parent_result, args, ctx, info):
    return "v0.1.0"


async def resolve_query_service_status(parent_result, args, ctx, info):
    return "UP"


async def resolve_query_human(parent_result, args, ctx, info):
    return find_object("Human", args["id"])


async def resolve_query_pet(parent_result, args, ctx, info):
    return find_object("Pet", args["id"])


async def resolve_friends(parent_result, args, ctx, info):
    friend_ids = parent_result.get("friend_ids")
    if friend_ids is None:
        return None

    friends = []
    for friend_type_id in friend_ids:
        friend_type, friend_id = friend_type_id.split(".")
        friends.append(find_object(friend_type, friend_id))
    return friends


@pytest.mark.asyncio
@pytest.mark.ttftt_engine(
    name="pets",
    resolvers={
        "MyQuery.version": resolve_query_version,
        "MyQuery.serviceStatus": resolve_query_service_status,
        "MyQuery.human": resolve_query_human,
        "Human.friends": resolve_friends,
        "MyQuery.pet": resolve_query_pet,
        "Cat.friends": resolve_friends,
        "Dog.friends": resolve_friends,
    },
)
@pytest.mark.parametrize(
    "query,variables,expected",
    [
        (
            """
            {
              __typename
              version
            }
            """,
            None,
            {"data": {"__typename": "MyQuery", "version": "v0.1.0"}},
        ),
        (
            """
            {
              __typename
              serviceStatus
            }
            """,
            None,
            {"data": {"__typename": "MyQuery", "serviceStatus": "UP"}},
        ),
        (
            """
            {
              human(id: 1) {
                __typename
                id
                name
              }
            }
            """,
            None,
            {
                "data": {
                    "human": {
                        "__typename": "Human",
                        "id": 1,
                        "name": "Human 1",
                    }
                }
            },
        ),
        (
            """
            {
              human(id: 1) {
                __typename
                id
                name
                friends {
                  __typename
                  ... on Human {
                    id
                  }
                  ... on Cat {
                    id
                  }
                  ... on Dog {
                    id
                  }
                }
              }
            }
            """,
            None,
            {
                "data": {
                    "human": {
                        "__typename": "Human",
                        "id": 1,
                        "name": "Human 1",
                        "friends": [{"__typename": "Human", "id": 2}],
                    }
                }
            },
        ),
        (
            """
            {
              human(id: 999) {
                __typename
                id
                name
                friends {
                  __typename
                  ... on Human {
                    id
                  }
                  ... on Cat {
                    id
                  }
                  ... on Dog {
                    id
                  }
                }
              }
            }
            """,
            None,
            {
                "data": {"human": None},
                "errors": [
                    {
                        "message": "Object < Human.999 > doesn't exists.",
                        "path": ["human"],
                        "locations": [{"line": 3, "column": 15}],
                        "extensions": {"kind": "Human", "id": 999},
                    }
                ],
            },
        ),
        (
            """
            {
              pet(id: 1) {
                __typename
                id
                name
                friends {
                  __typename
                  ... on Human {
                    id
                  }
                  ... on Cat {
                    id
                  }
                  ... on Dog {
                    id
                  }
                }
              }
            }
            """,
            None,
            {
                "data": {
                    "pet": {
                        "__typename": "Dog",
                        "id": 1,
                        "name": "Dog 1",
                        "friends": None,
                    }
                },
                "errors": [
                    {
                        "message": "Runtime Object type < Human > is not a possible type for < Pet >.",
                        "path": ["pet", "friends", 1],
                        "locations": [{"line": 7, "column": 17}],
                    }
                ],
            },
        ),
        (
            """
            {
              pet(id: 2) {
                __typename
                id
                name
                friends {
                  __typename
                  ... on Human {
                    id
                  }
                  ... on Cat {
                    id
                  }
                  ... on Dog {
                    id
                  }
                }
              }
            }
            """,
            None,
            {
                "data": {
                    "pet": {
                        "__typename": "Cat",
                        "id": 2,
                        "name": "Cat 2",
                        "friends": [
                            {"__typename": "Dog", "id": 1},
                            {"__typename": "Cat", "id": 3},
                            {"__typename": "Dog", "id": 5},
                        ],
                    }
                }
            },
        ),
        (
            """
            {
              human(id: 999) {
                __typename
                id
                name
                friends {
                  __typename
                  ... on Human {
                    id
                  }
                  ... on Cat {
                    id
                  }
                  ... on Dog {
                    id
                  }
                }
              }
            }
            """,
            None,
            {
                "data": {"human": None},
                "errors": [
                    {
                        "message": "Object < Human.999 > doesn't exists.",
                        "path": ["human"],
                        "locations": [{"line": 3, "column": 15}],
                        "extensions": {"kind": "Human", "id": 999},
                    }
                ],
            },
        ),
    ],
)
async def test_pets(engine, query, variables, expected):
    assert await engine.execute(query, variables=variables) == expected

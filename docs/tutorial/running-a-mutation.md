---
id: running-a-mutation
title: Running a Mutation
sidebar_label: 8. Running a Mutation
---

We are going to use what [we developed in the previous step](/docs/tutorial/write-your-mutation-resolvers).

Do not forget to use the embedded GraphiQL client, available at this address [http://localhost:8080/graphiql](http://localhost:8080/graphiql) when your server is running.

## Update the name and cooking time

Copy/paste this GraphQL Query to your GraphiQL instance and execute it.

```graphql
mutation {
    updateRecipe(input: {
        id: 1,
        name: "The best Tartiflette by Eric Guelpa",
        cookingTime: 12
    }) {
        id
        name
        cookingTime
    }
}
```

![Update recipe](/docs/assets/update-recipe.png)

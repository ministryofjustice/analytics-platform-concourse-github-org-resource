
def repos(org, after="null"):
  return """
{
  organization(login: "%(org)s") {
    name
    repositories(first: 100, after: %(after)s) {
      totalCount,
      pageInfo {
        hasNextPage,
        endCursor
      },
      totalDiskUsage
      edges {
        cursor,
        node {
          name,
          pushedAt,
          deploy: object(expression: "master:deploy.json") {
            ... on Blob {
              body: text
            }
          }
        }
      }
    }
  }
}
""" % {'org': org, 'after': after}

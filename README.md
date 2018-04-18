# Github Organization Resource

Provides a Concourse resource for Github Organizations. Used to create
pipelines for org repos when deploying a webapp on the Analytical Platform

## Resource configuration

These parameters go into the `source` fields of the resource type. Bold items are required:

| Parameter | Description |
| --------- | ----------- |
| **`access_token`** | Github access token |
| **`name`** | Name of the Github organization |
| **`concourse_url`** | Base URL of the Concourse API, eg: `https://concourse.example.com` |
| **`username`** | Concourse basic auth username |
| **`password`** | Concourse basic auth password |
| **`team_name`** | Concourse team name |
| **`cookie-secret`** | Secret used to encrypt deployed webapp session cookies |
| **`cluster-ca`** | Base64 encoded PEM |
| **`token`** | Bearer token for Kubernetes |
| `skip_ssl_verification` | Whether curl should verify SSL certificates.  (Default `false`) |

# Behaviour

### `check`: Fetch Organization versions

A version corresponds to the timestamp of the last push to any of the org's
repositories.

### `in`: Fetch Organization

Retrieves the
[Organization JSON object](https://developer.github.com/v3/orgs/#get-an-organization)
into the `org` file and a list of
[repositories](https://developer.github.com/v3/repos/#get) in the `repos` file.

### `out`: Create pipelines for any Org repos that want one

Creates pipelines for any repo for which their does not already exist a pipeline
with the same name, and which contains a `Jenkinsfile` (for now).

## Installation

This resource is not included with Concourse CI. You must integrate this resource in the `resource_types` section of your pipeline.

```yaml
resource_types:
- name: github-org
  type: docker-image
  source:
    repository: quay.io.mojanalytics/github-org-resource
    tag: v0.1.3

resources:
- name: moj-analytical-services
  type: github-org
  source:
    name: moj-analytical-services
    access_token: ((github-access-token))
    concourse_url: ((concourse-url))
    username: ((concourse-username))
    password: ((concourse-password))
    team_name: ((concourse-team-name))
    cookie-secret: ((cookie-secret))
    cluster-ca: ((cluster-ca))
    token: ((token))

jobs:
- name: deploy
  plan:
  - get: moj-analytical-services
    trigger: true
```

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Submit a pull request.

## License

[MIT Licence (MIT)](LICENCE)

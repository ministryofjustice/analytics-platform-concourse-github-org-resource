[![Docker Repository on Quay](https://quay.io/repository/mojanalytics/github-org-resource/status "Docker Repository on Quay")](https://quay.io/repository/mojanalytics/github-org-resource)

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

## Release process
Change this resource is not enough to release it.
A new release tag needs to be created and Concourse
needs to be instructed to use it.

Here the steps:

1. Create a [GitHub release](https://github.com/ministryofjustice/analytics-platform-concourse-github-org-resource/releases)
2. Update the config (`concourse-org-pipeline.yaml`)
to use this new version ([example PR here](https://github.com/ministryofjustice/analytics-platform-config/pull/209/files))
3. Upgrade the helm release for the `concourse-org-pipeline`
helm chart (see ["Installing the Chart" section of README](https://github.com/ministryofjustice/analytics-platform-helm-charts/blob/master/charts/concourse-org-pipeline/README.md#installing-the-chart))

Once this above is done, newly created pipelines will use
the new version of the pipeline templates.

**NOTE**: Existing pipelines are not affected.
Generally manually delete a concourse pipeline (using
`fly destroy-pipeline`) is safe as Concourse will
automatically re-create a pipeline, and use the
latest stable version of it.

If the pipeline change is just in one of the custom
resource types' version (e.g. `ecr-repo`, `pull-request`,
`auth0-client`, `helm`, `kubernetes`, etc...) there is
now a way to set the version of a resource on all
existing pipelines:

Here an example of how to invoke this script:

```
$ ./update-pipelines-resource-types.py --help
Usage: update-pipelines-resource-types.py [OPTIONS]

Options:
  -b, --fly-binary-path TEXT      path to the fly binary (the Concourse cli)
  -c, --concourse-url TEXT        URL of Concourse
  -t, --fly-target TEXT           Concourse's fly target name
  -n, --concourse-team-name TEXT  Concourse team where the pipelines to update
                                  are

  -r, --resource-name TEXT        Name of the custom resource to update. Note
                                  this is the name used in the pipelines (e.g.
                                  'auth0-client')  [required]

  -v, --resource-tag TEXT         New version/tag of the resource  [required]
  -d, --dry-run                   When true, will not update the upstream
                                  Concourse pipeline

  -i, --interactive               Run fly set-pipeline interactively
  --help                          Show this message and exit.
```

Let's say for example that you want to update all the
pipelines to use [`concourse-auth0-resource` `v2.0.2`](https://github.com/ministryofjustice/analytics-platform-concourse-auth0-client-resource/releases/tag/v2.0.2).

First you need to find out how this resource is called
in the pipeline, in this case if you check the `webapp`
pipeline definition, in the `resource_types` section
you'll see that this resource is instanciated with the
name `auth0-client`, this will be the value you'll pass
for the `resource-name` argument of the script.

This is the command you'd invoke (remove `--dry-run` when
you want the script to update the upstream Concourse
pipelines):

```
$ ./update-pipelines-resource-types.py --resource-name=auth0-client --resource-tag=v2.0.2 --dry-run
Fly binary path [/usr/local/bin/fly]:
Concourse url [https://concourse.services.dev.mojanalytics.xyz]:
Fly target [dev-main]:
Concourse team name [main]:
logging in to team 'main'

1: ap-main
2: Basic Auth
choose an auth method: 1

navigate to the following URL in your browser:

    https://concourse.services.dev.mojanalytics.xyz/auth/oauth?team_name=main&fly_local_port=59103

or enter token manually: target saved
  [####--------------------------------]   12%  00:01:27
```

**NOTE**: script requires Concourse's command line tool
`fly`. Also be sure you install its dependency by
running `pip install -r requirements.dev.txt` to be sure
its Python dependencies are satisfied.


## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Submit a pull request.

## License

[MIT Licence (MIT)](LICENCE)

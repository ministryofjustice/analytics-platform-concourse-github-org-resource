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
Changing this resource is not enough to release it.
A new release tag needs to be created and Concourse
needs to be instructed to use it.

Here are the steps:

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

Alternatively you can edit the pipelines in-place using update-pipelines.py - see next section

## update-pipelines.py

This is a script to make updates to all concourse pipelines, editing them in-place, using fly.

### Usage

Install python dependencies:

```sh
python3 -m venv venv
venv/bin/pip install -r requirements.dev.txt
```

Install fly (Concourse's command-line tool) - see https://github.com/ministryofjustice/analytics-platform/wiki/Concourse#download 

Login to fly (needs re-doing every 24h), choosing a particular environment:

```sh
fly --target mojap-dev login --team-name main --concourse-url https://concourse.services.dev.mojanalytics.xyz/
fly --target mojap-alpha login --team-name main --concourse-url https://concourse.services.alpha.mojanalytics.xyz/
```

Run the update script. Specifying `--fly-target` which is the target you logged into e.g.:

```sh
venv/bin/python update-pipelines.py --fly-target mojap-dev <other-option>
```

You need to add another option to specify the nature of the update to each pipeline. This could be `--update-resource` to update the resource version, `--update-helm-stable-repo` to update the helm stable repo, or any other update option that you choose to add to the script.

### --update-resource

If the pipeline change is just in one of the custom
resource types' version (e.g. `ecr-repo`, `pull-request`,
`auth0-client`, `helm`, `kubernetes`, etc...) you can set the new version of
the resource using `--update-resource`

Let's say for example that you want to update all the
pipelines to use [`concourse-auth0-resource` `v2.0.2`](https://github.com/ministryofjustice/analytics-platform-concourse-auth0-client-resource/releases/tag/v2.0.2).

First you need to find out what this resource is called
in the pipeline, in this case if you check the `webapp`
pipeline definition, in the `resource_types` section
you'll see that this resource is instantiated with the
name `auth0-client`, this will be the value you'll pass
for the `resource-name` argument of the script.

This is the command you'd invoke (remove `--dry-run` when
you want the script to update the upstream Concourse
pipelines):

```sh
venv/bin/python/update-pipelines.py --update-resource 'auth0-client=v2.0.2' --dry-run
[####--------------------------------]   12%  00:01:27
```

## Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Submit a pull request.

## License

[MIT Licence (MIT)](LICENCE)

#! /usr/bin/env python3

import click

import json
import os
import subprocess
import tempfile


DEFAULT_FLY_BIN = "/usr/local/bin/fly"
DEFAULT_CONCOURSE_URL = "https://concourse.services.dev.mojanalytics.xyz"
DEFAULT_TEAM_NAME = "main"
DEFAULT_TARGET = "update-pipelines-script"


TMP_DIR = os.path.join(tempfile.gettempdir(), "pipelines")
os.makedirs(TMP_DIR, exist_ok=True)


def concourse_login():
    """fly login"""

    subprocess.run([
        DEFAULT_FLY_BIN, "login",
        "-c", DEFAULT_CONCOURSE_URL,
        "-t", DEFAULT_TARGET,
        "-n", DEFAULT_TEAM_NAME,
    ])


def get_pipelines():
    """fly pipelines"""

    pipeline_names = []

    # fly pipelines
    c1 = subprocess.Popen([
            DEFAULT_FLY_BIN,
            "-t", DEFAULT_TARGET,
            "pipelines"
        ], stdout=subprocess.PIPE)
    output = c1.communicate()[0].decode("utf-8")

    # extract pipeline names from first column
    lines = output.split('\n')
    for line in lines:
        # ignore other pipeline information such as
        # whether they're paused or public
        pipeline_name = line.split(' ')[0]
        if pipeline_name:
            pipeline_names.append(pipeline_name)

    return pipeline_names


def get_pipeline(name):
    """fly get-pipeline"""

    cmd = subprocess.run([
        DEFAULT_FLY_BIN, "get-pipeline",
        "-t", DEFAULT_TARGET,
        "-p", name,
        "--json"
    ], capture_output=True)

    return json.loads(cmd.stdout)


def set_pipeline(name, config_path):
    """fly set-pipeline"""

    cmd = subprocess.run([
        DEFAULT_FLY_BIN, "set-pipeline",
        "-t", DEFAULT_TARGET,
        "-p", name,
        "-c", config_path,
    ])


def update_resource_tag(pipeline, resource_name, new_tag):
    for t in pipeline["resource_types"]:
        if t["name"] == resource_name:
            t["source"]["tag"] = new_tag
            break


if __name__ == "__main__":
    concourse_login()
    pipelines = get_pipelines()

    for pipeline_name in pipelines:
        click.echo(f"updating pipeline '{pipeline_name}'...")
        pipeline = get_pipeline(pipeline_name)

        update_resource_tag(pipeline, "auth0-client", "v2.0.2")

        pipeline_path = os.path.join(TMP_DIR, f"{pipeline_name}_UPDATED.json")
        with open(pipeline_path, "w") as file:
            json.dump(pipeline, file)

        set_pipeline(pipeline_name, pipeline_path)

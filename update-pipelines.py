#! /usr/bin/env python3

import click

import json
import os
import subprocess
import tempfile
import copy
from collections import Counter


TMP_DIR = os.path.join(tempfile.gettempdir(), "pipelines")
os.makedirs(TMP_DIR, exist_ok=True)


class Concourse():

    def __init__(self, fly_bin, fly_target):
        self.fly_bin = fly_bin
        self.fly_target = fly_target

    def get_pipelines(self):
        """fly pipelines"""

        pipeline_names = []

        # fly pipelines
        c1 = subprocess.Popen([
                self.fly_bin,
                "-t", self.fly_target,
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


    def get_pipeline(self, name):
        """fly get-pipeline"""

        cmd = subprocess.run([
            self.fly_bin, "get-pipeline",
            "-t", self.fly_target,
            "-p", name,
            "--json"
        ], capture_output=True)

        return json.loads(cmd.stdout)


    def set_pipeline(self, name, config_path, non_interactive=True):
        """fly set-pipeline"""

        set_pipeline_args = [
            self.fly_bin, "set-pipeline",
            "-t", self.fly_target,
            "-p", name,
            "-c", config_path,
        ]

        if non_interactive:
            set_pipeline_args.append("--non-interactive")

        print(set_pipeline_args)
        subprocess.run(set_pipeline_args)


def update_resource_tag(pipeline, resource_name, new_tag):
    if not pipeline.get("resource_types"):
        return

    for t in pipeline.get("resource_types", []):
        if t["name"] == resource_name:
            t["source"]["tag"] = new_tag
            break


def update_helm_stable_repo_(pipeline, stable_repo):
    if not pipeline.get("resources"):
        return

    for t in pipeline.get("resources", []):
        if t["name"] == "webapp-helm-release":
            t["source"]["stable_repo"] = stable_repo
            break

@click.command()
@click.option("-b", "--fly-binary-path", default="/usr/local/bin/fly", help="path to the fly binary (the Concourse cli)")
@click.option("-t", "--fly-target", required=True, default="mojap-dev", help="Concourse's fly target name", prompt=True)
@click.option("--update-resource", help="To update a custom resource, provide the name of the custom resource to update, as used in the pipelines and the new version/tag of the resource (e.g. 'auth0-client=1.4')")
@click.option("--update-helm-stable-repo", help="To update the helm stable repo, provide the name of the repo")
@click.option("-d", "--dry-run", is_flag=True, help="When true, will not write the changes to the upstream Concourse pipeline")
@click.option("-i", "--interactive", is_flag=True, default=False, help="Run fly set-pipeline interactively")
def main(fly_binary_path, fly_target, update_resource, update_helm_stable_repo, dry_run, interactive):
    non_interactive = not interactive

    concourse = Concourse(
        fly_bin=fly_binary_path,
        fly_target=fly_target,
    )

    pipelines = sorted(concourse.get_pipelines())

    outcomes = Counter()
    def print_and_save_outcome(outcome):
        print(outcome)
        outcomes.update((outcome,))

    with click.progressbar(pipelines) as pbar:
        for pipeline_name in pbar:
            print("\n\nPipeline: {} ".format(pipeline_name))

            pipeline = concourse.get_pipeline(pipeline_name)
            original_pipeline = copy.copy(pipeline)

            # Edit the pipeline
            if update_resource:
                resource_name, resource_tag = update_resource.split('=')
                update_resource_tag(pipeline, resource_name, resource_tag)
            if update_helm_stable_repo:
                update_helm_stable_repo_(pipeline, update_helm_stable_repo)

            if pipeline == original_pipeline:
                print_and_save_outcome('no changes needed')
                continue

            pipeline_path = os.path.join(TMP_DIR, f"{pipeline_name}_UPDATED.json")
            with open(pipeline_path, "w") as file:
                json.dump(pipeline, file)

            if not dry_run:
                concourse.set_pipeline(
                    pipeline_name,
                    pipeline_path,
                    non_interactive=non_interactive,
                )
                print_and_save_outcome('pipeline applied')
            else:
                print_and_save_outcome('skipped apply (dry-run mode)')

        print('\n\nSummary of actions:')
        print(outcomes)


if __name__ == "__main__":
    main()

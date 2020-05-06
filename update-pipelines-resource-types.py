#! /usr/bin/env python3

import click

import json
import os
import subprocess
import tempfile


TMP_DIR = os.path.join(tempfile.gettempdir(), "pipelines")
os.makedirs(TMP_DIR, exist_ok=True)


class Concourse():

    def __init__(self, fly_bin, fly_target, concourse_url, team_name):
        self.fly_bin = fly_bin
        self.fly_target = fly_target
        self.concourse_url = concourse_url
        self.team_name = team_name

    def login(self):
        """fly login"""

        subprocess.run([
            self.fly_bin, "login",
            "-c", self.concourse_url,
            "-t", self.fly_target,
            "-n", self.team_name,
        ])

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

        subprocess.run(set_pipeline_args)


def update_resource_tag(pipeline, resource_name, new_tag):
    for t in pipeline.get("resource_types", []):
        if t["name"] == resource_name:
            t["source"]["tag"] = new_tag
            break


@click.command()
@click.option("-b", "--fly-binary-path", default="/usr/local/bin/fly", help="path to the fly binary (the Concourse cli)", prompt=True)
@click.option("-c", "--concourse-url", default="https://concourse.services.dev.mojanalytics.xyz", help="URL of Concourse", prompt=True)
@click.option("-t", "--fly-target", default="dev-main", help="Concourse's fly target name", prompt=True)
@click.option("-n", "--concourse-team-name", default="main", help="Concourse team where the pipelines to update are", prompt=True)
@click.option("-r", "--resource-name", required=True, help="Name of the custom resource to update. Note this is the name used in the pipelines (e.g. 'auth0-client')", prompt=True)
@click.option("-v", "--resource-tag", required=True, help="New version/tag of the resource", prompt=True)
@click.option("-d", "--dry-run", is_flag=True, help="When true, will not update the upstream Concourse pipeline")
@click.option("-i", "--interactive", is_flag=True, default=False, help="Run fly set-pipeline interactively")
def main(fly_binary_path, concourse_url, fly_target, concourse_team_name, resource_name, resource_tag, dry_run, interactive):
    non_interactive = not interactive

    concourse = Concourse(
        fly_bin=fly_binary_path,
        fly_target=fly_target,
        concourse_url=concourse_url,
        team_name=concourse_team_name,
    )

    concourse.login()
    pipelines = concourse.get_pipelines()

    with click.progressbar(pipelines) as pbar:
        for pipeline_name in pbar:
            pipeline = concourse.get_pipeline(pipeline_name)

            update_resource_tag(pipeline, resource_name, resource_tag)

            pipeline_path = os.path.join(TMP_DIR, f"{pipeline_name}_UPDATED.json")
            with open(pipeline_path, "w") as file:
                json.dump(pipeline, file)

            if not dry_run:
                concourse.set_pipeline(
                    pipeline_name,
                    pipeline_path,
                    non_interactive=non_interactive,
                )


if __name__ == "__main__":
    main()

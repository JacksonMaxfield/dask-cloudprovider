#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
import uuid
from pathlib import Path
from typing import Dict, Optional, Union

import google.oauth2
import googleapiclient.discovery
from gcloud.client import Client
from google.oauth2.service_account import Credentials

#######################################################################################

log = logging.getLogger(__name__)

#######################################################################################

# Must install google cloud sdk and sign in before hand
# https://cloud.google.com/sdk/docs/quickstarts

# Also create a service account json and set the environment variable
# GOOGLE_APPLICATION_CREDENTIALS to it's path
# https://cloud.google.com/docs/authentication/getting-started

# To spawn with docker hub image the format needs to be docker.io/{user}/{image}:{tag}
# https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/compute/api/create_instance.py


def create_compute_instance_request(
    name: str,
    machine_type: str,
    source_image: str = "docker.io/daskdev/dask:latest",
    startup_script: str = "dask-scheduler",
    instance_icon: str = "https://dask.org/_images/dask_horizontal_white_no_pad.svg",
    instance_description: str = "Dask Scheduler or Worker",
) -> Dict:
    return {
        "name": name,
        "machineType": machine_type,
        # Specify the boot disk and the image to use as a source.
        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {"sourceImage": source_image,},
            }
        ],
        # Specify a network interface with NAT to access the public
        # internet.
        "networkInterfaces": [
            {
                "network": "global/networks/default",
                "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
            }
        ],
        # Allow the instance to access cloud storage and logging.
        "serviceAccounts": [
            {
                "email": "default",
                "scopes": [
                    "https://www.googleapis.com/auth/devstorage.read_write",
                    "https://www.googleapis.com/auth/logging.write",
                ],
            }
        ],
        # Metadata is readable from the instance and allows you to
        # pass configuration from deployment scripts to instances.
        "metadata": {
            "items": [
                {
                    # Startup script is automatically executed by the
                    # instance upon startup.
                    "key": "startup-script",
                    "value": startup_script,
                },
                {"key": "url", "value": instance_icon},
                {"key": "text", "value": instance_description},
            ],
        },
    }


def create_instance(
    compute,
    project: str,
    zone: str = "us-west1-a",
    name: Optional[str] = None,
    machine_type: str = "n1-standard-1",
    source_image: str = "docker.io/daskdev/dask:latest",
    startup_script: str = "dask-scheduler",
    instance_icon: str = "https://dask.org/_images/dask_horizontal_white_no_pad.svg",
    instance_description: str = "Dask Scheduler or Worker",
):
    # Generate name
    if name is None:
        name = f"dask-{uuid.uuid4()}"

    # Configure the machine type
    machine_type = (
        f"https://compute.googleapis.com/compute/v1/projects/"
        f"{project}"
        f"/zones/"
        f"{zone}"
        f"/machineTypes/"
        f"{machine_type}"
    )

    # Build config
    config = create_compute_instance_request(
        name=name,
        machine_type=machine_type,
        source_image=source_image,
        startup_script=startup_script,
        instance_icon=instance_icon,
        instance_description=instance_description,
    )

    # Run create
    return compute.instances().insert(project=project, zone=zone, body=config).execute()


def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result["items"] if "items" in result else None


def delete_instance(compute, project, zone, name):
    return (
        compute.instances().delete(project=project, zone=zone, instance=name).execute()
    )


def wait_for_operation(compute, project, zone, operation):
    print("Waiting for operation to finish...")
    while True:
        result = (
            compute.zoneOperations()
            .get(project=project, zone=zone, operation=operation)
            .execute()
        )

        if result["status"] == "DONE":
            print("done.")
            if "error" in result:
                raise Exception(result["error"])
            return result

        time.sleep(1)


def get_credentials(
    credentials_path: Optional[Union[str, Path]] = None
) -> Credentials:
    # Provided credentials path
    if credentials_path is not None:
        # Get absolute path and check exists
        credentials_path = Path(credentials_path).expanduser().resolve(strict=True)

        return Credentials.from_service_account_file(credentials_path)

    # Attempt to get default credentials
    return Client().connection.credentials


def generate_cluster(
    project: str,
    zone: str = "us-west1-a",
    credentials_path: Optional[Union[str, Path]] = None,
    scheduler_machine_type: str = "e2-standard-2",
    worker_machine_type: str = "n1-standard-1",
    worker_accelerator_type: Optional[str] = None,
    worker_accelerator_count: Optional[int] = None,
    source_image: str = "https://docker.io/daskdev/dask:latest",
    scheduler_instance_description: str = "Dask Scheduler",
    worker_instance_description: str = "Dask Worker",
):
    # Get credentials object
    creds = get_credentials(credentials_path)

    # Generate compute object
    compute = googleapiclient.discovery.build(
        "compute",
        "v1",
        credentials=creds,
        cache_discovery=False,
    )

    # Create scheduler
    scheduler_instance = create_instance(
        compute=compute,
        project=project,
        zone=zone,
        machine_type=scheduler_machine_type,
        source_image=source_image,
        instance_description=scheduler_instance_description,
    )
    log.info("Creating dask-scheduler instance.")

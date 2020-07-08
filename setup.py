#!/usr/bin/env python

from os.path import exists

from setuptools import find_packages, setup

import versioneer

requirements = [
    "aiobotocore>=0.10.2",
    "dask>=2.2.0",
    "distributed>=2.3.1",
    "azureml-sdk>=1.0.83",
]

gcp_requirements = [
    "google-api-python-client>=1.9.3",
    "google-auth-oauthlib>=0.4.1",
]

extra_requirements = {
    "gcp": gcp_requirements,
    "all": [
        *requirements,
        *gcp_requirements,
    ]
}

setup(
    name="dask-cloudprovider",
    cmdclass=versioneer.get_cmdclass(),
    version=versioneer.get_version(),
    description="Native Cloud Provider integration for Dask",
    url="https://github.com/dask/dask-cloudprovider",
    keywords="dask,cloud,distributed",
    license="BSD",
    packages=find_packages(),
    include_package_data=True,
    long_description=(open("README.md").read() if exists("README.md") else ""),
    zip_safe=False,
    install_requires=requirements,
    extras_require=extra_requirements,
    entry_points="""
    [console_scripts]
    dask-ecs=dask_cloudprovider.cli.ecs:go
    """,
    python_requires=">=3.5",
)

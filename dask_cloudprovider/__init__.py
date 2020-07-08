from . import config
from ._version import get_versions
from .providers.aws.ecs import ECSCluster, FargateCluster
from .providers.azure.azureml import AzureMLCluster
from .providers.gcp.compute import generate_cluster

__all__ = ["ECSCluster", "FargateCluster", "AzureMLCluster"]


__version__ = get_versions()["version"]

del get_versions

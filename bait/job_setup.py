import azure.mgmt.batchai.models as models
import azure.mgmt.batchai as batchai
from azure.storage.file import FileService
from datetime import datetime
import sys
import config
import os

# =========================
# Setup credentials
# =========================
from azure.common.credentials import ServicePrincipalCredentials
import azure.mgmt.batchai as batchai
import azure.mgmt.batchai.models as models

creds = ServicePrincipalCredentials(
  client_id=config.CREDENTIALS['aad_client_id'], 
  secret=config.CREDENTIALS['aad_secret'], 
  tenant=config.CREDENTIALS['aad_tenant']
)

batchai_client = batchai.BatchAIManagementClient(
  credentials=creds, 
  subscription_id=config.ACCOUNT['subscription_id']
)

# ========================
# Run Azure Batch AI Job
# ========================
input_directories = [
  models.InputDirectory(
    id='SCRIPTS',
    path='$AZ_BATCHAI_MOUNT_ROOT/{0}/{1}'.format(
      config.CLUSTER['file_share_mnt_path'], 
      config.AFS_PATHS['script_directory']
    )
  ),
  models.InputDirectory(
    id='MODELS',
    path='$AZ_BATCHAI_MOUNT_ROOT/{0}/{1}'.format(
      config.CLUSTER['file_share_mnt_path'], 
      os.path.join(config.AFS_PATHS['model_directory'], config.LOCAL['model_directory'])
    )
  )
]

output_directories = [
  models.OutputDirectory(
    id='RESULT',
    path_prefix='$AZ_BATCHAI_MOUNT_ROOT/{0}'.format(config.CLUSTER['file_share_mnt_path']),
    path_suffix='results')]

std_output_path_prefix = '$AZ_BATCHAI_MOUNT_ROOT/{0}'.format(config.CLUSTER['file_share_mnt_path'])

cluster = batchai_client.clusters.get(config.ACCOUNT['resource_group_name'], config.CLUSTER['name'])
job_name = datetime.utcnow().strftime("{0}_%m_%d_%Y_%H%M%S".format(config.JOB['name_prefix']))

parameters = models.JobCreateParameters(
  experiment_name=job_name,
  location=config.ACCOUNT['region'],
  cluster=models.ResourceId(id=cluster.id),
  node_count=config.JOB['node_count'],
  input_directories=input_directories,
  output_directories=output_directories,
  std_out_err_path_prefix=std_output_path_prefix,
  container_settings=models.ContainerSettings(
    image_source_registry=models.ImageSourceRegistry(
      image='tensorflow/tensorflow:1.8.0-gpu-py3'
    )
  ),
  custom_toolkit_settings=models.CustomToolkitSettings(
    command_line="python $AZ_BATCHAI_INPUT_SCRIPTS/conv_copy.py"
  )
)

job = batchai_client.jobs.create(
  resource_group_name=config.ACCOUNT['resource_group_name'], 
  job_name=job_name, 
  parameters=parameters
).result()
print('Created Job: {}'.format(job.name))

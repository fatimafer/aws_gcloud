#!/bin/bash
source ~/miniconda3/etc/profile.d/conda.sh
conda init
conda activate aws-gcloud #Cambiar por el nombre de nuestro entorno conda
conda env config vars set AWS_CONFIG_FILE=$PWD/.aws/config AWS_SHARED_CREDENTIALS_FILE=$PWD/.aws/credentials AWS_PROFILE=default GOOGLE_APPLICATION_CREDENTIALS=$PWD/.gcloud/adc.json GCLOUD_PROJECT=coral-cloud-510013 #Cambiar por la id de proyecto en gcloud
conda deactivate
source ~/miniconda3/etc/profile.d/conda.sh
conda init
conda activate aws-gcloud #Cambiar por el nombre de nuestro entorno conda
python upload_delete_all.py
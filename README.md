
# GCP IAM Roles Query

This application help to query Google Cloud Platform IAM Roles and Permissions. It helps answer the question like: 

- What predefined roles are available for Vertex AI?
- What predefined roles include permission `aiplatform.endpoints.list`?

# Installation

Download the latest version from [GitHub Releases](https://github.com/kborovik/gcp-iam-roles/releases).

```shell
pipx install gcp_iam_roles-2024.11.12-py3-none-any.whl
```

# Usage

**Get CLI help:**

```shell
(0) > gcp-iam-roles
usage: gcp-iam-roles [-h] [-r ROLE] [-p PERMISSION] [--status] [--bash-completion] [--init-db] [--clear-db]

Search Google Cloud IAM roles and permissions

options:
  -h, --help            show this help message and exit
  -r ROLE, --role ROLE  Search for Roles
  -p PERMISSION, --permission PERMISSION
                        Search for Permissions
  --status              Show Roles and Permissions count
  --bash-completion     Saved bash completion in /home/kb/.local/share/bash-completion/completions
  --init-db             Populate database with Google Cloud IAM roles
  --clear-db            Drop database tables
```

**What predefined roles are available for Vertex AI?**

```shell
(0) > gcp-iam-roles --role vertex
+--------------------------------------------------+-----------------------------------------------+-------+
| role                                             | title                                         | stage |
+--------------------------------------------------+-----------------------------------------------+-------+
| roles/aiplatform.admin                           | Vertex AI Administrator                       | GA    |
| roles/aiplatform.batchPredictionServiceAgent     | Vertex AI Batch Prediction Service Agent      | GA    |
| roles/aiplatform.colabServiceAgent               | Vertex AI Colab Service Agent                 | GA    |
| roles/aiplatform.customCodeServiceAgent          | Vertex AI Custom Code Service Agent           | GA    |
| roles/aiplatform.entityTypeOwner                 | Vertex AI Feature Store EntityType owner      | GA    |
| roles/aiplatform.expressAdmin                    | Vertex AI Platform Express Admin              | BETA  |
| roles/aiplatform.expressUser                     | Vertex AI Platform Express User               | BETA  |
| roles/aiplatform.extensionCustomCodeServiceAgent | Vertex AI Extension Custom Code Service Agent | GA    |
| roles/aiplatform.extensionServiceAgent           | Vertex AI Extension Service Agent             | GA    |
| roles/aiplatform.featurestoreAdmin               | Vertex AI Feature Store Admin                 | GA    |
| roles/aiplatform.featurestoreDataViewer          | Vertex AI Feature Store Data Viewer           | GA    |
| roles/aiplatform.featurestoreDataWriter          | Vertex AI Feature Store Data Writer           | GA    |
| roles/aiplatform.featurestoreInstanceCreator     | Vertex AI Feature Store Instance Creator      | GA    |
| roles/aiplatform.featurestoreResourceViewer      | Vertex AI Feature Store Resource Viewer       | GA    |
| roles/aiplatform.featurestoreUser                | Vertex AI Feature Store User                  | BETA  |
| roles/aiplatform.migrator                        | Vertex AI Migration Service User              | GA    |
| roles/aiplatform.modelMonitoringServiceAgent     | Vertex AI Model Monitoring Service Agent      | GA    |
| roles/aiplatform.notebookServiceAgent            | Vertex AI Notebook Service Agent              | GA    |
| roles/aiplatform.ragServiceAgent                 | Vertex AI RAG Data Service Agent              | GA    |
| roles/aiplatform.rapidevalServiceAgent           | Vertex AI Rapid Eval Service Agent            | GA    |
| roles/aiplatform.reasoningEngineServiceAgent     | Vertex AI Reasoning Engine Service Agent      | GA    |
| roles/aiplatform.serviceAgent                    | Vertex AI Service Agent                       | GA    |
| roles/aiplatform.tensorboardWebAppUser           | Vertex AI Tensorboard Web App User            | BETA  |
| roles/aiplatform.tuningServiceAgent              | Vertex AI Tuning Service Agent                | GA    |
| roles/aiplatform.user                            | Vertex AI User                                | GA    |
| roles/aiplatform.viewer                          | Vertex AI Viewer                              | GA    |
+--------------------------------------------------+-----------------------------------------------+-------+
```

**What predefined roles include permission `aiplatform.endpoints.list`**

```shell
(0) > gcp-iam-roles --permission aiplatform.endpoints.list
+----------------------------------------------+---------------------------+
| role                                         | permission                |
+----------------------------------------------+---------------------------+
| roles/aiplatform.admin                       | aiplatform.endpoints.list |
| roles/aiplatform.customCodeServiceAgent      | aiplatform.endpoints.list |
| roles/aiplatform.reasoningEngineServiceAgent | aiplatform.endpoints.list |
| roles/aiplatform.serviceAgent                | aiplatform.endpoints.list |
| roles/aiplatform.user                        | aiplatform.endpoints.list |
| roles/aiplatform.viewer                      | aiplatform.endpoints.list |
| roles/dlp.orgdriver                          | aiplatform.endpoints.list |
| roles/dlp.projectdriver                      | aiplatform.endpoints.list |
| roles/editor                                 | aiplatform.endpoints.list |
| roles/iam.securityAdmin                      | aiplatform.endpoints.list |
| roles/iam.securityReviewer                   | aiplatform.endpoints.list |
| roles/owner                                  | aiplatform.endpoints.list |
| roles/spanner.serviceAgent                   | aiplatform.endpoints.list |
| roles/viewer                                 | aiplatform.endpoints.list |
| roles/visualinspection.serviceAgent          | aiplatform.endpoints.list |
+----------------------------------------------+---------------------------+
```

**Populate DB with all IAM Roles and Permissions**

```shell
(0) > gcp-iam-roles --init-db 
Authenticated to Google Cloud with project ID: <project_id>
Created tables: roles, permissions
Getting Google Cloud IAM predefined roles...
```
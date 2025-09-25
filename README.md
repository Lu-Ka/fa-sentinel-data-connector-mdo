# Function App - Sentinel - Microsoft Defender for Office 365

This repository hosts an Azure Function App Python code in order to get Microsoft Defender for Office 365 alert logs when you have a Plan 1 license and send them into Microsoft Sentinel SIEM.


## Pre-requisites

> Before to deploy this script, you have to manually [enable an Office Subscription](https://learn.microsoft.com/en-us/office/office-365-management-api/office-365-management-activity-api-reference#start-a-subscription)<br>
You also need an App Registration with [right API permission on the Office 365 Management APIs](https://learn.microsoft.com/en-us/office/office-365-management-api/get-started-with-office-365-management-apis#specify-the-permissions-your-app-requires-to-access-the-office-365-management-apis).


  * A Python 3.12 [Azure Function App](https://docs.microsoft.com/en-us/azure/azure-functions/functions-overview) 
  * A [Log Analytics Workspace](https://docs.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-overview) with Sentinel enabled on it.
  * A [custom Log Analytics table](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/create-custom-table) to store MDO alert logs.
  * A [DCE](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/data-collection-endpoint-overview?tabs=portal) and [DCR](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/data-collection-rule-overview) to receive logs from the Function App and send them into Sentinel.
  * A [Storage Account](https://learn.microsoft.com/en-us/azure/storage/common/storage-account-overview)
  * A [Key Vault](https://learn.microsoft.com/en-us/azure/key-vault/general/overview) to store App Registration secrets.
  * Function [Managed Identity](https://docs.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/overview)
    with at least `Storage Blob Data Owner` right on the Storage Account for storing the state file, `Reader` on the 
KeyVault to retrieve secrets, `Monitoring Metrics Publisher` on the DCR.

### Variables

  * **DCE_URL** (required): The ingestion URL of the Data Collection Endpoint. 
  * **DCR_ID** (required): The Data Collection Rule immutable ID.
  * **DCR_STREAM** (required): The Data Collection Rule stream.
  * **KV_URL** (required): The Key Vault URL.
  * **KV_SECRET_SP_CLIENT_ID** (required): The Key Vault Secret name where the App Registration Client ID is stored.  
  * **KV_SECRET_SP_CLIENT_SECRET** (required): The Key Vault Secret name where the App Registration Client Secret is stored.
  * **KV_SECRET_SP_TENANT_ID** (required): The Key Vault Secret name where the App Registration Tenant ID is stored.
  * **STORAGE_BLOB_FILE** (required): The file used embedding the date used for querying the Office API.
  * **STORAGE_CONTAINER** (required): The Storage Account container name where the file is located.
  * **STORAGE_NAME** (required): The Storage Account name.
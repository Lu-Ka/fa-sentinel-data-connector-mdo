import json
import logging
import os

import requests

import azure.functions as func

from datetime import datetime, timedelta, timezone

from lib.office import Office
from lib.key_vault import KeyVault
from lib.log_analytics import LogAnalytics
from lib.storage import Storage


# Office parameters
OFFICE_CONTENT_TYPE = "Audit.General"
OFFICE_PUBLISHER_ID = "d3fc05f9-1eb4-4a92-bd0b-220dc6614f75"
# Interval of script execution
SCRIPT_EXECUTION_INTERVAL_MINUTES = 10
# Environment variables
ENV = (
    "DCE_URL",
    "DCR_ID",
    "DCR_STREAM",
    "KV_SECRET_SP_CLIENT_ID",
    "KV_SECRET_SP_CLIENT_SECRET",
    "KV_SECRET_SP_TENANT_ID",
    "KV_URL",
    "STORAGE_BLOB_FILE",
    "STORAGE_CONTAINER",
    "STORAGE_NAME",
)


def get_microsoft_token(tenant_id, client_id, client_secret):
    auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    payload = {
        "scope": "https://manage.office.com/.default",
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }

    token_req = requests.post(auth_url, data=payload)

    if token_req.status_code != 200:
        print("Failed to obtain token from the OAuth 2.0 server :")
        print(token_req.text)
        exit(1)

    token = json.loads(token_req.text)

    return token["access_token"]


def get_query_api_date(storage):
    logging.info("Getting last query date")

    last_query_date = storage.get()
    now = datetime.now(timezone.utc).replace(tzinfo=timezone.utc)

    # Check if we have the state file with the last query date within it
    if last_query_date:
        logging.info(f"Last query date - {last_query_date}")
    else:
        last_query_date = now - timedelta(minutes=SCRIPT_EXECUTION_INTERVAL_MINUTES)
        logging.info("Last query date is not known")

    # Minus 1 minute to let API provider publish logs
    endtime = now - timedelta(minutes=1)

    logging.info(f"Getting data from {last_query_date} to {endtime}")

    # Update state file with the end time of the current query
    # This one will be the start time for the next launch
    storage.post(endtime.isoformat())

    return last_query_date, endtime.isoformat()


def check_env(env_vars):
    vars = {}

    for env in env_vars:
        env_value = os.environ.get(env)
        if not env_value:
            raise ValueError(f"Environment variable {env} not set")
        else:
            vars[env] = env_value

    return vars


app = func.FunctionApp()


@app.function_name(name="MDOAlerts")
@app.timer_trigger(
    schedule="0 */10 * * * *",
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
def MDOAlertsSentinelConnector(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info("The timer is past due!")

    utc_timestamp = datetime.now(timezone.utc).replace(tzinfo=timezone.utc).isoformat()

    logging.info(f"Python timer trigger function ran at {utc_timestamp}")
    logging.info("Starting program")

    vars = check_env(ENV)

    storage = Storage(
        vars["STORAGE_NAME"],
        vars["STORAGE_CONTAINER"],
        vars["STORAGE_BLOB_FILE"],
    )

    start_time, end_time = get_query_api_date(storage)

    kv = KeyVault(vars["KV_URL"])
    sp_client_id = kv.get_secret(vars["KV_SECRET_SP_CLIENT_ID"])
    sp_client_secret = kv.get_secret(vars["KV_SECRET_SP_CLIENT_SECRET"])
    sp_tenant_id = kv.get_secret(vars["KV_SECRET_SP_TENANT_ID"])

    token = get_microsoft_token(sp_tenant_id, sp_client_id, sp_client_secret)

    office = Office(sp_tenant_id, OFFICE_CONTENT_TYPE, OFFICE_PUBLISHER_ID, token)

    alerts = []

    for blobs in office.list_blobs(start_time, end_time):
        for blob in blobs:
            content_url = blobs["contentUri"]
            content = office.get_content(content_url)

            for event in content:
                if (
                    event["Operation"] == "AlertTriggered"
                    and event["Workload"] == "SecurityComplianceCenter"
                ):
                    alerts.append(event)

    logging.info(f"Number of alerts - {len(alerts)}")

    log_analytics = LogAnalytics(
        vars["DCE_URL"],
        vars["DCR_ID"],
        vars["DCR_STREAM"],
    )
    log_analytics.upload(alerts)

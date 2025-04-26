import marimo

__generated_with = "0.13.2"

app = marimo.App(
    width="full",
    auto_download=["ipynb", "html"],
    app_title="Cloudflare Login",
)

####################
# Helper Functions #
####################

# Help function init stubs
get_token = get_accounts = login = None


@app.cell(hide_code=True)
async def _():
    # Helper Functions
    import marimo as mo
    import js
    import requests
    import urllib

    proxy = "https://examples-api-proxy.notebooks.cloudflare.com"

    async def get_token():
        # Retrieve the token from IndexedDB
        js.eval(
            """
        async function getAuthToken() {
          const dbName = 'notebook-examples';
          const storeName = 'oauth';
          const keyName = 'auth_token';
          return new Promise((resolve, reject) => {
            const request = indexedDB.open(dbName, 1);
            request.onupgradeneeded = event => {
              const db = event.target.result;
              if (!db.objectStoreNames.contains(storeName)) {
                db.createObjectStore(storeName, { keyPath: 'id' });
              }
            };
            request.onerror = event => reject("Error opening database " + dbName + ": " + event);
            request.onsuccess = event => {
              const db = event.target.result;
              const tx = db.transaction(storeName, 'readonly');
              const store = tx.objectStore(storeName);
              const getRequest = store.get(keyName);
              getRequest.onsuccess = () => resolve(getRequest.result);
              getRequest.onerror = event => reject("Missing data "
                + dbName + ":" + storeName + ":" + keyName + ": " + event);
            };
          });
        }
        """
        )
        tokenRecord = await js.getAuthToken()
        token = tokenRecord.token if tokenRecord and tokenRecord.token else None
        return token

    async def get_accounts(token):
        # Example API request to list available Cloudflare accounts
        token = token or await get_token()
        res = requests.get(
            f"{proxy}/client/v4/accounts",
            headers={"Authorization": f"Bearer {token}"},
        ).json()
        return res.get("result", []) or []

    def login():
        # Fetch and return the login form HTML from marimo public folder
        html_path = f"{mo.notebook_location()}/public/login"
        with urllib.request.urlopen(html_path) as response:
            html = response.read().decode()
        return html

    # Start Login Form
    mo.iframe(login(), height="1px")
    return None


##################
# Notebook Cells #
##################


@app.cell()
async def _(mo):
    # 1) After login, Run ▶ this cell to get your API token and accounts
    # 2) Select a specific Cloudflare account below
    # 3) Start coding!
    token = await get_token()
    accounts = await get_accounts(token)
    radio = mo.ui.radio(options=[a["name"] for a in accounts], label="Select Account")
    return token, accounts, radio


@app.cell(hide_code=True)
def _(token, accounts, radio, mo):
    # Run ▶ this cell to select a specific Cloudflare account
    account_name = radio.value
    account_id = next((a["id"] for a in accounts if a["name"] == account_name), None)
    mo.hstack([radio, mo.md(f"**Variables**  \n**token:** {token}  \n**account_name:** {account_name or 'None'}  \n**account_id:** {account_id or 'None'}")])  # noqa: E501
    return


@app.cell
def _():
    import altair as alt
    import json
    import numpy as np
    import pandas as pd

    return alt, json, np, pd


@app.cell
def _(mo):
    mo.md(
        r"""
        # D1 API use case

        In this notebook, we will show a simple use case involving interactions with D1 associated to a
        Cloudflare account. This will involve the following:<br>
         1. listing existing D1 datasets;<br>
         2. simple query fetching rows from a D1 dataset table;<br>

        all using the Cloudflare API.

        **Prerequisites:**<br>
         - API token (see [here](https://developers.cloudflare.com/r2/api/s3/tokens/)
        for info on how to create one) with **D1 read** permission;<br>
         - at least one D1 dataset with a table.
        """
    )
    return


@app.cell
def _():
    CF_ACCOUNT_TAG = "<your-account-tag>"
    TOKEN = "<your-token>"

    HOSTNAME = "https://examples-api-proxy.notebooks.cloudflare.com"
    URL = f"{HOSTNAME}/client/v4/accounts/{CF_ACCOUNT_TAG}/d1/database"
    return CF_ACCOUNT_TAG, HOSTNAME, TOKEN, URL


@app.cell
def _(mo):
    mo.md(
        r"""
        ## List available D1 datasets

        By performing a GET request (with no payload) to the `/accounts/{account_id}/d1/database`
        [endpoint](https://developers.cloudflare.com/api/resources/d1/subresources/database/methods/list/)
        we can get the names, unique Ids as well as other info of all D1 datasets associated with a Cloudflare account.
        """
    )
    return


@app.cell
def _(TOKEN, URL, pd, requests):
    # Send GET query
    api_resp = requests.get(URL, headers={"Authorization": "Bearer {}".format(TOKEN)})

    # Results handling
    api_resp_json = api_resp.json()
    if api_resp_json["success"]:
        print("Successfully fetched D1 dataset list")
        d1_datasets = pd.DataFrame(api_resp_json["result"])
    else:
        print(
            f"Failed to fetch D1 dataset list (status code {api_resp.status_code}). Received the following errors:"
        )
        for error in api_resp_json["errors"]:
            print(f" - {error['code']}: {error['message']}")
        api_resp.raise_for_status()
    return api_resp, api_resp_json, d1_datasets, error


@app.cell
def _(d1_datasets):
    d1_datasets
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        /// admonition |

        The same endpoint can also be used for creating a new D1 dataset. This can be done by performing a POST
        request with the name of the dataset as the payload.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Performing queries

        Queries to D1 databases using the API are made using POST requests to
        `/accounts/{account_id}/d1/database/{database_id}/query`
        [endpoint](https://developers.cloudflare.com/api/resources/d1/subresources/database/methods/query/).
        The query (as well as optional query parameters) must be added as payload.
        """
    )
    return


@app.cell
def _(HOSTNAME, requests):
    # Perform a query and return results as json
    # Raises error otherwise, prints which errors were obtained
    def query_d1(account_id, database_id, token, query):
        url = f"{HOSTNAME}/client/v4/accounts/{account_id}/d1/database/{database_id}/query"
        payload = dict(sql=query)
        query_resp = requests.post(
            url, headers={"Authorization": "Bearer {}".format(token)}, json=payload
        )
        query_resp_json = query_resp.json()

        if query_resp_json["success"]:
            return query_resp_json["result"]
        else:
            print(
                f"Failed to perform query to D1 dataset (status code {query_resp.status_code}).",
                "Received the following errors:",
            )
            for error in query_resp_json["errors"]:
                print(f" - {error['code']}: {error['message']}")
            query_resp.raise_for_status()

    return (query_d1,)


@app.cell
def _(mo):
    mo.md(
        r"""
        /// admonition | Setting up D1 datasets

        While not shown in this notebook, SQL tables can be created and populated on the API side by running queries
        with `CREATE TABLE` and `INSERT INTO` respectively. Both of these will require tokens with `write`
        permissions, however, and represent a more manual approach to populating SQL tables. The alternative would be
        to import an already existing database into D1.

        More information on how to import (and export) data from D1 datasets can be found in
        [this dev page](https://developers.cloudflare.com/d1/best-practices/import-export-data/).

        ///

        Queries vary from table to table, so we will perform a simple fetch of the first 10 lines of a given table.
        """
    )
    return


@app.cell
def _():
    # The database being queried (examples are the uuid in the d1_datasets dataframe above)
    DATABASE_ID = "<your-database-id>"

    TABLE_NAME = "<your-database-table>"
    return DATABASE_ID, TABLE_NAME


@app.cell
def _(CF_ACCOUNT_TAG, DATABASE_ID, TABLE_NAME, TOKEN, query_d1):
    _query = f"SELECT * FROM {TABLE_NAME} LIMIT 10;"

    query_resp_raw = query_d1(CF_ACCOUNT_TAG, DATABASE_ID, TOKEN, _query)
    return (query_resp_raw,)


@app.cell
def _(pd, query_resp_raw):
    try:
        query_output = pd.DataFrame(query_resp_raw[0]["results"])
    except Exception as e:
        print("Could not parse results into a dataframe:", e)
        print("Will display raw results instead")
        query_output = query_resp_raw
    return (query_output,)


@app.cell
def _(query_output):
    query_output
    return


if __name__ == "__main__":
    app.run()

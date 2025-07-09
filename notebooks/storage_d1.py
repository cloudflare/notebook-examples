# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "anywidget",
#     "js",
#     "marimo",
#     "moutils",
#     "nbformat",
#     "requests",
# ]
# ///

import marimo

__generated_with = "0.14.10"
app = marimo.App(
    width="full",
    app_title="Cloudflare Notebook",
    auto_download=["ipynb", "html"],
)

###############
# Login Cells #
###############
get_accounts = None


@app.cell(hide_code=True)
def _():
    # Helper Stub - click to view code
    import json
    import marimo as mo
    import requests
    import warnings
    import moutils
    import urllib
    from moutils.oauth import PKCEFlow
    from urllib.request import Request, urlopen

    debug = False
    warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")
    warnings.filterwarnings("ignore", category=UserWarning, module="fanstatic")
    proxy = "https://api-proxy.notebooks.cloudflare.com"

    # Configure OAuth endpoints based on environment
    try:
        import js

        origin = js.eval("self.location?.origin")
        if debug: print(f"[DEBUG] WASM environment detected - origin: {origin}")

        if "localhost:8088" in origin:
            if debug: print("[DEBUG] Environment: Local WASM with Cloudflare Pages")
            oauth_config = {
                "logout_url": f"{origin}/oauth2/revoke",
                "redirect_uri": f"{origin}/oauth/callback",
                "token_url": f"{origin}/oauth2/token",
                "use_new_tab": True,
            }
        elif "localhost" in origin:
            if debug: print("[DEBUG] Environment: Local WASM (standard)")
            oauth_config = {
                "logout_url": "https://dash.cloudflare.com/oauth2/revoke",
                "redirect_uri": "https://auth.sandbox.marimo.app/oauth/sso-callback",
                "token_url": "https://dash.cloudflare.com/oauth2/token",
                "use_new_tab": False,
            }
        else:
            if debug: print("[DEBUG] Environment: Production WASM")
            oauth_config = {
                "logout_url": f"{origin}/oauth2/revoke",
                "redirect_uri": f"{origin}/oauth/callback",
                "token_url": f"{origin}/oauth2/token",
                "use_new_tab": True,
            }
    except AttributeError:
        if debug: print("[DEBUG] Environment: Local Python")
        oauth_config = {
            "logout_url": "https://dash.cloudflare.com/oauth2/revoke",
            "redirect_uri": "https://auth.sandbox.marimo.app/oauth/sso-callback",
            "token_url": "https://dash.cloudflare.com/oauth2/token",
            "use_new_tab": False,
        }

    oauth_config["proxy"] = proxy
    oauth_config["moutils_oauth_version"] = moutils.__version__

    # Debug OAuth config
    if debug:
        print("[DEBUG] OAuth configuration:")
        for key, value in oauth_config.items():
            print(f"  {key}: {value}")

    # Functions
    async def get_accounts(debug, token):
        # Check for valid token
        if not token or token.strip() == "":
            print("Please login using the button above")
            return []

        # Use the proxy for API calls in WASM environment to avoid CORS issues
        request_url = f"{proxy}/client/v4/accounts"
        headers = {"Authorization": f"Bearer {token}"}
        if debug:
            print("[DEBUG] get_accounts request URL:", request_url)
            print("[DEBUG] get_accounts headers:", headers)
            print("[DEBUG] get_accounts token (first 40 chars):", token[:40] + "..." if token else "None")
        from urllib.error import HTTPError

        try:
            request = Request(request_url, headers=headers)
            res = json.load(urlopen(request))
            return res.get("result", []) or []
        except HTTPError as e:
            print("Token invalid - Please login using the button above")
            if debug:
                print("[DEBUG] HTTPError:", e)
                print("[DEBUG] HTTPError response body:", e.read().decode())
            return []
        except Exception as e:
            print("Token invalid - Please login using the button above")
            if debug: print("[DEBUG] Exception:", e)
            return []

    if debug: print("[DEBUG] Helper functions cell completed")
    return Request, debug, get_accounts, js, json, key, mo, moutils, oauth_config, origin, PKCEFlow, proxy, requests, urllib, urlopen, value, warnings


@app.cell(hide_code=True)
def _(debug, oauth_config, PKCEFlow):
    # Login to Cloudflare - click to view code
    df = PKCEFlow(
        provider="cloudflare",
        client_id="ec85d9cd-ff12-4d96-a376-432dbcf0bbfc",
        logout_url=oauth_config.get("logout_url"),
        redirect_uri=oauth_config.get("redirect_uri"),
        token_url=oauth_config.get("token_url"),
        proxy=oauth_config.get("proxy"),
        use_new_tab=oauth_config.get("use_new_tab", True),
        debug=debug,
    )
    df
    return df


@app.cell(hide_code=True)
async def _(debug, df, get_accounts, mo):
    # Login Stub - click to view code
    if debug: print(f"[DEBUG] Access token (truncated to 20 chars): {df.access_token[:20] + '...' if df.access_token else 'None'}")
    accounts = await get_accounts(debug, df.access_token)
    radio = mo.ui.radio(options=[a["name"] for a in accounts], label="Select Account")
    return accounts, radio


@app.cell(hide_code=True)
def _(accounts, df, mo, radio):
    # Select Account Stub - click to view code
    account_name = radio.value if radio.value else None
    account_id = (
        next((a["id"] for a in accounts if a["name"] == account_name), None)
        if accounts
        else None
    )
    mo.hstack(
        [
            radio,
            mo.md(
                "Variables"
                "<pre>"
                f"account_id:      {account_id[:20] + '...' if account_id else 'None'}\n"
                f"account_name:    {account_name if account_name else 'None'}\n"
                f"df.access_token: {df.access_token[:20] + '...' if df.access_token else 'None'}\n"
                "</pre>"
            ),
        ]
    )
    return account_id, account_name


##################
# Notebook Cells #
##################
@app.cell
def _():
    import pandas as pd
    return pd


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
         - API token (see [here](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)
        for info on how to create one) with **D1 read** permission;<br>
         - at least one D1 dataset with a table.
        """
    )
    return


@app.cell
def _(account_id, df):
    CF_ACCOUNT_ID = account_id
    CF_API_TOKEN = df.access_token
    HOSTNAME = "https://examples-api-proxy.notebooks.cloudflare.com"  # using notebooks.cloudflare.com proxy
    URL = f"{HOSTNAME}/client/v4/accounts/{CF_ACCOUNT_ID}/d1/database"
    return CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, URL


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
def _(CF_API_TOKEN, Request, URL, json, pd, urlopen):
    # Send GET query
    _request = Request(URL, headers={"Authorization": f"Bearer {CF_API_TOKEN}"})
    api_resp = urlopen(_request)

    # Results handling
    api_resp_json = json.load(api_resp)
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
    return (d1_datasets,)


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
def _(HOSTNAME, Request, json, urlopen):
    # Perform a query and return results as json
    # Raises error otherwise, prints which errors were obtained
    def query_d1(account_id, database_id, token, query):
        url = f"{HOSTNAME}/client/v4/accounts/{account_id}/d1/database/{database_id}/query"
        payload = json.dumps({'sql': query}).encode()
        request = Request(url,
                          headers={"Authorization": "Bearer {}".format(token),
                                   "Accept": "application/json",
                                   "Content-Type": "application/json"},
                          data=payload,
                          method='POST')
        query_resp = urlopen(request)
        query_resp_json = json.load(query_resp)

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
def _(mo):
    database_form = mo.ui.text(label="Selected database ID:").form()
    database_form
    return (database_form,)


@app.cell
def _(mo):
    table_form = mo.ui.text(label="Selected database table:").form()
    table_form
    return (table_form,)


@app.cell
def _(database_form, mo, table_form):
    # The database being queried (examples are the uuid in the d1_datasets dataframe above)
    mo.stop(database_form.value is None or table_form.value is None,
            'Please submit a database ID and table above first')
    DATABASE_ID = database_form.value

    TABLE_NAME = table_form.value
    return DATABASE_ID, TABLE_NAME


@app.cell
def _(CF_ACCOUNT_ID, CF_API_TOKEN, DATABASE_ID, TABLE_NAME, query_d1):
    _query = f"SELECT * FROM {TABLE_NAME} LIMIT 10;"

    query_resp_raw = query_d1(CF_ACCOUNT_ID, DATABASE_ID, CF_API_TOKEN, _query)
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

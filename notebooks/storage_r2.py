

import marimo

__generated_with = "0.13.2"
app = marimo.App(width="full", app_title="Cloudflare Notebook")


@app.cell(hide_code=True)
def _():
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
    return get_accounts, get_token, mo, proxy, requests


@app.cell
async def _(get_accounts, get_token, mo):
    # 1) After login, Run ▶ this cell to get your API token and accounts
    # 2) Select a specific Cloudflare account below
    # 3) Start coding!
    token = await get_token()
    accounts = await get_accounts(token)
    radio = mo.ui.radio(options=[a["name"] for a in accounts], label="Select Account")
    return accounts, radio, token


@app.cell(hide_code=True)
def _(accounts, mo, radio, token):
    # Run ▶ this cell to select a specific Cloudflare account
    account_name = radio.value
    account_id = next((a["id"] for a in accounts if a["name"] == account_name), None)
    mo.hstack([radio, mo.md(f"**Variables**  \n**token:** {token}  \n**account_name:** {account_name or 'None'}  \n**account_id:** {account_id or 'None'}")])  # noqa: E501
    return (account_id,)


@app.cell
def _():
    import json
    import pandas as pd
    import datetime
    import hashlib
    import hmac
    return datetime, hashlib, hmac, json, pd


@app.cell
def _(mo):
    mo.md(
        r"""
        # R2 API use case

        In this notebook, we will show a simple use case involving interactions with
         R2 buckets associated to a Cloudflare account. This will involve the following:<br>
         1. listing buckets;<br>
         2. retrieving a file from a bucket.

        **Prerequisites:**<br>
         - R2 API token (see [here](https://developers.cloudflare.com/r2/api/s3/tokens/) for info on how to create
         one);<br>
         - An existing R2 bucket with a CORS policy (see
         [here](https://developers.cloudflare.com/r2/buckets/cors/#add-cors-policies-from-the-dashboard)
           how to configure).

        Note: on the CORS `AllowedOrigins` field, `http://localhost:8088` should be included.
        """
    )
    return


@app.cell
def _(account_id, proxy, token):
    CF_ACCOUNT_ID = account_id  # After login, selected from list above
    CF_API_TOKEN = token  # Or a custom token from dash.cloudflare.com
    HOSTNAME = proxy  # using notebooks.cloudflare.com proxy
    R2_TOKEN = "<your-r2-token>"
    R2_SECRET = "<your-r2-secret>"
    return CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, R2_SECRET, R2_TOKEN


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Listing R2 buckets

        In order to get a list of R2 buckets, we can make use of the `/accounts/{account_id}/r2/buckets` endpoint.<br>

        Note: one call to this endpoint can return at most 1000 entries. Here we fetch only 100.
        """
    )
    return


@app.cell
def _(CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, json, pd, requests):
    # Endpoint to get buckets from an account
    _main_call = f"{HOSTNAME}/client/v4/accounts/{CF_ACCOUNT_ID}/r2/buckets"
    _api_resp = requests.get(
        _main_call,
        params={"per_page": 100},
        headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
    ).text

    r2_info = pd.DataFrame(json.loads(_api_resp)["result"]["buckets"])
    return (r2_info,)


@app.cell
def _(r2_info):
    r2_info
    return


@app.cell
def _(mo):
    mo.md(r"""We can then obtain extra info on each bucket by adding its name on the endpoint:""")
    return


@app.cell
def _(CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, json, requests):
    # Select R2 bucket name (this impacts the rest of the notebook)
    SELECTED_BUCKET = "<your-bucket>"

    # Endpoint to get bucket info
    _main_call = (
        f"{HOSTNAME}/client/v4/accounts/{CF_ACCOUNT_ID}/r2/buckets/{SELECTED_BUCKET}"
    )
    _api_resp = requests.get(
        _main_call, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}
    ).text

    json.loads(_api_resp)["result"]
    return (SELECTED_BUCKET,)


@app.cell
def _(mo):
    mo.md(
        r"""
        The `storage_class` value is particularly important as bucket usage metrics may be separated between standard
        and infrequent access versions. For more information on storage classes, check the dedicated
        [developers page](https://developers.cloudflare.com/r2/buckets/storage-classes/).

        Futher interactions with a given bucket can also be done using requests, but will require
        [signing](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_sigv-create-signed-request.html)
        each request. We will download an object to memory as an example:
        """
    )
    return


@app.cell
def _(CF_ACCOUNT_ID, SELECTED_BUCKET):
    # Select which r2 object to download to memory
    SELECTED_OBJECT_PATH = "<your-r2-object>"

    host = f'{SELECTED_BUCKET}.{CF_ACCOUNT_ID}.r2.cloudflarestorage.com'
    endpoint = f'https://{host}/{SELECTED_OBJECT_PATH}'
    return SELECTED_OBJECT_PATH, endpoint, host


@app.cell(hide_code=True)
def _(
    R2_SECRET,
    R2_TOKEN,
    SELECTED_OBJECT_PATH,
    datetime,
    hashlib,
    hmac,
    host,
):
    # These are steps needed in order to create a signed AWS request

    # Timestamp must be UTC
    _curr_timestamp = datetime.datetime.now(datetime.UTC)
    _request_datetime = _curr_timestamp.strftime('%Y%m%dT%H%M%SZ')
    _request_date = _curr_timestamp.strftime('%Y%m%d')

    # Canonical request
    _method = 'GET'
    _canonical_uri = f'/{SELECTED_OBJECT_PATH}'
    _canonical_querystring = ''
    _payload_hash = hashlib.sha256(b'').hexdigest()
    _canonical_headers = '\n'.join([
        f'host:{host}',
        f'x-amz-content-sha256:{_payload_hash}',
        f'x-amz-date:{_request_datetime}\n'
    ])
    _signed_headers = 'host;x-amz-content-sha256;x-amz-date'

    _canonical_request = '\n'.join([
        _method,
        _canonical_uri,
        _canonical_querystring,
        _canonical_headers,
        _signed_headers,
        _payload_hash
    ])

    # String to sign
    _region = 'auto'
    _service = 's3'
    _algorithm = 'AWS4-HMAC-SHA256'
    _credential_scope = f'{_request_date}/{_region}/{_service}/aws4_request'
    _hashed_canonical_request = hashlib.sha256(_canonical_request.encode('utf-8')).hexdigest()

    _string_to_sign = '\n'.join([
        _algorithm,
        _request_datetime,
        _credential_scope,
        _hashed_canonical_request
    ])

    # Signing key
    def hmac_sha_hash(key, msg):
        return hmac.new(key, msg=msg.encode('utf-8'), digestmod=hashlib.sha256).digest()

    _secret_access_key = ('AWS4' + R2_SECRET).encode('utf-8')
    _date_key = hmac_sha_hash(_secret_access_key, _request_date)
    _region_key = hmac_sha_hash(_date_key, _region)
    _service_key = hmac_sha_hash(_region_key, _service)
    _signing_key = hmac_sha_hash(_service_key, 'aws4_request')

    _signature = hmac.new(_signing_key, msg=_string_to_sign.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()

    # Create request with the signature
    _authorization_header = ' '.join([
        f'{_algorithm}',
        f'Credential={R2_TOKEN}/{_credential_scope},',
        f'SignedHeaders={_signed_headers},',
        f'Signature={_signature}'
    ])

    headers = {
        'x-amz-date': _request_datetime,
        'x-amz-content-sha256': _payload_hash,
        'Authorization': _authorization_header
    }
    return (headers,)


@app.cell
def _(endpoint, headers, requests):
    response = requests.get(endpoint, headers=headers)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    return


if __name__ == "__main__":
    app.run()

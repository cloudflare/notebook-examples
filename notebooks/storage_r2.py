# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "anywidget",
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
@app.cell(hide_code=True)
def _():
    # Helper Stub - click to view code
    import json, marimo as mo, requests, warnings, moutils, urllib, sys  # noqa: E401
    from moutils.oauth import PKCEFlow
    from urllib.request import Request, urlopen

    debug = False
    warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")
    warnings.filterwarnings("ignore", category=UserWarning, module="fanstatic")
    proxy = "https://api-proxy.notebooks.cloudflare.com"
    is_wasm = sys.platform == "emscripten"
    if debug:
        print(f"[DEBUG] WASM environment detected: {is_wasm}")

    async def get_accounts(token):
        if not token or token.strip() == "":
            print("Please login using the button above")
            return []
        request_url = f"{proxy}/client/v4/accounts" if is_wasm else "https://api.cloudflare.com/client/v4/accounts"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            request = Request(request_url, headers=headers)
            res = json.load(urlopen(request))
            return res.get("result", []) or []
        except Exception as e:
            print("Token invalid - Please login using the button above")
            if debug: print("[DEBUG] Exception:", e)
            return []

    return PKCEFlow, Request, debug, get_accounts, json, mo, moutils, proxy, requests, urllib, urlopen, warnings


@app.cell(hide_code=True)
def _(PKCEFlow):
    # Login to Cloudflare - click to view code
    df = PKCEFlow(provider="cloudflare")
    df
    return df


@app.cell(hide_code=True)
async def _(debug, df, get_accounts, mo):
    # Login Stub - click to view code
    if debug: print(f"[DEBUG] Access token (truncated to 20 chars): {df.access_token[:20] + '...' if df.access_token else 'None'}")
    accounts = await get_accounts(df.access_token)
    radio = mo.ui.radio(options=[a["name"] for a in accounts], label="Select Account")
    return accounts, radio


@app.cell(hide_code=True)
def _(accounts, df, mo, radio):
    # Select Account Stub - click to view code
    account_name = radio.value if radio.value else None
    account_id = (next((a["id"] for a in accounts if a["name"] == account_name), None) if accounts else None)
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
    import datetime
    import hashlib
    import hmac
    return datetime, hashlib, hmac, pd


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
def _(mo):
    r2_token_form = mo.ui.text(label="Provided R2 token:").form()
    r2_token_form
    return (r2_token_form,)


@app.cell
def _(mo):
    r2_secret_form = mo.ui.text(label="Provided R2 secret:").form()
    r2_secret_form
    return (r2_secret_form,)


@app.cell
def _(account_id, mo, r2_secret_form, r2_token_form, df):
    mo.stop((account_id is None or df.access_token is None
             or r2_token_form.value is None or r2_secret_form.value is None),
            'Please submit an account ID, API token, R2 token and R2 secret above first')

    CF_ACCOUNT_ID = account_id
    CF_API_TOKEN = df.access_token
    HOSTNAME = "https://examples-api-proxy.notebooks.cloudflare.com"  # using notebooks.cloudflare.com proxy
    R2_TOKEN = r2_token_form.value
    R2_SECRET = r2_secret_form.value
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
def _(
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    HOSTNAME,
    Request,
    json,
    pd,
    proxy,
    urllib,
    urlopen,
):
    # Endpoint to get buckets from an account
    _main_call = f"{proxy}/client/v4/accounts/{CF_ACCOUNT_ID}/r2/buckets"
    _params = {"per_page": 100}
    _main_call = _main_call + '?' + urllib.parse.urlencode(_params)
    _request = Request(_main_call, headers={"Authorization": f"Bearer {CF_API_TOKEN}"})
    _api_resp = urlopen(_request).read()

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
def _(mo):
    r2_bucket_form = mo.ui.text(label="Provided R2 bucket:").form()
    r2_bucket_form
    return (r2_bucket_form,)


@app.cell
def _(
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    HOSTNAME,
    Request,
    json,
    mo,
    proxy,
    r2_bucket_form,
    urlopen,
):
    mo.stop(r2_bucket_form.value is None,
            'Please submit an R2 bucket above first')

    SELECTED_BUCKET = r2_bucket_form.value

    # Endpoint to get bucket info
    _main_call = (
        f"{proxy}/client/v4/accounts/{CF_ACCOUNT_ID}/r2/buckets/{SELECTED_BUCKET}"
    )
    _request = Request(_main_call, headers={"Authorization": f"Bearer {CF_API_TOKEN}"})
    _api_resp = urlopen(_request).read()

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
def _(mo):
    r2_object_form = mo.ui.text(label="Provided R2 object:").form()
    r2_object_form
    return (r2_object_form,)


@app.cell
def _(CF_ACCOUNT_ID, SELECTED_BUCKET, mo, r2_object_form):
    mo.stop(r2_object_form.value is None,
            'Please submit an R2 object above first')

    SELECTED_OBJECT_PATH = r2_object_form.value

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
def _(Request, endpoint, headers, urlopen):
    _request = Request(endpoint, headers=headers)
    response = urlopen(_request)

    print(f"Status Code: {response.getcode()}")
    print(f"Response: {response.read()}")
    return


if __name__ == "__main__":
    app.run()

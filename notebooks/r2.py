import marimo

__generated_with = "0.11.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import boto3
    import json
    import pandas as pd
    import requests
    return boto3, json, mo, pd, requests


@app.cell
def _(mo):
    mo.md(
        r"""
        # R2 API use case

        In this notebook, we will show a simple use case involving interactions with
         R2 buckets associated to a Cloudflare account. This will involve the following:<br>
         1. listing buckets;<br>
         2. listing files within a bucket;<br>
         3. retrieving a file from a bucket.

        **Prerequisites:**<br>
         - R2 API token (see [here](https://developers.cloudflare.com/r2/api/s3/tokens/) for info on how to create one).
        """
    )
    return


@app.cell
def _():
    CF_ACCOUNT_TAG = "<your-account-tag>"
    R2_TOKEN = "<your-r2-token>"
    R2_SECRET = "<your-r2-secret>"
    CF_API_TOKEN = "<your-token>"

    ENDPOINT = f"https://{CF_ACCOUNT_TAG}.r2.cloudflarestorage.com"

    # API calls
    HOSTNAME = "https://examples-api-proxy.notebooks.cloudflare.com"
    return (
        CF_ACCOUNT_TAG,
        CF_API_TOKEN,
        ENDPOINT,
        HOSTNAME,
        R2_SECRET,
        R2_TOKEN,
    )


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
def _(CF_ACCOUNT_TAG, CF_API_TOKEN, HOSTNAME, json, pd, requests):
    # Endpoint to get buckets from an account
    _main_call = f'{HOSTNAME}/client/v4/accounts/{CF_ACCOUNT_TAG}/r2/buckets'
    _api_resp = requests.get(_main_call,
                             params={'per_page': 100},
                             headers={'Authorization': 'Bearer {}'.format(CF_API_TOKEN)}).text

    r2_info = pd.DataFrame(json.loads(_api_resp)['result']['buckets'])
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
def _(CF_ACCOUNT_TAG, CF_API_TOKEN, HOSTNAME, json, requests):
    # Select R2 bucket name (this impacts the rest of the notebook)
    SELECTED_BUCKET = '<your-bucket>'

    # Endpoint to get bucket info
    _main_call = f'{HOSTNAME}/client/v4/accounts/{CF_ACCOUNT_TAG}/r2/buckets/{SELECTED_BUCKET}'
    _api_resp = requests.get(_main_call,
                             headers={'Authorization': 'Bearer {}'.format(CF_API_TOKEN)}).text

    json.loads(_api_resp)['result']
    return (SELECTED_BUCKET,)


@app.cell
def _(mo):
    mo.md(
        r"""
        The `storage_class` value is particularly important as bucket usage metrics may be separated between standard
        and infrequent access versions. For more information on storage classes, check the dedicated
        [developers page](https://developers.cloudflare.com/r2/buckets/storage-classes/).

        Futher interactions with a given bucket are done using the `boto3` API. Here we will list bucket files and
        download one of them. Since we will be downloading to memory, we will use the S3 `client` instead of
        `resource`.
        """
    )
    return


@app.cell
def _(ENDPOINT, R2_SECRET, R2_TOKEN, boto3):
    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=R2_TOKEN,
        aws_secret_access_key=R2_SECRET,
    )
    return (s3,)


@app.cell
def _(mo):
    mo.md(
        r"""
        Buckets can contain a very large amount of objects, so to prevent long lists of files, we will obtain the
        first 50 only:
        """
    )
    return


@app.cell
def _(SELECTED_BUCKET, pd, s3):
    _file_list = s3.list_objects_v2(Bucket=SELECTED_BUCKET, MaxKeys=50)
    if 'Contents' in _file_list:
        df_files = pd.DataFrame(_file_list['Contents'])
    else:
        df_files = None
    return (df_files,)


@app.cell
def _(df_files):
    df_files
    return


@app.cell
def _(mo):
    mo.md(r"""Finally, we can also download an object to memory:""")
    return


@app.cell
def _(SELECTED_BUCKET, s3):
    # Select which r2 object to download to memory
    SELECTED_OBJECT_PATH = '<your-r2-object>'

    _response = s3.get_object(Bucket=SELECTED_BUCKET, Key=SELECTED_OBJECT_PATH)
    file_contents = _response["Body"].read().decode()
    return SELECTED_OBJECT_PATH, file_contents


@app.cell
def _(file_contents):
    file_contents
    return


if __name__ == "__main__":
    app.run()

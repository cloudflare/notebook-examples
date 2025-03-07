import marimo

__generated_with = "0.11.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import boto3
    import pandas as pd
    return boto3, mo, pd


app._unparsable_cell(
    r"""
    TODO:
     - separate cells
     - explain how to delete created files and buckets
    """,
    name="_"
)


@app.cell
def _(mo):
    mo.md(
        r"""
        # R2 API use case

        In this notebook, we will show a simple use case involving interactions with
         R2 buckets associated to a Cloudflare account. This will involve the following:<br>
         1. creating a bucket;<br>
         2. uploading a simple file;<br>
         3. retrieving said file

        all using the Cloudflare API.

        **Prerequisites:**<br>
         - API token (see [here](https://developers.cloudflare.com/r2/api/s3/tokens/) for info on how to create one).
        """
    )
    return


@app.cell
def _():
    CF_ACCOUNT_TAG = "your_account_id"
    TOKEN = "your-token"
    ACCESS_SECRET = "your-access-secret"

    ENDPOINT = f"https://{CF_ACCOUNT_TAG}.r2.cloudflarestorage.com"
    return ACCESS_SECRET, CF_ACCOUNT_TAG, ENDPOINT, TOKEN


@app.cell
def _(ACCESS_SECRET, ENDPOINT, TOKEN, boto3):
    s3 = boto3.client(
        "s3",
        endpoint_url=ENDPOINT,
        aws_access_key_id=TOKEN,
        aws_secret_access_key=ACCESS_SECRET,
    )

    # Step 1: creating a bucket
    bucket_name = "my-test-bucket"
    s3.create_bucket(Bucket=bucket_name)
    print(f"✅ Bucket '{bucket_name}' created!")

    # Step 2: Uploading a simple file
    file_name = "hello.txt"
    s3.put_object(Bucket=bucket_name, Key=file_name, Body="Hello, Cloudflare R2!")
    print(f"✅ File '{file_name}' uploaded!")

    # Step 3: Retrieve and print the file contents
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    file_contents = response["Body"].read().decode()
    print(f"📂 Retrieved file contents: {file_contents}")
    return bucket_name, file_contents, file_name, response, s3


if __name__ == "__main__":
    app.run()

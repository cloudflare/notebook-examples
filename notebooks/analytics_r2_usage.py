import marimo

__generated_with = "0.14.7"

app = marimo.App(
    width="full",
    auto_download=["ipynb", "html"],
    app_title="Cloudflare Notebook",
)

####################
# Helper Functions #
####################
get_accounts = None


@app.cell(hide_code=True)
async def _():
    # Helper Functions - click to view code
    import js
    import json
    from urllib.request import Request, urlopen

    origin = js.eval("self.location?.origin")
    proxy = "https://api-proxy.notebooks.cloudflare.com"

    async def get_accounts(token):
        # Example API request to list available Cloudflare accounts
        request = Request(f"{proxy}/client/v4/accounts", headers={"Authorization": f"Bearer {token}"})
        res = json.load(urlopen(request))
        return res.get("result", []) or []

    return js, json, Request, urlopen, origin, proxy, get_accounts


###############
# Login Cells #
###############
@app.cell(hide_code=True)
def _(origin):
    # Login to Cloudflare - click to view code
    import requests  # noqa: F401 - required for moutils.oauth
    from moutils.oauth import PKCEFlow

    df = PKCEFlow(
        provider="cloudflare",
        client_id="ec85d9cd-ff12-4d96-a376-432dbcf0bbfc",
        logout_url=f"{origin}/oauth2/revoke",
        redirect_uri=f"{origin}/oauth/callback",
        token_url=f"{origin}/oauth2/token",
    )
    df
    return PKCEFlow, df


@app.cell()
async def _(mo, df):
    # 1) After login, Run ▶ this cell to get your API token and accounts
    # 2) Select a specific Cloudflare account below
    # 3) Start coding
    print(f"df.access_token: {df.access_token}")
    accounts = await get_accounts(df.access_token)
    radio = mo.ui.radio(options=[a["name"] for a in accounts], label="Select Account")
    return accounts, radio


@app.cell(hide_code=True)
def _(df, accounts, radio, mo):
    # Run ▶ this cell to select a specific Cloudflare account
    account_name = radio.value if radio else None
    account_id = (next((a["id"] for a in accounts if a["name"] == account_name), None) if accounts else None)  # noqa: E501
    mo.hstack([radio, mo.md(f"**Variables**  \n**token:** {df.access_token}  \n**account_name:** {account_name or 'None'}  \n**account_id:** {account_id or 'None'}"),])  # noqa: E501
    return


##################
# Notebook Cells #
##################
@app.cell
def _(account_id, mo, proxy, token):
    mo.stop(token is None or account_id is None, 'Please retrieve a token first and select an account above')

    import altair as alt
    from datetime import datetime
    import pandas as pd

    CF_ACCOUNT_ID = account_id
    CF_API_TOKEN = token  # or a custom token from dash.cloudflare.com
    HOSTNAME = proxy
    return CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, alt, datetime, pd


@app.cell
def _(mo):
    mo.md(
        r"""
        # R2 usage metrics

        In this notebook, we will make use of the GraphQL endpoint in order to obtain usage metrics
        related to an account's R2 buckets. This will involve the following:<br>
        - Ranking buckets by number of objects, storage and operations<br>
        - Plot overall account's usage of R2.

        **Prerequisites:**<br>
        - API token (see [here](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)
        for info on how to create one);<br>
        - At least one active R2 bucket.<br>

        Relevant documentation:<br>
        - [R2 metrics dev page](https://developers.cloudflare.com/r2/platform/metrics-analytics/)<br>
        """
    )
    return


@app.cell
def _(datetime):
    # Establish time interval since start of month (trimmed to minutes)
    curr_dt = datetime.now().replace(second=0, microsecond=0)
    start_dt = curr_dt.replace(day=1, hour=0).strftime("%Y-%m-%dT%H:00:00Z")
    return (start_dt,)


@app.cell
def _():
    # Helper functions
    # Used to obtain human readable formats of values for chart hover info
    # Warning: these assume values are either 0 or positive

    # Human readable bytes
    def readable_byte_vals(val):
        for suffix in ["B", "kB", "MB", "GB", "TB"]:
            if val > 1000 and suffix != "TB":
                val /= 1000
            else:
                return f"{val:.2f} {suffix}"

    # Human readable numbers (requests, objects)
    def readable_numbers(val):
        for suffix in ["", "k", "M", "B"]:
            if val > 1000 and suffix != "B":
                val /= 1000
            else:
                return f"{round(val, 2)}{suffix}".strip()

    return readable_byte_vals, readable_numbers


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Rank of buckets

        Ranks will be limited to 15 entries by default.
        """
    )
    return


@app.cell
def _():
    TOP_N = 15
    return (TOP_N,)


@app.cell
def _(mo):
    mo.md(r"""### Rank by number of objects""")
    return


@app.cell
def _(
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    HOSTNAME,
    Request,
    TOP_N,
    json,
    start_dt,
    urlopen,
):
    _QUERY_STR = """
    query BucketLevelMetricsQuery($accountTag: string!, $limit: uint64!, $queryStart: Date) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          standard: r2StorageAdaptiveGroups(orderBy: [max_objectCount_DESC],
                                            limit: $limit,
                                            filter: {storageClass: "Standard", datetime_geq: $queryStart}) {
            max {
              objectCount
            }
            dimensions {
              bucketName
            }
          }
          ia: r2StorageAdaptiveGroups(orderBy: [max_objectCount_DESC],
                                      limit: $limit,
                                      filter: {storageClass: "InfrequentAccess", datetime_geq: $queryStart}) {
            max {
              objectCount
            }
            dimensions {
              bucketName
            }
          }
        }
      }
    }
    """

    _QUERY_VARIABLES = {
        "accountTag": CF_ACCOUNT_ID,
        "limit": TOP_N,
        "queryStart": start_dt,
    }

    _data = json.dumps({"query": _QUERY_STR, "variables": _QUERY_VARIABLES}).encode()
    _request = Request(f"{HOSTNAME}/client/v4/graphql",
                       headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
                       data=_data,
                       method='POST')
    _resp_raw = urlopen(_request).read()

    json_object_rank_data = json.loads(_resp_raw)
    return (json_object_rank_data,)


@app.cell
def _(json_object_rank_data, pd):
    if json_object_rank_data["errors"] is None:
        # Process results for standard buckets
        _rows_standard = []
        for _entry in json_object_rank_data["data"]["viewer"]["accounts"][0]["standard"]:
            _curr_row = dict(
                bucket=_entry["dimensions"]["bucketName"],
                objects=_entry["max"]["objectCount"],
            )
            _rows_standard.append(_curr_row)
        df_top_objects_standard = pd.DataFrame(_rows_standard)

        # Process results for infrequent access buckets
        _rows_ia = []
        for _entry in json_object_rank_data["data"]["viewer"]["accounts"][0]["ia"]:
            _curr_row = dict(
                bucket=_entry["dimensions"]["bucketName"],
                objects=_entry["max"]["objectCount"],
            )
            _rows_ia.append(_curr_row)
        df_top_objects_ia = pd.DataFrame(_rows_ia)
    else:
        _error_msg = "\n - ".join([el["message"] for el in json_object_rank_data["errors"]])
        print(f"Obtained the following errors:\n - {_error_msg}")
        raise
    return df_top_objects_ia, df_top_objects_standard


@app.cell
def _(alt, datetime, df_top_objects_standard, start_dt):
    # This prevents us from using fig.display() which would require
    # installing ipython
    _fig = None

    if int(df_top_objects_standard["objects"].sum()) == 0:
        print("No data found for standard buckets, skipping")
    else:
        # For the chart subtitle
        _start_str = datetime.strptime(start_dt, "%Y-%m-%dT%H:00:00Z").date()

        _fig = (
            alt.Chart(df_top_objects_standard)
            .mark_bar()
            .encode(
                alt.X("objects", title="Total objects"),
                alt.Y(
                    "bucket",
                    title="Bucket name",
                    sort=alt.EncodingSortField(field="objects", order="ascending"),
                ),
            )
            .properties(
                title=alt.TitleParams(
                    "Buckets with most standard objects",
                    subtitle=f"Data since {_start_str}",
                ),
                height=350,
                width=700,
            )
        )
    _fig
    return


@app.cell
def _(alt, datetime, df_top_objects_ia, start_dt):
    _fig = None

    if int(df_top_objects_ia["objects"].sum()) == 0:
        print("No data found for infrequent access buckets, skipping")
    else:
        # For the chart subtitle
        _start_str = datetime.strptime(start_dt, "%Y-%m-%dT%H:00:00Z").date()

        _fig = (
            alt.Chart(df_top_objects_ia)
            .mark_bar()
            .encode(
                alt.X("objects", title="Total objects"),
                alt.Y(
                    "bucket",
                    title="Bucket name",
                    sort=alt.EncodingSortField(field="objects", order="ascending"),
                ),
            )
            .properties(
                title=alt.TitleParams(
                    "Buckets with most infrequent access objects",
                    subtitle=f"Data since {_start_str}",
                ),
                height=350,
                width=700,
            )
        )
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""### Rank by storage size""")
    return


@app.cell
def _(
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    HOSTNAME,
    Request,
    TOP_N,
    json,
    start_dt,
    urlopen,
):
    _QUERY_STR = """
    query BucketLevelMetricsQuery($accountTag: string!, $limit: uint64!, $queryStart: Date) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          standard: r2StorageAdaptiveGroups(orderBy: [max_payloadSize_DESC],
                                            limit: $limit,
                                            filter: {storageClass: "Standard", datetime_geq: $queryStart}) {
            max {
              payloadSize
            }
            dimensions {
              bucketName
            }
          }
          ia: r2StorageAdaptiveGroups(orderBy: [max_payloadSize_DESC],
                                      limit: $limit,
                                      filter: {storageClass: "InfrequentAccess", datetime_geq: $queryStart}) {
            max {
              payloadSize
            }
            dimensions {
              bucketName
            }
          }
        }
      }
    }
    """

    _QUERY_VARIABLES = {
        "accountTag": CF_ACCOUNT_ID,
        "limit": TOP_N,
        "queryStart": start_dt,
    }

    _data = json.dumps({"query": _QUERY_STR, "variables": _QUERY_VARIABLES}).encode()
    _request = Request(f"{HOSTNAME}/client/v4/graphql",
                       headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
                       data=_data,
                       method='POST')
    _resp_raw = urlopen(_request).read()

    json_size_rank_data = json.loads(_resp_raw)
    return (json_size_rank_data,)


@app.cell
def _(json_size_rank_data, pd, readable_byte_vals):
    if json_size_rank_data["errors"] is None:
        # Process results for standard buckets
        _rows_standard = []
        for _entry in json_size_rank_data["data"]["viewer"]["accounts"][0]["standard"]:
            _curr_row = dict(
                bucket=_entry["dimensions"]["bucketName"],
                size=_entry["max"]["payloadSize"],
            )
            _rows_standard.append(_curr_row)
        df_top_size_standard = pd.DataFrame(_rows_standard)
        df_top_size_standard["size_gb"] = df_top_size_standard["size"] / 1e9
        df_top_size_standard["size_readable"] = df_top_size_standard["size"].apply(lambda x: readable_byte_vals(x))

        # Process results for infrequent access buckets
        _rows_ia = []
        for _entry in json_size_rank_data["data"]["viewer"]["accounts"][0]["ia"]:
            _curr_row = dict(
                bucket=_entry["dimensions"]["bucketName"],
                size=_entry["max"]["payloadSize"],
            )
            _rows_ia.append(_curr_row)
        df_top_size_ia = pd.DataFrame(_rows_ia)
        df_top_size_ia["size_gb"] = df_top_size_ia["size"] / 1e9
        df_top_size_ia["size_readable"] = df_top_size_ia["size"].apply(
            lambda x: readable_byte_vals(x)
        )
    else:
        _error_msg = "\n - ".join([el["message"] for el in json_size_rank_data["errors"]])
        print(f"Obtained the following errors:\n - {_error_msg}")
        raise
    return df_top_size_ia, df_top_size_standard


@app.cell
def _(alt, datetime, df_top_size_standard, start_dt):
    _fig = None

    if int(df_top_size_standard["size"].sum()) == 0:
        print("No data found for standard buckets, skipping")
    else:
        # For the chart subtitle
        _start_str = datetime.strptime(start_dt, "%Y-%m-%dT%H:00:00Z").date()

        _fig = (
            alt.Chart(df_top_size_standard)
            .mark_bar()
            .encode(
                alt.X("size_gb", title="Object storage (GB)"),
                alt.Y(
                    "bucket",
                    title="Bucket name",
                    sort=alt.EncodingSortField(field="size_gb", order="ascending"),
                ),
                alt.Text("size_readable"),
                alt.Tooltip(["bucket", "size_readable"]),
            )
            .properties(
                title=alt.TitleParams(
                    "Buckets with most standard object storage",
                    subtitle=f"Data since {_start_str}",
                ),
                height=350,
                width=700,
            )
        )
    _fig
    return


@app.cell
def _(alt, datetime, df_top_size_ia, start_dt):
    _fig = None

    if int(df_top_size_ia["size"].sum()) == 0:
        print("No data found for infrequent access buckets, skipping")
    else:
        # For the chart subtitle
        _start_str = datetime.strptime(start_dt, "%Y-%m-%dT%H:00:00Z").date()

        _fig = (
            alt.Chart(df_top_size_ia)
            .mark_bar()
            .encode(
                alt.X("size_gb", title="Object storage (GB)"),
                alt.Y(
                    "bucket",
                    title="Bucket name",
                    sort=alt.EncodingSortField(field="size_gb", order="ascending"),
                ),
                alt.Text("size_readable"),
                alt.Tooltip(["bucket", "size_readable"]),
            )
            .properties(
                title=alt.TitleParams(
                    "Buckets with most infrequent access object storage",
                    subtitle=f"Data since {_start_str}",
                ),
                height=350,
                width=700,
            )
        )
    _fig
    return


@app.cell
def _(
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    HOSTNAME,
    Request,
    TOP_N,
    json,
    start_dt,
    urlopen,
):
    _QUERY_STR = """
    query getR2Requests($accountTag: string,
                        $limit: $limit: uint64!,
                        $classAOpsFilterStandard: AccountR2OperationsAdaptiveGroupsFilter_InputObject,
                        $classBOpsFilterStandard: AccountR2OperationsAdaptiveGroupsFilter_InputObject,
                        $classAOpsFilterIA: AccountR2OperationsAdaptiveGroupsFilter_InputObject,
                        $classBOpsFilterIA: AccountR2OperationsAdaptiveGroupsFilter_InputObject) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          classAOpsStandard: r2OperationsAdaptiveGroups(orderBy: [sum_requests_DESC],
                                                        limit: $limit,
                                                        filter: $classAOpsFilterStandard) {
            sum {
              requests
            }
            dimensions {
              storageClass
              bucketName
            }
          }
          classBOpsStandard: r2OperationsAdaptiveGroups(orderBy: [sum_requests_DESC],
                                                        limit: $limit,
                                                        filter: $classBOpsFilterStandard) {
            sum {
              requests
            }
            dimensions {
              storageClass
              bucketName
            }
          }
          classAOpsIA: r2OperationsAdaptiveGroups(orderBy: [sum_requests_DESC],
                                                  limit: $limit,
                                                  filter: $classAOpsFilterIA) {
            sum {
              requests
            }
            dimensions {
              storageClass
              bucketName
            }
          }
          classBOpsIA: r2OperationsAdaptiveGroups(orderBy: [sum_requests_DESC],
                                                  limit: $limit,
                                                  filter: $classBOpsFilterIA) {
            sum {
              requests
            }
            dimensions {
              storageClass
              bucketName
            }
          }
        }
      }
    }
    """

    _action_status = ["success", "userError"]

    _aops_actions = [
        "ListBuckets",
        "PutBucket",
        "ListObjects",
        "PutObject",
        "CopyObject",
        "CompleteMultipartUpload",
        "CreateMultipartUpload",
        "UploadPart",
        "UploadPartCopy",
        "PutBucketEncryption",
        "ListMultipartUploads",
        "PutBucketCors",
        "PutBucketLifecycleConfiguration",
        "ListParts",
        "PutBucketStorageClass",
        "LifecycleStorageTierTransition",
    ]

    _bops_actions = [
        "HeadBucket",
        "HeadObject",
        "GetObject",
        "ReportUsageSummary",
        "GetBucketEncryption",
        "GetBucketLocation",
        "GetBucketLifecycleConfiguration",
        "GetBucketCors",
    ]

    _QUERY_VARIABLES = {
        "accountTag": CF_ACCOUNT_ID,
        "limit": TOP_N,
        "classAOpsFilterStandard": {
            "actionType_in": _aops_actions,
            "storageClass": "Standard",
            "actionStatus_in": _action_status,
            "AND": [{"datetime_geq": start_dt}],
        },
        "classBOpsFilterStandard": {
            "actionType_in": _bops_actions,
            "storageClass": "Standard",
            "actionStatus_in": _action_status,
            "AND": [{"datetime_geq": start_dt}],
        },
        "classAOpsFilterIA": {
            "actionType_in": _aops_actions,
            "storageClass": "InfrequentAccess",
            "actionStatus_in": _action_status,
            "AND": [{"datetime_geq": start_dt}],
        },
        "classBOpsFilterIA": {
            "actionType_in": _bops_actions,
            "storageClass": "InfrequentAccess",
            "actionStatus_in": _action_status,
            "AND": [{"datetime_geq": start_dt}],
        },
    }

    _data = json.dumps({"query": _QUERY_STR, "variables": _QUERY_VARIABLES}).encode()
    _request = Request(f"{HOSTNAME}/client/v4/graphql",
                       headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
                       data=_data,
                       method='POST')
    _resp_raw = urlopen(_request).read()

    json_request_rank_data = json.loads(_resp_raw)
    return (json_request_rank_data,)


@app.cell
def _(json_request_rank_data, pd, readable_numbers):
    if json_request_rank_data["errors"] is None:
        # Store everything under the same dataframe, long format
        _rows = []

        # Operations A - standard
        for _entry in json_request_rank_data["data"]["viewer"]["accounts"][0]["classAOpsStandard"]:
            _curr_row = dict(
                bucket=_entry["dimensions"]["bucketName"],
                storage_class=_entry["dimensions"]["storageClass"],
                operation_type="A",
                requests=_entry["sum"]["requests"],
            )
            _rows.append(_curr_row)

        # Operations A - infrequent access
        for _entry in json_request_rank_data["data"]["viewer"]["accounts"][0]["classAOpsIA"]:
            _curr_row = dict(
                bucket=_entry["dimensions"]["bucketName"],
                storage_class=_entry["dimensions"]["storageClass"],
                operation_type="A",
                requests=_entry["sum"]["requests"],
            )
            _rows.append(_curr_row)

        # Operations B - standard
        for _entry in json_request_rank_data["data"]["viewer"]["accounts"][0]["classBOpsStandard"]:
            _curr_row = dict(
                bucket=_entry["dimensions"]["bucketName"],
                storage_class=_entry["dimensions"]["storageClass"],
                operation_type="B",
                requests=_entry["sum"]["requests"],
            )
            _rows.append(_curr_row)

        # Operations B - infrequent access
        for _entry in json_request_rank_data["data"]["viewer"]["accounts"][0]["classBOpsIA"]:
            _curr_row = dict(
                bucket=_entry["dimensions"]["bucketName"],
                storage_class=_entry["dimensions"]["storageClass"],
                operation_type="B",
                requests=_entry["sum"]["requests"],
            )
            _rows.append(_curr_row)

        df_top_requests = pd.DataFrame(_rows)
        df_top_requests["requests_readable"] = df_top_requests["requests"].apply(
            lambda x: readable_numbers(x)
        )

    else:
        _error_msg = "\n - ".join([el["message"] for el in json_request_rank_data["errors"]])
        print(f"Obtained the following errors:\n - {_error_msg}")
        raise
    return (df_top_requests,)


@app.cell
def _(alt, datetime, df_top_requests, start_dt):
    _fig = None
    _curr_view = df_top_requests.loc[
        (df_top_requests["storage_class"] == "Standard")
        & (df_top_requests["operation_type"] == "A")
    ]

    if int(_curr_view["requests"].sum()) == 0:
        print("No data found for class A operations in standard buckets, skipping")
    else:
        # For the chart subtitle
        _start_str = datetime.strptime(start_dt, "%Y-%m-%dT%H:00:00Z").date()

        _fig = (
            alt.Chart(_curr_view)
            .mark_bar()
            .encode(
                alt.X(
                    "requests",
                    title="Class A operations",
                    scale=alt.Scale(type="symlog"),
                ),
                alt.Y(
                    "bucket",
                    title="Bucket name",
                    sort=alt.EncodingSortField(field="requests", order="ascending"),
                ),
                tooltip=[
                    alt.Tooltip("bucket", title="Bucket name"),
                    alt.Tooltip("requests_readable", title="Requests"),
                ],
            )
            .properties(
                title=alt.TitleParams(
                    "Buckets with most standard class A operations",
                    subtitle=f"Data since {_start_str}",
                ),
                height=350,
                width=700,
            )
        )
    _fig
    return


@app.cell
def _(alt, datetime, df_top_requests, start_dt):
    _fig = None
    _curr_view = df_top_requests.loc[
        (df_top_requests["storage_class"] == "Standard")
        & (df_top_requests["operation_type"] == "B")
    ]

    if int(_curr_view["requests"].sum()) == 0:
        print("No data found for class B operations in standard buckets, skipping")
    else:
        # For the chart subtitle
        _start_str = datetime.strptime(start_dt, "%Y-%m-%dT%H:00:00Z").date()

        _fig = (
            alt.Chart(_curr_view)
            .mark_bar()
            .encode(
                alt.X(
                    "requests",
                    title="Class B operations",
                    scale=alt.Scale(type="symlog"),
                ),
                alt.Y(
                    "bucket",
                    title="Bucket name",
                    sort=alt.EncodingSortField(field="requests", order="ascending"),
                ),
                tooltip=[
                    alt.Tooltip("bucket", title="Bucket name"),
                    alt.Tooltip("requests_readable", title="Requests"),
                ],
            )
            .properties(
                title=alt.TitleParams(
                    "Buckets with most standard class B operations",
                    subtitle=f"Data since {_start_str}",
                ),
                height=350,
                width=700,
            )
        )
    _fig
    return


@app.cell
def _(alt, datetime, df_top_requests, start_dt):
    _fig = None
    _curr_view = df_top_requests.loc[
        (df_top_requests["storage_class"] == "InfrequentAccess")
        & (df_top_requests["operation_type"] == "A")
    ]

    if int(_curr_view["requests"].sum()) == 0:
        print("No data found for class A operations in infrequent access buckets, skipping")
    else:
        # For the chart subtitle
        _start_str = datetime.strptime(start_dt, "%Y-%m-%dT%H:00:00Z").date()

        _fig = (
            alt.Chart(_curr_view)
            .mark_bar()
            .encode(
                alt.X(
                    "requests",
                    title="Class A operations",
                    scale=alt.Scale(type="symlog"),
                ),
                alt.Y(
                    "bucket",
                    title="Bucket name",
                    sort=alt.EncodingSortField(field="requests", order="ascending"),
                ),
                tooltip=[
                    alt.Tooltip("bucket", title="Bucket name"),
                    alt.Tooltip("requests_readable", title="Requests"),
                ],
            )
            .properties(
                title=alt.TitleParams(
                    "Buckets with most infrequent access class A operations",
                    subtitle=f"Data since {_start_str}",
                ),
                height=350,
                width=700,
            )
        )
    _fig
    return


@app.cell
def _(alt, datetime, df_top_requests, start_dt):
    _fig = None
    _curr_view = df_top_requests.loc[
        (df_top_requests["storage_class"] == "InfrequentAccess")
        & (df_top_requests["operation_type"] == "B")
    ]

    if int(_curr_view["requests"].sum()) == 0:
        print(
            "No data found for class B operations in infrequent access buckets, skipping"
        )
    else:
        # For the chart subtitle
        _start_str = datetime.strptime(start_dt, "%Y-%m-%dT%H:00:00Z").date()

        _fig = (
            alt.Chart(_curr_view)
            .mark_bar()
            .encode(
                alt.X(
                    "requests",
                    title="Class B operations",
                    scale=alt.Scale(type="symlog"),
                ),
                alt.Y(
                    "bucket",
                    title="Bucket name",
                    sort=alt.EncodingSortField(field="requests", order="ascending"),
                ),
                tooltip=[
                    alt.Tooltip("bucket", title="Bucket name"),
                    alt.Tooltip("requests_readable", title="Requests"),
                ],
            )
            .properties(
                title=alt.TitleParams(
                    "Buckets with most infrequent access class B operations",
                    subtitle=f"Data since {_start_str}",
                ),
                height=350,
                width=700,
            )
        )
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""## Overall usage""")
    return


@app.cell
def _(
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    HOSTNAME,
    Request,
    TOP_N,
    json,
    start_dt,
    urlopen,
):
    _QUERY_STR = """
    query getR2Requests($accountTag: string,
                        $classAOpsFilter: AccountR2OperationsAdaptiveGroupsFilter_InputObject,
                        $classBOpsFilter: AccountR2OperationsAdaptiveGroupsFilter_InputObject,
                        $storageFilter: AccountR2StorageAdaptiveGroupsFilter_InputObject) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          classAOps: r2OperationsAdaptiveGroups(limit: 10000,
                                                orderBy: [datetimeHour_ASC],
                                                filter: $classAOpsFilter) {
            sum {
              requests
            }
            dimensions {
              storageClass
              datetimeHour
            }
          }
          classBOps: r2OperationsAdaptiveGroups(limit: 10000,
                                                orderBy: [datetimeHour_ASC],
                                                filter: $classBOpsFilter) {
            sum {
              requests
            }
            dimensions {
              storageClass
              datetimeHour
            }
          }
          storage: r2StorageAdaptiveGroups(limit: 10000,
                                           orderBy: [datetimeHour_ASC],
                                           filter: $storageFilter) {
            max {
              payloadSize
              metadataSize
            }
            dimensions {
              storageClass
              datetimeHour
            }
          }
        }
      }
    }
    """

    _action_status = ["success", "userError"]

    _aops_actions = [
        "ListBuckets",
        "PutBucket",
        "ListObjects",
        "PutObject",
        "CopyObject",
        "CompleteMultipartUpload",
        "CreateMultipartUpload",
        "UploadPart",
        "UploadPartCopy",
        "PutBucketEncryption",
        "ListMultipartUploads",
        "PutBucketCors",
        "PutBucketLifecycleConfiguration",
        "ListParts",
        "PutBucketStorageClass",
        "LifecycleStorageTierTransition",
    ]

    _bops_actions = [
        "HeadBucket",
        "HeadObject",
        "GetObject",
        "ReportUsageSummary",
        "GetBucketEncryption",
        "GetBucketLocation",
        "GetBucketLifecycleConfiguration",
        "GetBucketCors",
    ]

    _QUERY_VARIABLES = {
        "accountTag": CF_ACCOUNT_ID,
        "limit": TOP_N,
        "classAOpsFilter": {
            "actionType_in": _aops_actions,
            "actionStatus_in": _action_status,
            "AND": [{"datetime_geq": start_dt}],
        },
        "classBOpsFilter": {
            "actionType_in": _bops_actions,
            "actionStatus_in": _action_status,
            "AND": [{"datetime_geq": start_dt}],
        },
        "storageFilter": {"AND": [{"datetime_geq": start_dt}]},
    }

    _data = json.dumps({"query": _QUERY_STR, "variables": _QUERY_VARIABLES}).encode()
    _request = Request(f"{HOSTNAME}/client/v4/graphql",
                       headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
                       data=_data,
                       method='POST')
    _resp_raw = urlopen(_request).read()

    json_metric_data = json.loads(_resp_raw)
    return (json_metric_data,)


@app.cell
def _(json_metric_data, pd, readable_byte_vals):
    if json_metric_data["errors"] is None:
        # Store everything request related under the same dataframe, long format
        # Storage is organized into a separate dataframe
        _rows = []
        _rows_storage = []

        # Requests
        for _entry in json_metric_data["data"]["viewer"]["accounts"][0]["classAOps"]:
            _curr_row = dict(
                time=_entry["dimensions"]["datetimeHour"],
                storage_class=_entry["dimensions"]["storageClass"],
                operation_type="A",
                requests=_entry["sum"]["requests"],
            )
            _rows.append(_curr_row)

        for _entry in json_metric_data["data"]["viewer"]["accounts"][0]["classBOps"]:
            _curr_row = dict(
                time=_entry["dimensions"]["datetimeHour"],
                storage_class=_entry["dimensions"]["storageClass"],
                operation_type="B",
                requests=_entry["sum"]["requests"],
            )
            _rows.append(_curr_row)
        df_metric_requests = pd.DataFrame(_rows)
        df_metric_requests["time"] = pd.to_datetime(
            df_metric_requests["time"], format="%Y-%m-%dT%H:%M:00Z"
        ).astype("datetime64[s]")

        # Storage
        for _entry in json_metric_data["data"]["viewer"]["accounts"][0]["storage"]:
            _curr_row = dict(
                time=_entry["dimensions"]["datetimeHour"],
                storage_class=_entry["dimensions"]["storageClass"],
                payload_size=_entry["max"]["payloadSize"],
                metadata_size=_entry["max"]["metadataSize"],
            )
            _rows_storage.append(_curr_row)
        df_metric_storage = pd.DataFrame(_rows_storage)
        df_metric_storage["time"] = pd.to_datetime(
            df_metric_storage["time"], format="%Y-%m-%dT%H:%M:00Z"
        ).astype("datetime64[s]")
        df_metric_storage["payload_size_gb"] = df_metric_storage["payload_size"] / 1e9
        df_metric_storage["payload_size_readable"] = df_metric_storage[
            "payload_size"
        ].apply(lambda x: readable_byte_vals(x))

    else:
        _error_msg = "\n - ".join([el["message"] for el in json_metric_data["errors"]])
        print(f"Obtained the following errors:\n - {_error_msg}")
        raise
    return df_metric_requests, df_metric_storage


@app.cell
def _(alt, df_metric_requests):
    alt.Chart(df_metric_requests).transform_calculate(
        category="datum.storage_class + ' - Operation class ' + datum.operation_type"
    ).mark_area().encode(
        alt.X("time:T", title="Time"),
        alt.Y("requests:Q", title="Summed requests"),
        alt.Color("category:N", title="Storage type - Operation class"),
        tooltip=[
            alt.Tooltip("time", title="Time", format="%b %d, %Y %H:%M"),
            alt.Tooltip("storage_class:N", title="Storage type"),
            alt.Tooltip("operation_type:N", title="Operation class"),
            alt.Tooltip("requests", title="Requests"),
        ],
    ).properties(
        title=alt.TitleParams("R2 storage usage over time"),
        height=350,
        width=700,
    )
    return


@app.cell
def _(alt, df_metric_storage):
    alt.Chart(df_metric_storage).mark_line().encode(
        alt.X("time:T", title="Time"),
        alt.Y("payload_size_gb:Q", title="Object storage (GB)"),
        alt.Color("storage_class:N", title="Storage type"),
        tooltip=[
            alt.Tooltip("time", title="Time", format="%b %d, %Y %H:%M"),
            alt.Tooltip("storage_class:N", title="Storage type"),
            alt.Tooltip("payload_size_readable", title="Object storage"),
        ],
    ).properties(
        title=alt.TitleParams("R2 storage space over time"),
        height=350,
        width=700,
    )
    return


if __name__ == "__main__":
    app.run()

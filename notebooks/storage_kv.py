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
    import altair as alt
    from datetime import datetime, timedelta
    import pandas as pd
    return alt, datetime, pd, timedelta


@app.cell
def _(mo):
    mo.md(
        r"""
        # Workers KV analytics

        In this notebook, we will explore KV logs, where we will make use of the GraphQL API to obtain KV insights
        and rank entries by most requests, whether they are `read`, `write` and `list` requests.

        <b style='color: tomato'>Warning:</b> by default this notebook will fetch at most 500 KV entries from a given
        account, whilst other entries will be grouped into an "Other" entry. This number can be increased by
        increasing the `_MAX_PAGE_REQUESTS` variable, which dictates how many hundreds of KV name - Id pairs
        are obtained from the API.

        **Prerequisites:**<br>
         - API token (see [here](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)
        for info on how to create one);<br>
         - At least one active KV.
        """
    )
    return


@app.cell
def _(account_id, df, datetime, timedelta):
    CF_ACCOUNT_ID = account_id
    CF_API_TOKEN = df.access_token
    HOSTNAME = "https://examples-api-proxy.notebooks.cloudflare.com"  # using notebooks.cloudflare.com proxy

    # Establish time interval to last 2 weeks (trimmed to day)
    curr_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = curr_dt.strftime("%Y-%m-%dT%H:00:00Z")
    start_dt = (curr_dt - timedelta(days=14)).strftime("%Y-%m-%dT%H:00:00Z")
    return CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, end_dt, start_dt


@app.cell
def _(mo):
    mo.md(r"""## Rank of KVs with most requests""")
    return


@app.cell
def _(
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    HOSTNAME,
    Request,
    end_dt,
    json,
    start_dt,
    urlopen,
):
    _QUERY_STR = """
    query KVOperationsSummary($accountTag: string!, $filter: AccountKVOperationsAdaptiveGroupsFilter_InputObject) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          kvOperationsAdaptiveGroups(limit: 10000, filter: $filter) {
            count
            sum {
              requests
            }
            dimensions {
              actionType
              namespaceId
            }
          }
        }
      }
    }
    """

    _QUERY_VARIABLES = {
        "accountTag": CF_ACCOUNT_ID,
        "filter": {"AND": [{"datetimeHour_leq": end_dt, "datetimeHour_geq": start_dt}]},
    }

    _data = json.dumps({"query": _QUERY_STR, "variables": _QUERY_VARIABLES}).encode()
    _request = Request(f"{HOSTNAME}/client/v4/graphql",
                       headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
                       data=_data,
                       method='POST')
    _resp_raw = urlopen(_request).read()

    json_kv_data = json.loads(_resp_raw)
    return (json_kv_data,)


@app.cell
def _(mo):
    mo.md(
        r"""
        It's important to note that the query itself may not return KVs that did not register any type of request
        during our time interval.

        The query returns the KV Ids. To make results more readable, we will also perform an API call to obtain the
        name:
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
    # Before processing the GraphQL results, we fetch the KV info first so we can merge the info after processing
    # If results are incomplete, this represents the total number of pages we request
    _MAX_PAGE_REQUESTS = 5

    # Endpoint to get all KV name and Ids
    _main_call = f"{proxy}/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces"
    _params = {"per_page": 100}
    _curr_call = _main_call + '?' + urllib.parse.urlencode(_params)
    _request = Request(_curr_call, headers={"Authorization": f"Bearer {CF_API_TOKEN}"})
    _api_resp = urlopen(_request).read()
    kv_info = pd.DataFrame(json.loads(_api_resp)["result"])

    # Each API GET request can fetch at most 100 rows, if there are more pages
    # we fetch the next 4 at most, totalling 500 KVs
    _total_pages = json.loads(_api_resp)["result_info"]["total_pages"]
    if _total_pages > 1:
        _page_upper_bound = min(_total_pages, _MAX_PAGE_REQUESTS) + 1
        print(
            f"Results are incomplete, will fetch the next {min(_total_pages - 1, _MAX_PAGE_REQUESTS - 1)} pages"
        )

        for _page in range(2, _page_upper_bound):
            _params = {"per_page": 100, "page": _page}
            _curr_call = _main_call + '?' + urllib.parse.urlencode(_params)
            _request = Request(_curr_call, headers={"Authorization": f"Bearer {CF_API_TOKEN}"})
            _api_resp = urlopen(_request).read()
            _curr_results = pd.DataFrame(json.loads(_api_resp)["result"])
            kv_info = pd.concat([kv_info, _curr_results])

    # Clean columns
    kv_info = kv_info[["id", "title"]].reset_index(drop=True)
    return (kv_info,)


@app.cell
def _(json_kv_data, kv_info, pd):
    # Format results into requests per obtained kv
    _all_rows = []
    for _el in json_kv_data["data"]["viewer"]["accounts"][0][
        "kvOperationsAdaptiveGroups"
    ]:
        _curr_row = dict(
            kv=_el["dimensions"]["namespaceId"],
            action_type=_el["dimensions"]["actionType"],
            requests=_el["sum"]["requests"],
        )
        _all_rows.append(_curr_row)
    df_kv = pd.DataFrame(_all_rows)

    df_kv = df_kv.merge(kv_info, left_on="kv", right_on="id", how="left")
    df_kv = df_kv.drop(columns=["id"])

    # If an account has more than 500 KVs not all will be fetched, so we mark them as "Other"
    df_kv["title"] = df_kv["title"].fillna("Other")

    # Data is in long format, but we want shares out of total for each action type
    # That is, all "read"s sum to 100% as well as all "write"s and "list"s
    df_kv["share_of_action_requests"] = (
        df_kv["requests"]
        / df_kv.groupby("action_type")["requests"].transform("sum")
        * 100
    )
    return (df_kv,)


@app.cell
def _(df_kv):
    df_kv
    return


@app.cell
def _(alt, datetime, df_kv, end_dt, start_dt):
    # Number of entries + "Other"
    _TOP_N = 5
    # For the chart subtitle
    _start_str = datetime.strptime(start_dt, "%Y-%m-%dT%H:00:00Z").date()
    _end_str = datetime.strptime(end_dt, "%Y-%m-%dT%H:00:00Z").date()

    # KVs with most "read" requests
    _top_reads = (
        df_kv.loc[df_kv["action_type"] == "read"]
        .groupby("title")
        .agg({"requests": "sum"})
        .reset_index()
    )
    _top_reads = _top_reads.sort_values("requests", ascending=False)

    # Entries not in top 5 are grouped
    _top_reads.loc[
        ~_top_reads["title"].isin(_top_reads.head(_TOP_N)["title"]), "title"
    ] = "Other"
    _top_reads = (
        _top_reads.groupby("title")
        .agg({"requests": "sum"})
        .reset_index()
        .sort_values("requests", ascending=False)
    )

    # Trim empty entries
    _top_reads = _top_reads.loc[_top_reads["requests"] > 0]

    alt.Chart(_top_reads).mark_bar().encode(
        alt.X("requests", title='"Read" requests'),
        alt.Y(
            "title",
            title="KV name",
            sort=alt.EncodingSortField(field="requests", order="ascending"),
        ),
    ).properties(
        title=alt.TitleParams(
            'KVs with most "read" requests',
            subtitle=f"Data ranges from {_start_str} to {_end_str}",
        ),
        height=350,
        width=700,
    )
    return


@app.cell
def _(alt, datetime, df_kv, end_dt, start_dt):
    # Number of entries + "Other"
    _TOP_N = 5
    # For the chart subtitle
    _start_str = datetime.strptime(start_dt, "%Y-%m-%dT%H:00:00Z").date()
    _end_str = datetime.strptime(end_dt, "%Y-%m-%dT%H:00:00Z").date()

    # KVs with most "write" requests
    _top_write = (
        df_kv.loc[df_kv["action_type"] == "write"]
        .groupby("title")
        .agg({"requests": "sum"})
        .reset_index()
    )
    _top_write = _top_write.sort_values("requests", ascending=False)

    # Entries not in top 5 are grouped
    _top_write.loc[
        ~_top_write["title"].isin(_top_write.head(_TOP_N)["title"]), "title"
    ] = "Other"
    _top_write = (
        _top_write.groupby("title")
        .agg({"requests": "sum"})
        .reset_index()
        .sort_values("requests", ascending=False)
    )

    # Trim empty entries
    _top_write = _top_write.loc[_top_write["requests"] > 0]

    alt.Chart(_top_write).mark_bar().encode(
        alt.X("requests", title='"Write" requests'),
        alt.Y(
            "title",
            title="KV name",
            sort=alt.EncodingSortField(field="requests", order="ascending"),
        ),
    ).properties(
        title=alt.TitleParams(
            'KVs with most "write" requests',
            subtitle=f"Data ranges from {_start_str} to {_end_str}",
        ),
        height=350,
        width=700,
    )
    return


@app.cell
def _(alt, datetime, df_kv, end_dt, start_dt):
    # Number of entries + "Other"
    _TOP_N = 5
    # For the chart subtitle
    _start_str = datetime.strptime(start_dt, "%Y-%m-%dT%H:00:00Z").date()
    _end_str = datetime.strptime(end_dt, "%Y-%m-%dT%H:00:00Z").date()

    # KVs with most "read" requests
    _top_lists = (
        df_kv.loc[df_kv["action_type"] == "list"]
        .groupby("title")
        .agg({"requests": "sum"})
        .reset_index()
    )
    _top_lists = _top_lists.sort_values("requests", ascending=False)

    # Entries not in top 5 are grouped
    _top_lists.loc[
        ~_top_lists["title"].isin(_top_lists.head(_TOP_N)["title"]), "title"
    ] = "Other"
    _top_lists = (
        _top_lists.groupby("title")
        .agg({"requests": "sum"})
        .reset_index()
        .sort_values("requests", ascending=False)
    )

    # Trim empty entries
    _top_lists = _top_lists.loc[_top_lists["requests"] > 0]

    alt.Chart(_top_lists).mark_bar().encode(
        alt.X("requests", title='"Write" requests'),
        alt.Y(
            "title",
            title="KV name",
            sort=alt.EncodingSortField(field="requests", order="ascending"),
        ),
    ).properties(
        title=alt.TitleParams(
            'KVs with most "list" requests',
            subtitle=f"Data ranges from {_start_str} to {_end_str}",
        ),
        height=350,
        width=700,
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## KV request usage over time

        This trend does not concern the KVs themselves, merely their aggregated request counts over time.

        <b style='color: tomato'>Warning:</b> Due to incomplete date aggregregations, the first and last dates on the
        final charts may present lower numbers.
        """
    )
    return


@app.cell
def _(
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    HOSTNAME,
    Request,
    end_dt,
    json,
    start_dt,
    urlopen,
):
    _QUERY_STR = """
    query KVOperationsTime($accountTag: string!, $filter: AccountKVOperationsAdaptiveGroupsFilter_InputObject) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          kvOperationsAdaptiveGroups(limit: 10000, filter: $filter) {
            count
            sum {
              requests
            }
            dimensions {
              actionType
              date
            }
          }
        }
      }
    }
    """

    _QUERY_VARIABLES = {
        "accountTag": CF_ACCOUNT_ID,
        "filter": {"AND": [{"datetimeHour_leq": end_dt, "datetimeHour_geq": start_dt}]},
    }

    _data = json.dumps({"query": _QUERY_STR, "variables": _QUERY_VARIABLES}).encode()
    _request = Request(f"{HOSTNAME}/client/v4/graphql",
                       headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
                       data=_data,
                       method='POST')
    _resp_raw = urlopen(_request).read()

    json_kv_time_data = json.loads(_resp_raw)
    return (json_kv_time_data,)


@app.cell
def _(json_kv_time_data, pd):
    # Format results into hourly metrics per obtained worker
    _all_rows = []
    for _el in json_kv_time_data["data"]["viewer"]["accounts"][0][
        "kvOperationsAdaptiveGroups"
    ]:
        _curr_row = dict(
            time=_el["dimensions"]["date"],
            action_type=_el["dimensions"]["actionType"],
            requests=_el["sum"]["requests"],
        )
        _all_rows.append(_curr_row)
    df_time = pd.DataFrame(_all_rows)
    df_time["time"] = pd.to_datetime(df_time["time"])
    df_time = df_time.sort_values("time")
    return (df_time,)


@app.cell
def _(alt, df_time):
    alt.Chart(df_time).mark_line().encode(
        alt.X("time", title="Date"),
        alt.Y("requests", title="Daily requests"),
        alt.Color("action_type", title="Operation type"),
    ).properties(title="KV requests over time", height=400, width=700)
    return


if __name__ == "__main__":
    app.run()

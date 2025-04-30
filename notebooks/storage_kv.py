import marimo

__generated_with = "0.13.2"

app = marimo.App(
    width="full",
    auto_download=["ipynb", "html"],
    app_title="Cloudflare Notebook",
)

####################
# Helper Functions #
####################

# Helper function stubs
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


###############
# Login Cells #
###############


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


##################
# Notebook Cells #
##################


@app.cell
def _():
    import altair as alt
    from datetime import datetime, timedelta
    import json
    import pandas as pd

    return alt, datetime, json, pd, timedelta


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
def _(account_id, token, proxy, datetime, timedelta):
    CF_ACCOUNT_ID = account_id  # After login, selected from list above
    CF_API_TOKEN = token  # Or a custom token from dash.cloudflare.com
    HOSTNAME = proxy  # using notebooks.cloudflare.com proxy

    # Establish time interval to last 2 weeks (trimmed to day)
    curr_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = curr_dt.strftime("%Y-%m-%dT%H:00:00Z")
    start_dt = (curr_dt - timedelta(days=14)).strftime("%Y-%m-%dT%H:00:00Z")
    return CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, curr_dt, end_dt, start_dt


@app.cell
def _(mo):
    mo.md(r"""## Rank of KVs with most requests""")
    return


@app.cell
def _(
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    HOSTNAME,
    end_dt,
    json,
    requests,
    start_dt,
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

    _resp_raw = requests.post(
        f"{HOSTNAME}/client/v4/graphql",
        headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
        json={"query": _QUERY_STR, "variables": _QUERY_VARIABLES},
    )

    json_kv_data = json.loads(_resp_raw.text)
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
def _(CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, json, pd, requests):
    # Before processing the GraphQL results, we fetch the KV info first so we can merge the info after processing
    # If results are incomplete, this represents the total number of pages we request
    _MAX_PAGE_REQUESTS = 5

    # Endpoint to get all KV name and Ids
    main_call = f"{HOSTNAME}/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces"
    _api_resp = requests.get(
        main_call,
        params={"per_page": 100},
        headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
    ).text
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
            _api_resp = requests.get(
                main_call,
                params={"per_page": 100, "page": _page},
                headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
            ).text
            _curr_results = pd.DataFrame(json.loads(_api_resp)["result"])
            kv_info = pd.concat([kv_info, _curr_results])

    # Clean columns
    kv_info = kv_info[["id", "title"]].reset_index(drop=True)
    return kv_info, main_call


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
    end_dt,
    json,
    requests,
    start_dt,
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

    _resp_raw = requests.post(
        f"{HOSTNAME}/client/v4/graphql",
        headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
        json={"query": _QUERY_STR, "variables": _QUERY_VARIABLES},
    )

    json_kv_time_data = json.loads(_resp_raw.text)
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

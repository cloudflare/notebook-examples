# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "anywidget",
#     "marimo",
#     "moutils",
#     "nbformat",
#     "requests",
# ]
# ///
import marimo

__generated_with = "0.14.11"
app = marimo.App(width="full", app_title="Cloudflare Notebook", auto_download=["ipynb", "html"])


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
    return PKCEFlow, Request, debug, get_accounts, is_wasm, json, mo, moutils, proxy, requests, sys, urllib, urlopen, warnings


@app.cell(hide_code=True)
def _(PKCEFlow):
    # Login to Cloudflare - click to view code
    df = PKCEFlow(provider="cloudflare", use_new_tab=True)
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
def _(account_id, mo, proxy, df):
    mo.stop(df.access_token is None or account_id is None, 'Please retrieve a token first and select an account above')

    import altair as alt
    from datetime import datetime, timedelta
    import pandas as pd

    CF_ACCOUNT_ID = account_id  # After login, selected from list above
    CF_API_TOKEN = df.access_token  # Or a custom token from dash.cloudflare.com
    HOSTNAME = proxy
    return CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, alt, datetime, pd, timedelta


@app.cell
def _(mo):
    mo.md(
        r"""
        # Workers use case

        In this notebook, we will show a simple use case involving workers.

        **Prerequisites:**<br>
         - API token (see [here](https://developers.cloudflare.com/r2/api/s3/tokens/) for info on how
         to create one);<br>
         - at least one active worker.
        """
    )
    return


@app.cell
def _(datetime, timedelta):
    # Establish time interval to last 24 hours (rounded to hour)
    curr_dt = datetime.now().replace(minute=0, second=0, microsecond=0)
    end_dt = curr_dt.strftime("%Y-%m-%dT%H:00:00Z")
    start_dt = (curr_dt - timedelta(days=1)).strftime("%Y-%m-%dT%H:00:00Z")
    return end_dt, start_dt


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
    query getServiceRequestsQuery($accountTag: string, $filter: ZoneWorkersRequestsFilter_InputObject) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          workersInvocationsAdaptive(limit: 10000, filter: $filter) {
            sum {
              errors
              clientDisconnects
              requests
              subrequests
              responseBodySize
            }
            quantiles {
              cpuTimeP50
              cpuTimeP75
              cpuTimeP99
              cpuTimeP999
              wallTimeP50
              wallTimeP75
              wallTimeP99
              wallTimeP999
              durationP50
              durationP75
              durationP99
              durationP999
              responseBodySizeP50
              responseBodySizeP75
              responseBodySizeP99
              responseBodySizeP999
            }
            dimensions {
              scriptName
              datetimeHour
              status
              scriptVersion
            }
          }
          workersSubrequestsAdaptiveGroups(limit: 10000, filter: $filter) {
            sum {
              requestBodySizeUncached
              subrequests
            }
            dimensions {
              usageModel
              datetimeHour
              cacheStatus
              scriptVersion
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

    json_worker_data = json.loads(_resp_raw)
    return (json_worker_data,)


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Ranking workers by multiple metrics

        Here, we will show the top workers by 4 metrics also available in dash: requests, errors,
        disconnects and median CPU time.
        Results are returned on a hourly basis, so here is how these metrics are aggregated:<br>
         - requests are summed;<br>
         - dash combines both errors and disconnects, here we show them standalone, summed as well;<br>
         - cpu time is averaged out of all hourly 50th percentiles.
        """
    )
    return


@app.cell
def _(json_worker_data, pd):
    # Format results into hourly metrics per obtained worker
    _all_rows = []
    for el in json_worker_data["data"]["viewer"]["accounts"][0][
        "workersInvocationsAdaptive"
    ]:
        _curr_row = dict(
            time=el["dimensions"]["datetimeHour"],
            worker=el["dimensions"]["scriptName"],
            requests=el["sum"]["requests"],
            errors=el["sum"]["errors"],
            disconnects=el["sum"]["clientDisconnects"],
            subrequests=el["sum"]["subrequests"],
            cpu_time=el["quantiles"]["cpuTimeP50"],
        )
        _all_rows.append(_curr_row)
    df_worker = pd.DataFrame(_all_rows)

    # For top entries bar chart
    df_worker_agg = (
        df_worker.groupby("worker")
        .agg(
            {
                "requests": "sum",
                "errors": "sum",
                "disconnects": "sum",
                "cpu_time": "mean",
            }
        )
        .reset_index()
    )
    df_worker_agg["cpu_time"] /= 1000
    return (df_worker_agg,)


@app.cell
def _(alt, df_worker_agg):
    _TOP_N = 5

    # To prevent large query results, we only store the top 5 for comparison of top entries

    # Workers with most requests
    _top_requests = df_worker_agg.sort_values("requests", ascending=False).head(_TOP_N)
    TOP_REQUESTS_WORKERS = list(_top_requests.head(5)["worker"].values)
    _requests_chart = (
        alt.Chart(_top_requests)
        .mark_bar()
        .encode(
            alt.X("requests:Q", title="Requests"),
            alt.Y(
                "worker:N",
                sort=alt.EncodingSortField(field="requests", order="descending"),
            ),
        )
        .properties(height=220, width=300)
    )

    # Workers with most errors
    _top_errors = df_worker_agg.sort_values("errors", ascending=False).head(_TOP_N)
    TOP_ERRORS_WORKERS = list(_top_errors.head(5)["worker"].values)
    _errors_chart = (
        alt.Chart(_top_errors)
        .mark_bar()
        .encode(
            alt.X("errors:Q", title="Errors"),
            alt.Y(
                "worker:N",
                sort=alt.EncodingSortField(field="errors", order="descending"),
            ),
        )
        .properties(height=220, width=300)
    )

    # Workers with most disconnects
    _top_disconnects = df_worker_agg.sort_values("disconnects", ascending=False).head(
        _TOP_N
    )
    TOP_DISCONNECTS_WORKERS = list(_top_disconnects.head(5)["worker"].values)
    _disconnects_chart = (
        alt.Chart(_top_disconnects)
        .mark_bar()
        .encode(
            alt.X("disconnects:Q", title="Disconnects"),
            alt.Y(
                "worker:N",
                sort=alt.EncodingSortField(field="disconnects", order="descending"),
            ),
        )
        .properties(height=220, width=300)
    )

    # Workers with highest median CPU time
    _top_cpu = df_worker_agg.sort_values("cpu_time", ascending=False).head(_TOP_N)
    TOP_CPU_TIME_WORKERS = list(_top_cpu.head(5)["worker"].values)
    _cpu_chart = (
        alt.Chart(_top_cpu)
        .mark_bar()
        .encode(
            alt.X("cpu_time:Q", title="CPU time (ms)"),
            alt.Y(
                "worker:N",
                sort=alt.EncodingSortField(field="cpu_time", order="descending"),
            ),
        )
        .properties(height=220, width=300)
    )

    (_requests_chart | _errors_chart) & (_disconnects_chart | _cpu_chart)
    return (
        TOP_CPU_TIME_WORKERS,
        TOP_DISCONNECTS_WORKERS,
        TOP_ERRORS_WORKERS,
        TOP_REQUESTS_WORKERS,
    )


@app.cell
def _(mo):
    mo.md(r"""Raw data (includes all entries from GraphQL results):""")
    return


@app.cell
def _(df_worker_agg):
    df_worker_agg
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        Now, what we are interested in is comparing side by side these top entries for each metric.

        <span style="color: tomato"><b>Warning:</b> both the start and end of the obtained timeseries may have
        sharp drops due to aggregations on incomplete periods of time.<span>
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""### Workers with the most requests""")
    return


@app.cell
def _(
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    HOSTNAME,
    Request,
    TOP_REQUESTS_WORKERS,
    end_dt,
    json,
    start_dt,
    urlopen,
):
    _QUERY_STR = """
    query GetWorkerRequests($accountTag: string!,
                            $datetimeStart: Time,
                            $datetimeEnd: Time,
                            $scriptNames: [string]) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          workersInvocationsAdaptive(limit: 10000, filter: {
              scriptName_in: $scriptNames,
              datetime_geq: $datetimeStart,
              datetime_leq: $datetimeEnd},
            orderBy: [datetimeFifteenMinutes_ASC]) {
            sum {
              requests
            }
            dimensions {
              datetimeFifteenMinutes
              scriptName
            }
          }
        }
      }
    }
    """

    _QUERY_VARIABLES = {
        "accountTag": CF_ACCOUNT_ID,
        "datetimeStart": start_dt,
        "datetimeEnd": end_dt,
        "scriptNames": TOP_REQUESTS_WORKERS,
    }

    _data = json.dumps({"query": _QUERY_STR, "variables": _QUERY_VARIABLES}).encode()
    _request = Request(f"{HOSTNAME}/client/v4/graphql",
                       headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
                       data=_data,
                       method='POST')
    _resp_raw = urlopen(_request).read()

    json_request_data = json.loads(_resp_raw)
    return (json_request_data,)


@app.cell
def _(json_request_data, pd):
    # Format data into wide format
    _all_rows = []
    for _el in json_request_data["data"]["viewer"]["accounts"][0][
        "workersInvocationsAdaptive"
    ]:
        _curr_row = dict(
            time=_el["dimensions"]["datetimeFifteenMinutes"],
            worker=_el["dimensions"]["scriptName"],
            requests=_el["sum"]["requests"],
        )
        _all_rows.append(_curr_row)
    df_workers_requests = pd.DataFrame(_all_rows)
    df_workers_requests["time"] = pd.to_datetime(
        df_workers_requests["time"], format="%Y-%m-%dT%H:%M:00Z"
    ).astype("datetime64[s]")
    df_workers_requests = df_workers_requests.sort_values(["time", "worker"])
    return (df_workers_requests,)


@app.cell
def _(alt, df_workers_requests):
    alt.Chart(df_workers_requests).mark_line().encode(
        alt.X("time", title="Time (UTC)"),
        alt.Y("requests", title="Requests"),
        alt.Color("worker", title="Worker"),
    ).properties(
        title="Comparison of workers with most requests", height=350, width=700
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ### Workers with the most errors and disconnects

        The bellow code fetches errors and disconnects for both the top workers with most errors,
        as well as the top workers with the most disconnects.
        """
    )
    return


@app.cell
def _(
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    HOSTNAME,
    Request,
    TOP_DISCONNECTS_WORKERS,
    TOP_ERRORS_WORKERS,
    end_dt,
    json,
    start_dt,
    urlopen,
):
    _QUERY_STR = """
    query GetWorkerRequests($accountTag: string!,
                            $datetimeStart: Time,
                            $datetimeEnd: Time,
                            $scriptNames: [string]) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          workersInvocationsAdaptive(limit: 10000, filter: {
              scriptName_in: $scriptNames,
              status_neq: "success",
              datetime_geq: $datetimeStart,
              datetime_leq: $datetimeEnd
          }, orderBy: [datetimeFifteenMinutes_ASC]) {
            sum {
              errors
              clientDisconnects
            }
            dimensions {
              datetimeFifteenMinutes
              scriptName
            }
          }
        }
      }
    }
    """

    _QUERY_VARIABLES = {
        "accountTag": CF_ACCOUNT_ID,
        "datetimeStart": start_dt,
        "datetimeEnd": end_dt,
        # Unique set of workers with most errors and disconnects
        "scriptNames": list(set(TOP_DISCONNECTS_WORKERS + TOP_ERRORS_WORKERS)),
    }

    _data = json.dumps({"query": _QUERY_STR, "variables": _QUERY_VARIABLES}).encode()
    _request = Request(f"{HOSTNAME}/client/v4/graphql",
                       headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
                       data=_data,
                       method='POST')
    _resp_raw = urlopen(_request).read()

    json_error_data = json.loads(_resp_raw)
    return (json_error_data,)


@app.cell
def _(json_error_data, pd):
    # Format data into wide format
    _all_rows = []
    for _el in json_error_data["data"]["viewer"]["accounts"][0][
        "workersInvocationsAdaptive"
    ]:
        _curr_row = dict(
            time=_el["dimensions"]["datetimeFifteenMinutes"],
            worker=_el["dimensions"]["scriptName"],
            errors=_el["sum"]["errors"],
            disconnects=_el["sum"]["clientDisconnects"],
        )
        _all_rows.append(_curr_row)
    df_workers_errors = pd.DataFrame(_all_rows)
    df_workers_errors["time"] = pd.to_datetime(
        df_workers_errors["time"], format="%Y-%m-%dT%H:%M:00Z"
    ).astype("datetime64[s]")
    df_workers_errors = df_workers_errors.sort_values(["time", "worker"])
    return (df_workers_errors,)


@app.cell
def _(TOP_ERRORS_WORKERS, alt, df_workers_errors):
    _df_errors_only = df_workers_errors.loc[
        df_workers_errors["worker"].isin(TOP_ERRORS_WORKERS)
    ]
    alt.Chart(_df_errors_only).mark_line().encode(
        alt.X("time", title="Time (UTC)"),
        alt.Y("errors", title="Errors"),
        alt.Color("worker", title="Worker"),
    ).properties(title="Comparison of workers with most errors", height=350, width=700)
    return


@app.cell
def _(TOP_DISCONNECTS_WORKERS, alt, df_workers_errors):
    _df_errors_only = df_workers_errors.loc[
        df_workers_errors["worker"].isin(TOP_DISCONNECTS_WORKERS)
    ]
    alt.Chart(_df_errors_only).mark_line().encode(
        alt.X("time", title="Time (UTC)"),
        alt.Y("disconnects", title="Disconnects"),
        alt.Color("worker", title="Worker"),
    ).properties(
        title="Comparison of workers with most disconnects", height=350, width=700
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ### Workers with the highest average CPU times

        Note: This query only fetches the 50th quantile of CPU times, but other quantiles, such as `cpuTimeP90`,
        `cpuTimeP99` and `cpuTimeP999` can also be queried by adding these columns in the `quantiles {}` field.
        """
    )
    return


@app.cell
def _(
    CF_ACCOUNT_ID,
    CF_API_TOKEN,
    HOSTNAME,
    Request,
    TOP_CPU_TIME_WORKERS,
    end_dt,
    json,
    start_dt,
    urlopen,
):
    _QUERY_STR = """
    query GetWorkerCPUTime($accountTag: string!,
                           $datetimeStart: Time,
                           $datetimeEnd: Time,
                           $scriptNames: [string]) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          workersInvocationsAdaptive(limit: 10000, filter: {
              scriptName_in: $scriptNames,
              datetime_geq: $datetimeStart,
              datetime_leq: $datetimeEnd
              }, orderBy: [datetimeFifteenMinutes_ASC]) {
            quantiles {
              cpuTimeP50
            }
            dimensions {
              datetimeFifteenMinutes
              scriptName
            }
          }
        }
      }
    }
    """

    _QUERY_VARIABLES = {
        "accountTag": CF_ACCOUNT_ID,
        "datetimeStart": start_dt,
        "datetimeEnd": end_dt,
        "scriptNames": TOP_CPU_TIME_WORKERS,
    }

    _data = json.dumps({"query": _QUERY_STR, "variables": _QUERY_VARIABLES}).encode()
    _request = Request(f"{HOSTNAME}/client/v4/graphql",
                       headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
                       data=_data,
                       method='POST')
    _resp_raw = urlopen(_request).read()

    json_cpu_data = json.loads(_resp_raw)
    return (json_cpu_data,)


@app.cell
def _(json_cpu_data, pd):
    # Format data into wide format
    _all_rows = []
    for _el in json_cpu_data["data"]["viewer"]["accounts"][0][
        "workersInvocationsAdaptive"
    ]:
        _curr_row = dict(
            time=_el["dimensions"]["datetimeFifteenMinutes"],
            worker=_el["dimensions"]["scriptName"],
            cpuTimeP50=_el["quantiles"]["cpuTimeP50"],
        )
        _all_rows.append(_curr_row)
    df_workers_cputime = pd.DataFrame(_all_rows)
    df_workers_cputime["time"] = pd.to_datetime(
        df_workers_cputime["time"], format="%Y-%m-%dT%H:%M:00Z"
    ).astype("datetime64[s]")
    df_workers_cputime = df_workers_cputime.sort_values(["time", "worker"])
    return (df_workers_cputime,)


@app.cell
def _(alt, df_workers_cputime):
    alt.Chart(df_workers_cputime).mark_line().encode(
        alt.X("time", title="Time (UTC)"),
        alt.Y("cpuTimeP50", title="CPU time (P50)"),
        alt.Color("worker", title="Worker"),
    ).properties(
        title="Comparison of workers with highest CPU times", height=350, width=700
    )
    return


if __name__ == "__main__":
    app.run()

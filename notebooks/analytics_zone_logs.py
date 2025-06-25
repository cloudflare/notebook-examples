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
    return df


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
    from datetime import datetime, timedelta
    import pandas as pd

    CF_ACCOUNT_ID = account_id
    CF_API_TOKEN = token  # or a custom token from dash.cloudflare.com
    HOSTNAME = proxy
    return CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, alt, datetime, pd, timedelta


@app.cell
def _(mo):
    mo.md(
        """
        # Zone logs use case
        In this notebook, we will show a simple use case involving account zone information and traffic logs.

        **Prerequisites:**<br>
         - API token (see [here](https://developers.cloudflare.com/r2/api/s3/tokens/)
          for info on how to create one);<br>
         - At least one active zone.
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
    urllib,
    urlopen,
):
    # Endpoint to get list of zones belonging to the selected account
    # Warning: this will fetch at most 50 zones
    _main_call = f"{HOSTNAME}/client/v4/zones"
    _params = {"per_page": 50, "account.id": CF_ACCOUNT_ID}
    _api_call = _main_call + '?' + urllib.parse.urlencode(_params)
    _request = Request(_api_call, headers={"Authorization": f"Bearer {CF_API_TOKEN}"})
    _api_resp = urlopen(_request).read()
    _res_raw = pd.DataFrame(json.loads(_api_resp)["result"])

    # Clean columns
    account_zones = _res_raw[
        ["id", "name", "status", "paused", "plan", "modified_on"]
    ].copy()
    account_zones["plan_name"] = account_zones["plan"].apply(lambda x: x["name"])
    account_zones = account_zones.drop(columns=["plan"])[
        ["name", "id", "plan_name", "status", "paused", "modified_on"]
    ]
    account_zones = account_zones.sort_values("name")
    return (account_zones,)


@app.cell
def _(account_zones):
    account_zones
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Fetch zone logs

        Here we will perform a GraphQL query used in the Cloudflare dashboard obtained using
        [browser developer tools](
        https://developers.cloudflare.com/analytics/graphql-api/tutorials/capture-graphql-queries-from-dashboard/).
        These [differ](https://developers.cloudflare.com/analytics/graphql-api/) from traditional API endpoints in
        the sense that data is obtained from a POST request to a single endpoint:
        `https://developers.cloudflare.com/analytics/graphql-api/`.
        The query as well as related variables are provided in the json body.
        """
    )
    return


@app.cell
def _(account_zones, datetime, timedelta):
    # Choose zone tag (id) to obtain data from, using the table above
    zone_tag = account_zones["id"][0]
    # Demo example: First zone from the list

    # Establish time interval to last 24 hours
    curr_dt = datetime.now().replace(second=0, microsecond=0)
    end_dt = curr_dt.strftime("%Y-%m-%dT%H:%M:00Z")
    start_dt = (curr_dt - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:00Z")
    return end_dt, start_dt, zone_tag


@app.cell
def _(
    CF_API_TOKEN,
    HOSTNAME,
    Request,
    end_dt,
    json,
    start_dt,
    urlopen,
    zone_tag,
):
    _QUERY_STR = """
    query GetZoneAnalytics($zoneTag: string, $since: string, $until: string) {
      viewer {
        zones(filter: {zoneTag: $zoneTag}) {
          totals: httpRequests1hGroups(limit: 10000, filter: {datetime_geq: $since, datetime_lt: $until}) {
            uniq {
              uniques
            }
          }
          zones: httpRequests1hGroups(orderBy: [datetime_ASC], limit: 10000,
                                      filter: {datetime_geq: $since, datetime_lt: $until}) {
            dimensions {
              timeslot: datetime
            }
            uniq {
              uniques
            }
            sum {
              browserMap {
                pageViews
                key: uaBrowserFamily
              }
              bytes
              cachedBytes
              cachedRequests
              contentTypeMap {
                bytes
                requests
                key: edgeResponseContentTypeName
              }
              clientSSLMap {
                requests
                key: clientSSLProtocol
              }
              countryMap {
                bytes
                requests
                threats
                key: clientCountryName
              }
              encryptedBytes
              encryptedRequests
              ipClassMap {
                requests
                key: ipType
              }
              pageViews
              requests
              responseStatusMap {
                requests
                key: edgeResponseStatus
              }
              threats
              threatPathingMap {
                requests
                key: threatPathingName
              }
            }
          }
        }
      }
    }
    """
    _QUERY_VARIABLES = {"zoneTag": zone_tag, "since": start_dt, "until": end_dt}

    _data = json.dumps({"query": _QUERY_STR, "variables": _QUERY_VARIABLES}).encode()
    _request = Request(f"{HOSTNAME}/client/v4/graphql",
                       headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
                       data=_data,
                       method='POST')
    _resp_raw = urlopen(_request).read()

    json_analytics = json.loads(_resp_raw)
    return (json_analytics,)


@app.cell
def _(mo):
    mo.md(
        """
        The query, if successful, will return a lot of data at once, including page views and requests,
        as well as some metrics such as the browser associated with the request, the response code, among others.

        Here, we will focus on a single metric: requests by common response codes. The `json_analytics` object
        will have other types of data for further analysis, but it needs to be formated to a pandas `DataFrame` first.
        """
    )
    return


@app.cell
def _(mo):
    mo.md("""### Distribution of HTTP response codes""")
    return


@app.cell
def _(json_analytics, pd):
    df_status_code = pd.DataFrame()

    # Format response code data into a DataFrame with [time - typename - response code - requests]
    for j in range(len(json_analytics["data"]["viewer"]["zones"][0]["zones"])):
        _temp_row_ts = json_analytics["data"]["viewer"]["zones"][0]["zones"][j][
            "dimensions"
        ]["timeslot"]
        _temp_row = pd.DataFrame(
            json_analytics["data"]["viewer"]["zones"][0]["zones"][j]["sum"][
                "responseStatusMap"
            ]
        )
        _temp_row["time"] = _temp_row_ts
        df_status_code = pd.concat([df_status_code, _temp_row])

    df_status_code["time"] = pd.to_datetime(
        df_status_code["time"], format="%Y-%m-%dT%H:%M:00Z"
    ).astype("datetime64[s]")

    df_status_code = (
        df_status_code.groupby(["time", "key"]).agg({"requests": "sum"}).reset_index()
    )
    # For now, we do not want status codes to be interpreted as integers
    # (tends to affect charts)
    df_status_code["key"] = df_status_code["key"].astype(str)
    return (df_status_code,)


@app.cell
def _(df_status_code):
    # Select number of status codes to show in summary
    TOP_STATUS_CODES = 10

    df_status_summary = (
        df_status_code.groupby("key").agg({"requests": "sum"}).reset_index()
    )

    # Rename non-top entries into the "Other" label
    df_status_summary.loc[
        df_status_summary["requests"].rank(ascending=False) > TOP_STATUS_CODES, "key"
    ] = "Other"

    # The "Other" label must be aggregated
    df_status_summary = (
        df_status_summary.groupby("key")
        .agg({"requests": "sum"})
        .reset_index()
        .sort_values("requests", ascending=False)
        .reset_index(drop=True)
    )

    # Percentage out of all requests
    df_status_summary["share_requests"] = (
        df_status_summary["requests"] / df_status_summary["requests"].sum() * 100
    )
    return (df_status_summary,)


@app.cell
def _(df_status_summary):
    df_status_summary
    return


@app.cell
def _(alt, df_status_summary):
    alt.Chart(
        df_status_summary, title="Requests by HTTP status code"
    ).mark_bar().encode(
        alt.X("share_requests:Q", title="Share of requests").axis(
            labelExpr='datum.value + "%"'
        ),
        alt.Y(
            "key:O",
            title="HTTP status code",
            sort=alt.EncodingSortField(field="share_requests", order="ascending"),
        ),
    ).properties(
        height=400, width=500
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        This last section of the notebook will perform a separate query that digs deeper into a specified status code.
        Perhaps in the results above, a non 2XX was higher than expected. Which hosts were being requested? Which paths?

        To achieve this, we will extract the GraphQL query which provides these statistics in the Cloudflare dashboard
        using the aforementioned method involving browser developer tools. We saw in the previous query that the status
        code variable is `edgeResponseStatus`, so we will have to add a filter in the GraphQL variable dictionary:
        `"edgeResponseStatus": {HTTP_STATUS_CODE}`

        where `{HTTP_STATUS_CODE}` represents our chosen HTTP response status code (200 for `OK`, 403 for `Forbidden`,
        429 for `Too Many Requests`, etc).
        """
    )
    return


@app.cell
def _(mo):
    mo.md("""### HTTP status code trends""")
    return


@app.cell
def _():
    # Choose the status code as an integer
    HTTP_STATUS_CODE = 403
    return (HTTP_STATUS_CODE,)


@app.cell
def _(
    CF_API_TOKEN,
    HOSTNAME,
    HTTP_STATUS_CODE,
    Request,
    end_dt,
    json,
    start_dt,
    urlopen,
    zone_tag,
):
    _QUERY_STR = """
    query GetZoneTopNs {
      viewer {
        scope: zones(filter: {zoneTag: $zoneTag}) {
          total: httpRequestsAdaptiveGroups(filter: $filter, limit: 1) {
            count
            sum {
              edgeResponseBytes
              visits
            }
          }
          topPaths: httpRequestsAdaptiveGroups(filter: $filter, limit: 15, orderBy: [$order]) {
            count
            avg {
              sampleInterval
            }
            sum {
              edgeResponseBytes
              visits
            }
            dimensions {
              metric: clientRequestPath
            }
          }
          topHosts: httpRequestsAdaptiveGroups(filter: $filter, limit: 15, orderBy: [$order]) {
            count
            avg {
              sampleInterval
            }
            sum {
              edgeResponseBytes
              visits
            }
            dimensions {
              metric: clientRequestHTTPHost
            }
          }
          topBrowsers: httpRequestsAdaptiveGroups(filter: $filter, limit: 15, orderBy: [$order]) {
            count
            avg {
              sampleInterval
            }
            sum {
              edgeResponseBytes
              visits
            }
            dimensions {
              metric: userAgentBrowser
            }
          }
          topEdgeStatusCodes: httpRequestsAdaptiveGroups(filter: $filter, limit: 15, orderBy: [$order]) {
            count
            avg {
              sampleInterval
            }
            sum {
              edgeResponseBytes
              visits
            }
            dimensions {
              metric: edgeResponseStatus
            }
          }
          countries: httpRequestsAdaptiveGroups(filter: $filter, limit: 200, orderBy: [$order]) {
            count
            avg {
              sampleInterval
            }
            sum {
              edgeResponseBytes
              visits
            }
            dimensions {
              metric: clientCountryName
            }
          }
          topUserAgents: httpRequestsAdaptiveGroups(filter: $filter, limit: 15, orderBy: [$order]) {
            count
            avg {
              sampleInterval
            }
            sum {
              edgeResponseBytes
              visits
            }
            dimensions {
              metric: userAgent
            }
          }
        }
      }
    }
    """
    _QUERY_VARIABLES = {
        "zoneTag": zone_tag,
        "filter": {
            "AND": [
                {"datetime_geq": start_dt, "datetime_leq": end_dt},
                {"requestSource": "eyeball"},
                {"edgeResponseStatus": HTTP_STATUS_CODE},
            ]
        },
        "order": "count_DESC",
    }

    _data = json.dumps({"query": _QUERY_STR, "variables": _QUERY_VARIABLES}).encode()
    _request = Request(f"{HOSTNAME}/client/v4/graphql",
                       headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
                       data=_data,
                       method='POST')
    _resp_raw = urlopen(_request).read()

    json_dict_filtered = json.loads(_resp_raw)
    return (json_dict_filtered,)


@app.cell
def _(pd):
    # Obtain top n of a given request attribute in a pandas DataFrame
    # Attribute and counts will be in the "entry" and "count" values, respectively
    def top_n_from_json(json_dict, attribute):
        _all_rows = []
        for el in json_dict["data"]["viewer"]["scope"][0][attribute]:
            _temp_row = {"entry": el["dimensions"]["metric"], "count": el["count"]}
            _all_rows.append(_temp_row)
        return pd.DataFrame(_all_rows)

    return (top_n_from_json,)


@app.cell
def _(mo):
    mo.md(
        r"""
        Most of these attributes tend to be too large to fit into chart labels, so we will display
        them as tables instead:
        """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""#### Top countries""")
    return


@app.cell
def _(json_dict_filtered, top_n_from_json):
    top_n_from_json(json_dict_filtered, "countries")
    return


@app.cell
def _(mo):
    mo.md(r"""#### Top hosts""")
    return


@app.cell
def _(json_dict_filtered, top_n_from_json):
    top_n_from_json(json_dict_filtered, "topHosts")
    return


@app.cell
def _(mo):
    mo.md(r"""#### Top paths""")
    return


@app.cell
def _(json_dict_filtered, top_n_from_json):
    top_n_from_json(json_dict_filtered, "topPaths")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Going further

        This notebook barely scratches the surface of zone-level traffic analytics, as there are a plethora of other
        statistics that can be obtained from GraphQL.<br>
        Some examples include diving deeper into API related requests and check which requests are being rate limited,
        check if there is content which is largely uncached, perform anomaly detection on traffic by country, and much
        more.
        """
    )
    return


if __name__ == "__main__":
    app.run()

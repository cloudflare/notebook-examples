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

# Helper function stubs
get_accounts = None


@app.cell(hide_code=True)
async def _():
    # Helper Functions - click to view code
    import js
    import requests  # required for moutils.oauth

    origin = js.eval("self.location?.origin")
    proxy = "https://api-proxy.notebooks.cloudflare.com"

    async def get_accounts(token):
        # Example API request to list available Cloudflare accounts
        res = requests.get(
            f"{proxy}/client/v4/accounts",
            headers={"Authorization": f"Bearer {token}", },
        ).json()
        return res.get("result", []) or []

    return origin, proxy


###############
# Login Cells #
###############
@app.cell(hide_code=True)
def _(origin):
    # Login cell - click to view code
    from moutils.oauth import PKCEFlow

    df = PKCEFlow(
        provider="cloudflare",
        client_id="ec85d9cd-ff12-4d96-a376-432dbcf0bbfc",
        logout_url=f"{origin}/oauth2/revoke",
        redirect_uri=f"{origin}/oauth/callback",
        token_url=f"{origin}/oauth2/token",
    )
    df
    return PKCEFlow, df, None, None


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
    import json
    import pandas as pd
    import warnings

    # Process robots.txt content
    from urllib.robotparser import RobotFileParser
    from urllib.parse import unquote

    CF_API_TOKEN = token
    HOSTNAME = proxy
    return (
        CF_API_TOKEN,
        HOSTNAME,
        RobotFileParser,
        alt,
        datetime,
        json,
        pd,
        timedelta,
        unquote,
        warnings,
    )


@app.cell
def _(mo):
    mo.md(
        r"""
        # AI Audit

        In this notebook, we will use AI audit data to check for most common `robots.txt` violations.

        **Prerequisites:**<br>
         - API token (see [here](https://developers.cloudflare.com/r2/api/s3/tokens/) for info on how
         to create one);<br>
         - at least one active zone with a `robots.txt` file.

        <span style='color:tomato'>Note:</span> when making a GET request to the specified zone's robots.txt page,
        it is required that the domain returns the CORS `Access-Control-Allow-Origin` header.
        """
    )
    return


@app.cell
def _():
    # List of AI user agents to filter traffic by
    # Filtering is done by checking if any of these strings appear anywhere in the user agent
    USER_AGENTS = ['Applebot', 'OAI-SearchBot', 'ChatGPT-User', 'GPTBot', 'Meta-ExternalFetcher', 'Bytespider',
                   'CCBot', 'ClaudeBot', 'FacebookBot', 'Meta-ExternalAgent', 'Amazonbot', 'PerplexityBot',
                   'YouBot', 'archive.org_bot', 'Arquivo-web-crawler', 'heritrix', 'ia-archiver',
                   'ia_archiver-web.archive.org', 'Nicecrawler', 'anthropic-ai', 'Claude-Web', 'cohere-ai']
    return (USER_AGENTS,)


@app.cell
def _(datetime, timedelta):
    # Establish time interval to last 14 days (rounded to hour)
    curr_dt = datetime.now().replace(minute=0, second=0, microsecond=0)
    end_dt = curr_dt.strftime('%Y-%m-%dT%H:00:00Z')
    start_dt = (curr_dt - timedelta(days=14)).strftime('%Y-%m-%dT%H:00:00Z')
    return end_dt, start_dt


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Obtain and parse robots.txt rules

        First, we will select the zone by its ID and fetch the associated hostname. On the GraphQL side, data is
        obtained by filtering by both ID and host. The hostname is also important to obtain since we must fetch
        and process the given zone's `robots.txt` manually.
        """
    )
    return


@app.cell(hide_code=True)
def _(CF_API_TOKEN, HOSTNAME, account_id, json, pd, requests):
    # Fetch a sample of the zones in the account
    _zone_call = f"{HOSTNAME}/client/v4/zones"
    _api_resp = requests.get(
        _zone_call,
        headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
        params={"per_page": 50, "account.id": account_id},
    ).text
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

    print('Zone sample:')
    account_zones
    return


@app.cell
def _(mo):
    zone_form = mo.ui.text(label="Selected zone ID:").form()
    zone_form
    return (zone_form,)


@app.cell
def _(CF_API_TOKEN, HOSTNAME, mo, requests, zone_form):
    # Zone Id of the zone to obtain data from
    mo.stop(zone_form.value is None, 'Please submit a zone ID above first')
    SELECTED_ZONE = zone_form.value

    # Endpoint to get zone info
    main_call = f'{HOSTNAME}/client/v4/zones/{SELECTED_ZONE}'
    _api_resp = requests.get(main_call,
                             headers={'Authorization': 'Bearer {}'.format(CF_API_TOKEN)})
    _api_resp_json = _api_resp.json()

    if not _api_resp_json['success']:
        print(f'Failed to fetch zone info (status code {_api_resp.status_code}). Received the following errors:')
        for _error in _api_resp_json['errors']:
            print(f" - {_error['code']}: {_error['message']}")
        _api_resp.raise_for_status()

    ROBOTS_HOST = _api_resp_json['result']['name']

    print(f'Obtained the following zone: {SELECTED_ZONE} - {ROBOTS_HOST}')
    return ROBOTS_HOST, SELECTED_ZONE


@app.cell
def _(mo):
    mo.md(
        r"""
        Now we will fetch and parse content found on the `/robots.txt` path, using the `urllib` library.

        /// Attention

        It is not guaranteed that requesting `robots.txt` content will be successful, as requests using this method
        are perceived as bot traffic which may be blocked depending on how the zone is configured, as well as due to
        other factors.

        ///
        """
    )
    return


@app.cell
def _(ROBOTS_HOST, requests):
    # Request robots.txt content
    headers = {'User-Agent': 'Cloudflare notebooks'}
    content = requests.get(f'https://{ROBOTS_HOST}/robots.txt', headers=headers).text
    return (content,)


@app.cell
def _(RobotFileParser, content, unquote):
    # Format obtained content into a list of [crawlers - path] entries
    # Note: multiple entries may be associated with a given path
    rfp = RobotFileParser()

    rfp.parse(content.splitlines(keepends=True))
    entries = ([rfp.default_entry, *rfp.entries] if rfp.default_entry else rfp.entries)

    entries_parsed = []
    for entry in entries:
        for ruleline in entry.rulelines:
            if not ruleline.allowance:
                entries_parsed.append((entry.useragents, unquote(ruleline.path)))
    return (entries_parsed,)


@app.cell
def _(USER_AGENTS, entries_parsed):
    # Format entries into GraphQL filters
    # Filters are composed of user agent but may also have a specified path
    # A user agent of '*' represents all specified AI crawlers, a '/' path represents all paths
    filters = []

    for _curr_entry in entries_parsed:
        # Add all AI user agents if * is specified
        if '*' in _curr_entry[0]:
            _ua_to_add = USER_AGENTS
        # Else, add only specified ones
        else:
            _ua_to_add = _curr_entry[0]

        for _ua in _ua_to_add:
            _ua_regex = f'%{_ua}%'
            if _curr_entry[1] != '/':
                # Changes to SQL "LIKE" syntax
                _path_regex = _curr_entry[1].replace('*', '%').replace('_', '\\_')
                _curr_filter = {"AND": [{"userAgent_like": _ua_regex},
                                        {"clientRequestPath_like": _path_regex}]}
            else:
                _curr_filter = {"userAgent_like": _ua_regex}
            filters.append(_curr_filter)
    return (filters,)


@app.cell
def _(mo):
    mo.md(r"""## Obtain data""")
    return


@app.cell
def _(
    CF_API_TOKEN,
    HOSTNAME,
    ROBOTS_HOST,
    SELECTED_ZONE,
    end_dt,
    filters,
    json,
    requests,
    start_dt,
):
    _QUERY_STR = '''
    {
        viewer {
          scope: zones(filter: {zoneTag: $zoneTag}) {
            topPaths: httpRequestsAdaptiveGroups(
              limit: 5000
              filter: $filter
            ) {
              count
              avg {
                sampleInterval
              }
              sum {
                edgeResponseBytes
                visits
              }
              dimensions {
                userAgent
                metric: clientRequestPath
                clientRequestHTTPHost
                clientRequestScheme
              }
            }
          }
        }
      }
    '''

    _QUERY_VARIABLES = {"zoneTag": SELECTED_ZONE,
                        "filter": {
                            "AND": [{"datetime_leq": end_dt,
                                     "datetime_geq": start_dt},
                                    {"requestSource": "eyeball"},
                                    {"clientRequestPath_neq": "/robots.txt"},
                                    {"clientRequestHTTPHost_like": f"{ROBOTS_HOST}%"},
                                    {"OR": [{"edgeResponseStatus": 200},
                                            {"edgeResponseStatus": 304}]},
                                    {"OR": filters}]
                        }}

    _resp_raw = requests.post(f'{HOSTNAME}/client/v4/graphql',
                              headers={'Authorization': 'Bearer {}'.format(CF_API_TOKEN)},
                              json={'query': _QUERY_STR, 'variables': _QUERY_VARIABLES})

    json_audit_data = json.loads(_resp_raw.text)
    return (json_audit_data,)


@app.cell
def _(USER_AGENTS, json_audit_data, pd, warnings):
    _all_rows = []

    # Format response code data into a DataFrame with [host - metric - user agent - matched user agent - visits]
    for _entry in json_audit_data['data']['viewer']['scope'][0]['topPaths']:
        # Given that AI user agents are matched with a `%{ua}%` pattern, we check for matches using the "in" statement
        # Just in case, we store as arrays, but ideally the lengths should be exactly 1
        _curr_ua_matches = [el for el in USER_AGENTS if el in _entry['dimensions']['userAgent']]

        # Warn the user if any user agent matches multiple AI entries
        if len(_curr_ua_matches) > 1:
            warnings.warn(f'''Pattern {_entry['dimensions']['userAgent']} matched {len(_curr_ua_matches)} entries''')
        elif len(_curr_ua_matches) == 0:
            raise ValueError(f'''Pattern {_entry['dimensions']['userAgent']} matched no entries''')

        _curr_row = dict(
            host=_entry['dimensions']['clientRequestHTTPHost'],
            metric=_entry['dimensions']['metric'],
            user_agent=_entry['dimensions']['userAgent'],
            ua_matches=_curr_ua_matches,
            violations=_entry['sum']['visits']
        )
        _all_rows.append(_curr_row)

    df_ai_paths = pd.DataFrame(_all_rows)
    return (df_ai_paths,)


@app.cell
def _(df_ai_paths):
    _df_ai_matches_agg = df_ai_paths.copy()
    _df_ai_matches_agg['match'] = _df_ai_matches_agg['ua_matches'].apply(lambda x: x[0])
    _df_ai_matches_agg = _df_ai_matches_agg.groupby('match').agg({
        'violations': 'sum'
    }).reset_index().sort_values('violations', ascending=False)
    _df_ai_matches_agg
    return


@app.cell
def _(df_ai_paths):
    df_ai_paths.sort_values('violations', ascending=False)
    return


@app.cell
def _(
    CF_API_TOKEN,
    HOSTNAME,
    ROBOTS_HOST,
    SELECTED_ZONE,
    end_dt,
    filters,
    json,
    requests,
    start_dt,
):
    _QUERY_STR = '''
    {
        viewer {
          scope: zones(filter: {zoneTag: $zoneTag}) {
            topPaths: httpRequestsAdaptiveGroups(
              limit: 5000
              filter: $filter
            ) {
              count
              avg {
                sampleInterval
              }
              sum {
                edgeResponseBytes
                visits
              }
              dimensions {
                userAgent
                ts: date
              }
            }
          }
        }
      }
    '''

    _QUERY_VARIABLES = {"zoneTag": SELECTED_ZONE,
                        "filter": {
                            "AND": [{"datetime_leq": end_dt,
                                     "datetime_geq": start_dt},
                                    {"requestSource": "eyeball"},
                                    {"clientRequestPath_neq": "/robots.txt"},
                                    {"clientRequestHTTPHost_like": f"{ROBOTS_HOST}%"},
                                    {"OR": [{"edgeResponseStatus": 200},
                                            {"edgeResponseStatus": 304}]},
                                    {"OR": filters}]
                        }}

    _resp_raw = requests.post(f'{HOSTNAME}/client/v4/graphql',
                              headers={'Authorization': 'Bearer {}'.format(CF_API_TOKEN)},
                              json={'query': _QUERY_STR, 'variables': _QUERY_VARIABLES})

    json_audit_ts_data = json.loads(_resp_raw.text)
    return (json_audit_ts_data,)


@app.cell
def _(USER_AGENTS, json_audit_ts_data, pd):
    _all_rows = []

    # Format response code data into a DataFrame with [time - user agent - matched user agent - visits]
    for _entry in json_audit_ts_data['data']['viewer']['scope'][0]['topPaths']:
        # Given that AI user agents are matched with a `%{ua}%` pattern, we check for matches using the "in" statement
        # Just in case, we store as arrays, but ideally the lengths should be exactly 1
        _curr_ua_matches = [el for el in USER_AGENTS if el in _entry['dimensions']['userAgent']]

        # For this trend, we are assuming each row corresponds to a single AI entry
        if len(_curr_ua_matches) != 1:
            raise ValueError(f'''Pattern {_entry['dimensions']['userAgent']} matched {len(_curr_ua_matches)} entries''')

        _curr_row = dict(
            time=_entry['dimensions']['ts'],
            user_agent=_entry['dimensions']['userAgent'],
            ua_matches=_curr_ua_matches[0],
            violations=_entry['sum']['visits']
        )
        _all_rows.append(_curr_row)

    df_ai_time = pd.DataFrame(_all_rows)
    df_ai_time['time'] = pd.to_datetime(df_ai_time['time']).astype('datetime64[s]')
    return (df_ai_time,)


@app.cell
def _(alt, df_ai_time):
    alt.Chart(df_ai_time).mark_line().encode(
        alt.X('time:T', title='Time'),
        alt.Y('violations:Q', title='Visits'),
        alt.Color('ua_matches', title='AI crawler')
    ).properties(height=400, width=500,
                 title=dict(text='Site requests by AI crawler', subtitle='Violations only'))
    return


if __name__ == "__main__":
    app.run()

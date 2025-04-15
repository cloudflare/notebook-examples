import marimo

__generated_with = "0.11.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import altair as alt
    from datetime import datetime, timedelta
    import json
    import marimo as mo
    import pandas as pd
    import requests
    import warnings

    # Process robots.txt content
    from urllib.robotparser import RobotFileParser
    from urllib.parse import unquote
    return (
        RobotFileParser,
        alt,
        datetime,
        json,
        mo,
        pd,
        requests,
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
    CF_API_TOKEN = "<your-token>"

    HOSTNAME = "https://examples-api-proxy.notebooks.cloudflare.com"

    # Establish time interval to last 14 days (rounded to hour)
    curr_dt = datetime.now().replace(minute=0, second=0, microsecond=0)
    end_dt = curr_dt.strftime('%Y-%m-%dT%H:00:00Z')
    start_dt = (curr_dt - timedelta(days=14)).strftime('%Y-%m-%dT%H:00:00Z')
    return CF_API_TOKEN, HOSTNAME, curr_dt, end_dt, start_dt


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


@app.cell
def _(CF_API_TOKEN, HOSTNAME, requests):
    # Zone Id of the zone to obtain data from
    SELECTED_ZONE = '<your-zone-tag>'

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
    return ROBOTS_HOST, SELECTED_ZONE, main_call


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
    return content, headers


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
    return entries, entries_parsed, entry, rfp, ruleline


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
            visits=_entry['sum']['visits']
        )
        _all_rows.append(_curr_row)

    df_ai_paths = pd.DataFrame(_all_rows)
    return (df_ai_paths,)


@app.cell
def _(df_ai_paths):
    _df_ai_matches_agg = df_ai_paths.copy()
    _df_ai_matches_agg['match'] = _df_ai_matches_agg['ua_matches'].apply(lambda x: x[0])
    _df_ai_matches_agg = _df_ai_matches_agg.groupby('match').agg({
        'visits': 'sum'
    }).reset_index().sort_values('visits', ascending=False)
    _df_ai_matches_agg
    return


@app.cell
def _(df_ai_paths):
    df_ai_paths.sort_values('visits', ascending=False)
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
            visits=_entry['sum']['visits']
        )
        _all_rows.append(_curr_row)

    df_ai_time = pd.DataFrame(_all_rows)
    df_ai_time['time'] = pd.to_datetime(df_ai_time['time']).astype('datetime64[s]')
    return (df_ai_time,)


@app.cell
def _(alt, df_ai_time):
    alt.Chart(df_ai_time).mark_line().encode(
        alt.X('time:T', title='Time'),
        alt.Y('visits:Q', title='Requests'),
        alt.Color('ua_matches', title='AI crawler')
    ).properties(height=400, width=500,
                 title=dict(text='Site requests by AI crawler', subtitle='Violations only'))
    return


if __name__ == "__main__":
    app.run()

import marimo

__generated_with = "0.11.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import altair as alt
    import json
    import marimo as mo
    import numpy as np
    import pandas as pd
    import requests
    return alt, json, mo, np, pd, requests


app._unparsable_cell(
    r"""
    TODO:
     - separate warnings as markdown
     - explain how to delete created files and buckets
    """,
    name="_"
)


@app.cell
def _(mo):
    mo.md(
        r"""
        # D1 API use case

        In this notebook, we will show a simple use case involving interactions with D1 associated to a
        Cloudflare account. This will involve the following:<br>
         1. creating a D1 dataset;<br>
         2. listing existing D1 datasets;<br>
         3. simple query listing tables of a D1 dataset.<br>

        all using the Cloudflare API.

        **Prerequisites:**<br>
         - API token (see [here](https://developers.cloudflare.com/r2/api/s3/tokens/)
        for info on how to create one) with **D1 write** permission.
        """
    )
    return


@app.cell
def _():
    CF_ACCOUNT_TAG = 'your-account-tag'
    TOKEN = "your-token"

    HOSTNAME = 'https://examples-api-proxy.notebooks.cloudflare.com'
    URL = f'{HOSTNAME}/client/v4/accounts/{CF_ACCOUNT_TAG}/d1/database'
    return CF_ACCOUNT_TAG, HOSTNAME, TOKEN, URL


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Create new D1 dataset

        We will start by creating a new dataset.
        For this, we will make use of the `/accounts/{account_id}/d1/database`
        [endpoint](https://developers.cloudflare.com/api/resources/d1/subresources/database/methods/create/).
        This endpoint will return all account D1 datasets by default.
        A POST request with the name of the dataset in the payload will create a new entry.
        """
    )
    return


@app.cell
def _():
    NEW_DATASET_NAME = 'test-dataset'
    return (NEW_DATASET_NAME,)


@app.cell
def _(NEW_DATASET_NAME, TOKEN, URL, requests):
    # Warning: skip this cell if the dataset already exists

    # Send POST query with dataset name as payload
    _payload = dict(name=NEW_DATASET_NAME)
    new_dataset_resp = requests.post(URL, headers={'Authorization': 'Bearer {}'.format(TOKEN)},
                                     json=_payload)

    # Results handling
    new_dataset_resp_json = new_dataset_resp.json()
    if new_dataset_resp_json['success']:
        _new_dataset_info = new_dataset_resp_json['result']
        print(f"Successfully created new D1 dataset: {_new_dataset_info['name']} ({_new_dataset_info['uuid']})")
    else:
        print(f'Failed to create new D1 dataset (status code {new_dataset_resp.status_code}).',
              'Received the following errors:')
        for _error in new_dataset_resp_json['errors']:
            print(f" - {_error['code']}: {_error['message']}")
        new_dataset_resp.raise_for_status()
    return new_dataset_resp, new_dataset_resp_json


@app.cell
def _(mo):
    mo.md(
        r"""
        ## List available D1 datasets

        By performing a GET request (with no payload) to the same `/accounts/{account_id}/d1/database`
        [endpoint](https://developers.cloudflare.com/api/resources/d1/subresources/database/methods/list/)
        we can get the names, unique Ids as well as other info of all D1 datasets associated with a Cloudflare account.
        """
    )
    return


@app.cell
def _(TOKEN, URL, pd, requests):
    # Send GET query
    api_resp = requests.get(URL, headers={'Authorization': 'Bearer {}'.format(TOKEN)})

    # Results handling
    api_resp_json = api_resp.json()
    if api_resp_json['success']:
        print('Successfully fetched D1 dataset list')
        d1_datasets = pd.DataFrame(api_resp_json['result'])
    else:
        print(f'Failed to fetch D1 dataset list (status code {api_resp.status_code}). Received the following errors:')
        for error in api_resp_json['errors']:
            print(f" - {error['code']}: {error['message']}")
        api_resp.raise_for_status()
    return api_resp, api_resp_json, d1_datasets, error


@app.cell
def _(d1_datasets):
    d1_datasets
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Performing queries

        Queries to D1 databases using the API are made using POST requests to
        `/accounts/{account_id}/d1/database/{database_id}/query`
        [endpoint](https://developers.cloudflare.com/api/resources/d1/subresources/database/methods/query/).
        The query (as well as optional query parameters) must be added as payload.
        """
    )
    return


@app.cell
def _(HOSTNAME, requests):
    # Perform a query and return results as json
    # Raises error otherwise, prints which errors were obtained
    def query_d1(account_id, database_id, token, query):
        url = f'{HOSTNAME}/client/v4/accounts/{account_id}/d1/database/{database_id}/query'
        payload = dict(sql=query)
        query_resp = requests.post(url, headers={'Authorization': 'Bearer {}'.format(token)},
                                   json=payload)
        query_resp_json = query_resp.json()

        if query_resp_json['success']:
            return query_resp_json['result']
        else:
            print(f'Failed to perform query to D1 dataset (status code {query_resp.status_code}).',
                  'Received the following errors:')
            for error in query_resp_json['errors']:
                print(f" - {error['code']}: {error['message']}")
            query_resp.raise_for_status()
    return (query_d1,)


@app.cell
def _():
    DATABASE_ID = 'your-database-id'
    return (DATABASE_ID,)


@app.cell
def _(CF_ACCOUNT_TAG, DATABASE_ID, TOKEN, query_d1):
    # Note: D1 uses SQLite syntax
    _query = '''
    CREATE TABLE IF NOT EXISTS simple(
        t       INTEGER PRIMARY KEY AUTOINCREMENT,
        val     INTEGER
    );
    '''

    _ = query_d1(
        CF_ACCOUNT_TAG,
        DATABASE_ID,
        TOKEN,
        _query
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        For the purposes of this demonstration, we will create a short (slightly noisy) sinusoidal function
        which will be stored in the previously created table.
        """
    )
    return


@app.cell
def _(CF_ACCOUNT_TAG, DATABASE_ID, TOKEN, np, query_d1):
    # Warning: rerunning this cell will append new data to an already existing table!

    # Number of entries
    _SIZE_TS = 100

    # Create sinusoidal time series with fixed seed
    _rng = np.random.default_rng(1234)
    _ts = np.cos(np.arange(_SIZE_TS)) + _rng.random(_SIZE_TS)

    # Generate the SQL INSERT query based on the generated time series
    _query_inserts = ',\n'.join([f'({float(el)})' for el in _ts])
    _query = f'''
    INSERT INTO simple(val) VALUES
    {_query_inserts};
    '''

    _ = query_d1(
        CF_ACCOUNT_TAG,
        DATABASE_ID,
        TOKEN,
        _query
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        This is a more manual approach to populating SQL tables. The alternative would be to import an already existing
        database into D1, although that approach requires efforts outside of this notebook.

        More information on how to import (and export) data from D1 datasets can be found in
        [this dev page](https://developers.cloudflare.com/d1/best-practices/import-export-data/).

        Now, let's test the table by querying its contents and visualising the time series.
        """
    )
    return


@app.cell
def _(CF_ACCOUNT_TAG, DATABASE_ID, TOKEN, query_d1):
    # Obtain previously created time series
    _query = 'SELECT * FROM simple;'

    ts_resp = query_d1(
        CF_ACCOUNT_TAG,
        DATABASE_ID,
        TOKEN,
        _query
    )
    return (ts_resp,)


@app.cell
def _(alt, pd, ts_resp):
    ts_df = pd.DataFrame(ts_resp[0]['results'])

    alt.Chart(ts_df, title='Sinusoidal time series from D1').mark_line().encode(
        alt.X('t',
              title='Index'),
        alt.Y('val',
              title='Value')
    ).properties(height=400, width=500)
    return (ts_df,)


if __name__ == "__main__":
    app.run()

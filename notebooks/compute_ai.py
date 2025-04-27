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
        # Cloudflare AI use case

        In this notebook, we will show a simple use case using Cloudflare's
        [AI endpoints](https://developers.cloudflare.com/api/resources/ai/).

        More information on using AI models with Cloudflare can be found here:
        https://ai.cloudflare.com/

        **Prerequisites:**<br>
         - API token (see [here](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)
        for info on how to create one)
        """
    )
    return


@app.cell
def _(account_id, token, proxy):
    CF_ACCOUNT_TAG = account_id  # After login, selected from list above
    CF_API_TOKEN = token  # Or a custom token from dash.cloudflare.com
    HOSTNAME = proxy  # using notebooks.cloudflare.com proxy
    return CF_ACCOUNT_TAG, CF_API_TOKEN, HOSTNAME


@app.cell
def _(CF_API_TOKEN, HOSTNAME, requests):
    # Class used to prompt a given model
    class AIClient:
        def __init__(self, cf_account, cf_token, model_name):
            self.cf_account = cf_account
            self.cf_token = cf_token
            self.model_name = model_name

        def change_model(self, model_name):
            self.model_name = model_name

        # Json info varies from model to model, so it must be provided as input
        def prompt(self, payload):
            endpoint = f"{HOSTNAME}/client/v4/accounts/{self.cf_account}/ai/run/{self.model_name}"
            resp = requests.post(
                endpoint,
                json=payload,
                headers={
                    "Authorization": "Bearer {}".format(CF_API_TOKEN),
                    "Content-Type": "application/json",
                },
            )

            if resp.status_code == 200:
                return resp.json()
            else:
                print(resp.text)
                resp.raise_for_status()

    return (AIClient,)


@app.cell
def _(mo):
    mo.md(
        r"""
        In order to interact with a model using the API, it is required to specify the model on the endpoint URL,
        as well as model specific inputs as the json payload.

        For a complete list of all models available, as well as their inputs, see the dedicated
        [developers webpage](https://developers.cloudflare.com/workers-ai/models/).
        Each model also has simple usage snippets to help users get started. Here we will present two model
        interactions:
        """
    )
    return


@app.cell
def _(AIClient, CF_ACCOUNT_TAG, CF_API_TOKEN):
    model_name = "@cf/meta/llama-3.1-8b-instruct"

    ai_session = AIClient(CF_ACCOUNT_TAG, CF_API_TOKEN, model_name)
    return ai_session, model_name


@app.cell
def _(mo):
    mo.md(
        r"""
        ### Text generation example

        Using the `@cf/meta/llama-3.1-8b-instruct` model, we will ask the model for information about Workers AI.
        """
    )
    return


@app.cell
def _(ai_session, mo):
    # Simple text generation example

    # User prompt
    _prompt = "Can you tell me about Cloudflare Workers AI?"

    # Includes prompt and other model specific inputs
    _payload = {
        "messages": [
            {
                "role": "system",  # ...tells the model how to behave (system prompt).
                "content": "You are a friendly assistant. Try to keep your answers short, but informative.",
            },
            {
                "role": "user",
                "content": _prompt,
            },
        ]
    }

    _prompt_resp = ai_session.prompt(_payload)

    mo.md(_prompt_resp["result"]["response"])
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ### Translation example

        Now changing to the `@cf/meta/m2m100-1.2b` model, we will translate a portuguese sentence into english.
        """
    )
    return


@app.cell
def _(ai_session, mo):
    # Translation example
    ai_session.change_model("@cf/meta/m2m100-1.2b")

    # Text to be translated
    _text = "Este é um exemplo de texto a ser traduzido de Português a Inglês usando modelos AI com Cloudflare"
    # The language text is currently in
    _source_lang = "pt"
    # The language is to be translated into
    _target_lang = "en"

    # Includes prompt and other model specific inputs
    _payload = {"text": _text, "source_lang": _source_lang, "target_lang": _target_lang}

    _prompt_resp = ai_session.prompt(_payload)
    _translated = _prompt_resp["result"]["translated_text"]

    mo.md(
        f"""
    **Original text:** {_text}<br>
    **Translated text:** {_translated}
    """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Checking AI model usage

        The Cloudflare dash has a page dedicated to account level AI model usage, which can be found in the
        `AI tab > Workers AI` page.
        Alternatively, we can perform queries using GraphQL to obtain the same information. Let's fetch the
        most used models in the last 30 days.

        These metrics are measured in number of neurons used, which represent GPU usage.
        For more information, including neuron usage per model, check the
        [AI platform pricing page](https://developers.cloudflare.com/workers-ai/platform/pricing/).
        """
    )
    return


@app.cell
def _(datetime, timedelta):
    # Establish time interval to last 30 days (trimmed to minute)
    curr_dt = datetime.now().replace(second=0, microsecond=0)
    end_dt = curr_dt.strftime("%Y-%m-%dT%H:%M:00Z")
    start_dt = (curr_dt - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:00Z")
    return curr_dt, end_dt, start_dt


@app.cell
def _(
    CF_ACCOUNT_TAG,
    CF_API_TOKEN,
    HOSTNAME,
    end_dt,
    json,
    requests,
    start_dt,
):
    _QUERY_STR = """
    query GetModelUsageOverTime($accountTag: string, $filter: filter) {
      viewer {
        accounts(filter: {accountTag: $accountTag}) {
          data: aiInferenceAdaptiveGroups(filter: {datetime_geq: $dateStart, datetime_leq: $dateEnd, neurons_gt: 0},
                                          orderBy: [date_ASC], limit: 10000) {
            sum {
              neurons: totalNeurons
            }
            dimensions {
              ts: date
              modelId
            }
          }
        }
      }
    }
    """

    _QUERY_VARIABLES = {
        "accountTag": CF_ACCOUNT_TAG,
        "dateStart": start_dt,
        "dateEnd": end_dt,
    }

    _resp_raw = requests.post(
        f"{HOSTNAME}/client/v4/graphql",
        headers={"Authorization": "Bearer {}".format(CF_API_TOKEN)},
        json={"query": _QUERY_STR, "variables": _QUERY_VARIABLES},
    )

    json_object_model_data = json.loads(_resp_raw.text)
    return (json_object_model_data,)


@app.cell
def _(json_object_model_data, pd):
    if json_object_model_data["errors"] is None:
        # Process model usage results
        _rows = []
        for _entry in json_object_model_data["data"]["viewer"]["accounts"][0]["data"]:
            _curr_row = dict(
                time=_entry["dimensions"]["ts"],
                model=_entry["dimensions"]["modelId"],
                neurons=_entry["sum"]["neurons"],
            )
            _rows.append(_curr_row)
        df_model = pd.DataFrame(_rows)
    else:
        _error_msg = "\n - ".join(
            [el["message"] for el in json_object_model_data["errors"]]
        )
        print(f"Obtained the following errors:\n - {_error_msg}")
        raise
    return (df_model,)


@app.cell
def _(alt, df_model):
    _TOP_ENTRIES = 15

    _df_model_agg = df_model.groupby("model").agg({"neurons": "sum"}).reset_index()
    _df_model_agg = _df_model_agg.sort_values("neurons", ascending=False).reset_index(
        drop=True
    )
    _df_model_agg["neuron_share"] = (
        _df_model_agg["neurons"] / _df_model_agg["neurons"].sum() * 100
    )

    _df_model_agg = _df_model_agg.head(_TOP_ENTRIES)

    alt.Chart(_df_model_agg).mark_bar().encode(
        alt.X("neuron_share:Q", title="Neurons %").axis(labelExpr='datum.value + "%"'),
        alt.Y(
            "model:N",
            title="Model",
            sort=alt.EncodingSortField(field="neuron_share", order="ascending"),
        ),
        tooltip=[
            alt.Tooltip("model:N", title="Model"),
            alt.Tooltip("neuron_share:Q", title="Neurons %"),
            alt.Tooltip("neurons:N", title="Total neurons"),
        ],
    ).properties(
        title=alt.TitleParams("Models with most usage"),
        height=350,
        width=700,
    )
    return


@app.cell
def _(alt, df_model):
    alt.Chart(df_model).mark_line().encode(
        alt.X("time:T", title="Date"),
        alt.Y("neurons:Q", title="Neurons"),
        alt.Color("model:N", title="Model"),
        tooltip=[
            alt.Tooltip("time:T", title="Time", format="%b %d, %Y"),
            alt.Tooltip("model:N", title="Model"),
            alt.Tooltip("neurons:Q", title="Neurons"),
        ],
    ).properties(
        title=alt.TitleParams("Model usage over time"),
        height=350,
        width=700,
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        <b style='color: tomato'>Note:</b> Since we are querying for the current day, results may be incomplete.
        Not only that, but if this query is executed right after running the prompt above, model usage may not be
        updated in time.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Going further

        We can take advantage of Cloudflare's tooling to unlock more advanced use cases. One such example involves
        using R2 buckets, which can act as storage to both model inputs and outputs.
        To see more on R2 interactions, check the `r2` example notebook.
        """
    )
    return


if __name__ == "__main__":
    app.run()

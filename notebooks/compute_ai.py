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
def _(CF_API_TOKEN, HOSTNAME, Request, json, urlopen):
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
            req = Request(endpoint,
                          headers={
                              "Authorization": "Bearer {}".format(CF_API_TOKEN),
                              "Content-Type": "application/json",
                          },
                          data=json.dumps(payload),
                          method='POST')
            resp = urlopen(req)

            if resp.getcode() == 200:
                return json.load(resp)
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
def _(AIClient, CF_ACCOUNT_ID, CF_API_TOKEN):
    model_name = "@cf/meta/llama-3.1-8b-instruct"

    ai_session = AIClient(CF_ACCOUNT_ID, CF_API_TOKEN, model_name)
    return (ai_session,)


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
    _text = "Este é um exemplo de texto a ser traduzido para Inglês usando modelos AI com Cloudflare"
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
        "accountTag": CF_ACCOUNT_ID,
        "dateStart": start_dt,
        "dateEnd": end_dt,
    }

    _data = json.dumps({"query": _QUERY_STR, "variables": _QUERY_VARIABLES}).encode()
    _request = Request(f"{HOSTNAME}/client/v4/graphql",
                       headers={"Authorization": f"Bearer {CF_API_TOKEN}",
                                "Accept": "application/json",
                                "Content-Type": "application/json"},
                       data=_data,
                       method='POST')
    _resp_raw = urlopen(_request).read()

    json_object_model_data = json.loads(_resp_raw)
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
        raise Exception
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

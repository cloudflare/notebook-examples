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

    CF_ACCOUNT_ID = account_id  # After login, selected from list above
    CF_API_TOKEN = df.access_token  # Or a custom token from dash.cloudflare.com
    HOSTNAME = proxy
    return CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME


@app.cell
def _(CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, Request, json, mo, proxy, urlopen):

    WORKERS_AI_MODEL = "@cf/meta/llama-3.2-3b-instruct"

    def workers_ai_llm_request(prompt):
        if not prompt.value:
            return "**Please ask a question using the form above.** 👆"

        # For more details see: https://developers.cloudflare.com/workers-ai/get-started/rest-api/
        url = f"{proxy}/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{WORKERS_AI_MODEL}"
        headers = {"Authorization": f"Bearer {CF_API_TOKEN}",
                   "Accept": "application/json",
                   "Content-Type": "application/json"}

        payload = json.dumps({
            "messages": [
                {
                    "role": "system",  # ...tells the model how to behave (system prompt).
                    "content": "You are a friendly assistant. Try to keep your answers short, but informative.",
                },
                {
                    "role": "user",
                    "content": prompt.value,
                },
            ]
        })
        request = Request(url, headers=headers, data=payload,
                          method='POST')
        api_response = urlopen(request)
        model_result = json.load(api_response)

        # We are not handling any possible errors, but only because this is just an example.
        return model_result["result"]["response"]

    prompt = mo.ui.text_area(
        placeholder='Write your prompt here and click the "Submit" button.'
    ).form()
    mo.md(f"Ask a question to {WORKERS_AI_MODEL}: {prompt}")
    return prompt, workers_ai_llm_request


@app.cell
def _(mo, prompt, workers_ai_llm_request):
    answer = workers_ai_llm_request(prompt)
    mo.md(f"""{answer}""")
    return


if __name__ == "__main__":
    app.run()

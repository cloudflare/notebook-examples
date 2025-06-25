

import marimo

__generated_with = "0.13.2"
app = marimo.App(width="full", app_title="Cloudflare Notebook")


@app.cell(hide_code=True)
def _():
    # Helper Functions
    import marimo as mo
    import js
    import requests
    import urllib
    from urllib.request import Request, urlopen
    import json

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
    return Request, get_accounts, get_token, json, mo, proxy, urlopen


@app.cell
async def _(get_accounts, get_token, mo):
    # 1) After login, Run ▶ this cell to get your API token and accounts
    # 2) Select a specific Cloudflare account below
    # 3) Start coding!
    token = await get_token()
    accounts = await get_accounts(token)
    radio = mo.ui.radio(options=[a["name"] for a in accounts], label="Select Account")
    return accounts, radio, token


@app.cell(hide_code=True)
def _(accounts, mo, radio, token):
    # Run ▶ this cell to select a specific Cloudflare account
    account_name = radio.value
    account_id = next((a["id"] for a in accounts if a["name"] == account_name), None)
    mo.hstack([radio, mo.md(f"**Variables**  \n**token:** {token}  \n**account_name:** {account_name or 'None'}  \n**account_id:** {account_id or 'None'}")])  # noqa: E501
    return (account_id,)


@app.cell
def _(account_id, mo, proxy, token):
    mo.stop(token is None or account_id is None, 'Please retrieve a token first and select an account above')

    CF_ACCOUNT_ID = account_id  # After login, selected from list above
    CF_API_TOKEN = token  # Or a custom token from dash.cloudflare.com
    HOSTNAME = proxy
    return CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME


@app.cell
def _(CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, Request, json, mo, urlopen):

    WORKERS_AI_MODEL = "@cf/meta/llama-3.2-3b-instruct"

    def workers_ai_llm_request(prompt):
        if not prompt.value:
            return "**Please ask a question using the form above.** 👆"

        # For more details see: https://developers.cloudflare.com/workers-ai/get-started/rest-api/
        # Account must have Workers AI enabled, such as "Edge Notebooks"
        url = f"{HOSTNAME}/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{WORKERS_AI_MODEL}"
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

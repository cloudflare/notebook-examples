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

# Help function init stubs
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


##################
# Notebook Cells #
##################


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


@app.cell
def _():
    # Find your account ID by logging into https://dash.cloudflare.com and selecting a website,
    # then look for "Account ID" under the "API" section on the right-hand side of the screen.
    CF_ACCOUNT_ID = "paste-your-account-id-here"

    # Go to https://dash.cloudflare.com/profile/api-tokens and create a "Workers AI" token.
    # Then paste it here, but do not share it with anyone else. It's a secret... 🤫
    CF_API_TOKEN = "paste-your-api-token-here"
    return CF_ACCOUNT_ID, CF_API_TOKEN


@app.cell
def _(CF_ACCOUNT_ID, CF_API_TOKEN, mo):
    import requests

    WORKERS_AI_MODEL = "@cf/meta/llama-3.2-3b-instruct"

    def workers_ai_llm_request(prompt):
        if not prompt.value:
            return "**Please ask a question using the form above.** 👆"

        # For more details see: https://developers.cloudflare.com/workers-ai/get-started/rest-api/
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{WORKERS_AI_MODEL}"
        headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}

        payload = {
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
        }

        api_response = requests.post(url, json=payload, headers=headers)
        model_result = api_response.json()

        # We are not handling any possible errors, but only because this is just an example.
        return model_result["result"]["response"]

    prompt = mo.ui.text_area(
        placeholder='Write your prompt here and click the "Submit" button.'
    ).form()
    mo.md(f"Ask a question to {WORKERS_AI_MODEL}: {prompt}")
    return WORKERS_AI_MODEL, prompt, requests, workers_ai_llm_request


@app.cell
def _(mo, prompt, workers_ai_llm_request):
    answer = workers_ai_llm_request(prompt)
    mo.md(answer)
    return (answer,)


if __name__ == "__main__":
    app.run()

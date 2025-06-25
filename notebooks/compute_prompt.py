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

    CF_ACCOUNT_ID = account_id  # After login, selected from list above
    CF_API_TOKEN = token  # Or a custom token from dash.cloudflare.com
    HOSTNAME = proxy
    return CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME


@app.cell
def _(CF_ACCOUNT_ID, CF_API_TOKEN, HOSTNAME, mo, requests):

    WORKERS_AI_MODEL = "@cf/meta/llama-3.2-3b-instruct"

    def workers_ai_llm_request(prompt):
        if not prompt.value:
            return "**Please ask a question using the form above.** 👆"

        # For more details see: https://developers.cloudflare.com/workers-ai/get-started/rest-api/
        # Account must have Workers AI enabled, such as "Edge Notebooks"
        url = f"{HOSTNAME}/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{WORKERS_AI_MODEL}"
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
    return prompt, workers_ai_llm_request


@app.cell
def _(mo, prompt, workers_ai_llm_request):
    answer = workers_ai_llm_request(prompt)
    mo.md(f"""{answer}""")
    return


if __name__ == "__main__":
    app.run()

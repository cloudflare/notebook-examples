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
def _(token, account_name, account_id):
    print("Hello, World! 🌎")
    print(f"Cloudflare API Token: {token}")
    print(f"Cloudflare Account Name: {account_name}")
    print(f"Cloudflare Account ID: {account_id}")
    return


if __name__ == "__main__":
    app.run()

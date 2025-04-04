import marimo

__generated_with = "0.11.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


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

    prompt = mo.ui.text_area(placeholder='Write your prompt here and click the "Submit" button.').form()
    mo.md(f"Ask a question to {WORKERS_AI_MODEL}: {prompt}")
    return WORKERS_AI_MODEL, prompt, requests, workers_ai_llm_request


@app.cell
def _(mo, prompt, workers_ai_llm_request):
    answer = workers_ai_llm_request(prompt)
    mo.md(answer)
    return (answer,)


if __name__ == "__main__":
    app.run()

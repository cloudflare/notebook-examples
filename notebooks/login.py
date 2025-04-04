import marimo

__generated_with = "0.11.2"
app = marimo.App(width="medium")


@app.cell
def login():
    """
    Step 1: Click the ▶ button at the top right of this cell code to load a login form!
    """
    import marimo as mo
    import urllib.request

    html_path = f"{mo.notebook_location()}/public/login"
    html = ""
    with urllib.request.urlopen(html_path) as response:
        html = response.read().decode()
    mo.iframe(html)

    return html, mo


@app.cell
async def token():
    """
    Step 2: Loads the Cloudflare API token in python and tests it with a basic account list request.
    This will automatically pick up a token if it is loaded in the first 3 minutes, no need to ▶ run this cell manually.
    See the output result at the bottom of this cell!
    """
    import asyncio
    import js
    import requests

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

    async def wait_for_token(timeout=180):
        start = asyncio.get_event_loop().time()
        while True:
            try:
                tokenRecord = await js.getAuthToken()
                if tokenRecord and tokenRecord.token:
                    return tokenRecord.token
            except Exception:
                pass
            elapsed = asyncio.get_event_loop().time() - start
            print(f"Waiting for token... {elapsed:.1f}s elapsed", end="\r")
            await asyncio.sleep(1)
            if elapsed > timeout:
                raise TimeoutError("Timed out waiting for token")

    token = await wait_for_token()
    print("\nCloudflare API token for this session:")
    print(token)

    # API request test using standard Python output
    url = "https://examples-api-proxy.notebooks.cfdata.org/client/v4/accounts"
    headers = {"Authorization": f"Bearer {token}"}
    api_response = requests.get(url, headers=headers)
    result = api_response.json()
    print("")
    if result.get("success"):
        print("Token test was successful!")
        accounts = result.get("result", [])
        print("Cloudflare Accounts:")
        for account in accounts:
            print(f"- {account['name']} (ID: {account['id']})")
    else:
        print("Error listing accounts:")
        print(result)
    return token


if __name__ == "__main__":
    app.run()

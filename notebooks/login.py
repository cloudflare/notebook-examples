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
    with urllib.request.urlopen(html_path) as response:
        html = response.read().decode()
    mo.iframe(html, height="1px")
    return html, mo


@app.cell
async def token():
    """
    Step 2: After login, load the Cloudflare API token in python and tests it with a basic account list request.
    Run this cell ▶ and view the output!
    """
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
    token = None
    tokenRecord = await js.getAuthToken()
    if tokenRecord and tokenRecord.token:
        token = tokenRecord.token

    print("\nCloudflare API token for this session:")
    print(token)

    # API request test using standard Python output
    url = "https://examples-api-proxy.notebooks.cloudflare.com/client/v4/accounts"
    headers = {"Authorization": f"Bearer {token}"}
    result = requests.get(url, headers=headers).json()
    if result.get("success"):
        print("\nToken test was successful!")
        accounts = result.get("result", [])
        print("Cloudflare Accounts:")
        for account in accounts:
            print(f"- {account['name']} (ID: {account['id']})")
    else:
        print("\nError listing accounts:")
        print(result)
    return token


if __name__ == "__main__":
    app.run()

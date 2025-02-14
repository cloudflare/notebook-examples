# Notebook Examples

These examples demonstrate how to use the [Cloudflare API](https://developers.cloudflare.com/api/) within interactive Python notebooks. They cover a number of relatively simple tasks, from analysing logs to writing billing reports, storing files in [R2](https://www.cloudflare.com/developer-platform/products/r2/), or querying [D1](https://developers.cloudflare.com/d1/) databases. They aren't meant as complete solutions, but rather as starting points for your own ideas and explorations.

Each one of these notebooks is also being served from [Cloudflare Pages](https://pages.cloudflare.com/) at [&lt;url&gt;>]() and that runs entirely within your browser, with all data saved solely in your browser. You can read more about it at [marimo.io](https://docs.marimo.io/guides/wasm/) and [pyodide.org](https://pyodide.org/). If you wish to run heavier tasks, you may want to consider running them as an application instead.

## Adding new Notebooks

Create the new notebook (`.py`) inside the notebooks directory, and add it to the `notebooks.yaml` file at the root of the repository.

## Testing Notebooks Locally

Run `make edit` to start a local [Marimo](https://docs.marimo.io/) server inside a Python virtual environment.

Run `make export` to convert the notebooks to WASM. Then run `make preview` if you want to see how it will look like once published to Cloudflare Pages.

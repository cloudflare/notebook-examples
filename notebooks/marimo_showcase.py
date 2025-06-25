# Source: https://marimo.io/p/@marimo/embedding-visualizer
import marimo

__generated_with = "0.14.7"

app = marimo.App(
    width="full",
    auto_download=["ipynb", "html"],
    app_title="Cloudflare Notebook",
)


##################
# Notebook Cells #
##################


@app.cell(hide_code=True)
def _():
    import marimo as mo
    mo.md(
        """
        # Marimo Gallery
        Analysis of AI in Business
        > https://marimo.io/p/@sumble/gen-ai?show-code=false

        Neural Networks in browser
        > https://marimo.io/p/@marimo/micrograd

        F1 Visualization
        > https://marimo.io/p/@marimo/f1-driver-career-explorer?show-code=false

        Education, visualization, and progressive stages of the notebook
        > https://marimo.io/@public/signal-decomposition
        """
    )

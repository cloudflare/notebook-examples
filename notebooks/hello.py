import marimo

__generated_with = "0.11.2"
app = marimo.App(width="medium")


@app.cell
def _():
    print("Hello, World!")
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

"""Entry point: `python app.py` runs the development server."""

from achecker_gui import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])

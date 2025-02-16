# run.py

from app_final import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, url_for

app = Flask(__name__,
    static_folder='static',
    static_url_path='/static'
)
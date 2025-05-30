from flask import Flask
from backend.routes.v1 import v1

app = Flask(__name__)
app.register_blueprint(v1, url_prefix="/v1")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5234, debug=True)

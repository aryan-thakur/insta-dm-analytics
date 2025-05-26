from flask import Flask
from backend.routes.v1 import v1

app = Flask(__name__)
app.register_blueprint(v1, url_prefix="/v1")

if __name__ == "__main__":
    # You can run this simple app using `python your_file_name.py`
    # It will be accessible at http://127.0.0.1:5000/message_volume
    app.run(host="0.0.0.0", port=5234, debug=True)

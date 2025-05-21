from flask import Flask, render_template_string, request
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, Text, DateTime, Boolean
import plotly.graph_objs as go
import plotly.io as pio
import pandas as pd
import os

app = Flask(__name__)

# --- Database Configuration ---
DATABASE_FILENAME = os.environ.get(
    "DATABASE_FILENAME", "instagram_messages.db"
)  # Default if env var is not set
DATABASE_PATH = os.path.join("/app", DATABASE_FILENAME)  # Path inside the container
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Database Model ---
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_username = Column(Text)
    sender = Column(Text)
    message = Column(Text)
    timestamp = Column(DateTime)
    timestamp_iso = Column(Text)  # Add the timestamp_iso column
    story_reply = Column(Text)
    liked = Column(Boolean)
    timestamp_liked = Column(DateTime)
    attachment = Column(Text)
    attachment_link = Column(Text)
    reference_account = Column(Text)
    audio = Column(Boolean)
    photo = Column(Boolean)
    video = Column(Boolean)


@app.route("/message_volume")
def message_volume():
    """
    Displays a Plotly graph of message volume per month, filterable by username.
    """
    db = SessionLocal()
    username_filter = request.args.get("username")  # Get username from query parameter

    try:
        query = db.query(
            func.strftime("%Y-%m", Message.timestamp_iso).label(
                "month"
            ),  # Use timestamp_iso
            func.count().label("message_count"),
        ).group_by("month")

        if username_filter:
            query = query.filter(Message.conversation_username == username_filter)

        results = query.all()

        # Convert results to a pandas DataFrame for easier Plotly plotting
        df = pd.DataFrame(results, columns=["month", "message_count"])
        df["month"] = pd.to_datetime(df["month"])
        df = df.sort_values("month")

        fig = go.Figure(data=[go.Bar(x=df["month"], y=df["message_count"])])
        fig.update_layout(
            title=f'Message Volume Per Month{" for " + username_filter if username_filter else ""}',
            xaxis_title="Month",
            yaxis_title="Number of Messages",
        )

        graph_html = pio.to_html(fig, full_html=False)

        return render_template_string(
            """
            <h1>Message Volume Analysis</h1>
            <form action="" method="get">
                <label for="username">Filter by Username:</label>
                <input type="text" id="username" name="username" value="{{ username }}">
                <input type="submit" value="Filter">
            </form>
            <div>
                {{ graph_html | safe }}
            </div>
        """,
            graph_html=graph_html,
            username=username_filter,
        )

    except Exception as e:
        return f"An error occurred: {e}", 500
    finally:
        db.close()


if __name__ == "__main__":
    # You can run this simple app using `python your_file_name.py`
    # It will be accessible at http://127.0.0.1:5000/message_volume
    app.run(host="0.0.0.0", port=5234, debug=True)

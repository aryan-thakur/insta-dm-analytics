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


@app.route("/message_comparison")
def message_comparison():
 """
 Displays a Plotly pie chart comparing the proportion of messages
 sent by "self" and "unknown" within a conversation and date range.
 """
db = SessionLocal()
 conversation_username = request.args.get("conversation_username")
 start_date_str = request.args.get("start_date")
 end_date_str = request.args.get("end_date")

 if not conversation_username:
 return (
 "Please provide 'conversation_username', 'start_date', and 'end_date' parameters.",
 400,
 )

 try:
 # Base query filtered by conversation and date range
 query = db.query(Message).filter(
 Message.conversation_username == conversation_username
 )
 if start_date_str:
 query = query.filter(Message.timestamp_iso >= start_date_str)
 if end_date_str:
 query = query.filter(Message.timestamp_iso <= end_date_str)

 # Count messages for "self" and "unknown"
 self_count = query.filter(Message.sender == "self").count()
 unknown_count = query.filter(Message.sender == "unknown").count()

 total_messages = self_count + unknown_count

 if total_messages == 0:
 return "No messages found for the specified criteria.", 404

 labels = ["Self", "Unknown"]
 values = [self_count, unknown_count]

 # Create a pie chart
 fig = go.Figure(
 data=[
 go.Pie(
 labels=labels,
 values=values,
 hoverinfo="label+percent",
 textinfo="value",
 insidetextorientation="radial",
 ),
 ]
 )

 # Update layout
 fig.update_layout(
 title=f'Message Proportion for "{conversation_username}"<br>({start_date_str} to {end_date_str})',
 )

 # Convert to HTML
 graph_html = pio.to_html(fig, full_html=False)

 return render_template_string(
 """
 <h1>Message Proportion Analysis</h1>
 <p>Analyzing messages in conversation "{{ conversation_username }}" from {{ start_date }} to {{ end_date }}.</p>
 <div>
 {{ graph_html | safe }}
 </div>
 )

 fig.update_layout(
 barmode="group",
 title=f'Message Comparison for "{conversation_username}" (unknown vs conversation username)',
 xaxis_title="Month",
 yaxis_title="Number of Messages",
 )

 graph_html = pio.to_html(fig, full_html=False)

 return render_template_string(
 """
 <h1>Message Comparison Analysis</h1>
 """, # Remove the previous template
 graph_html=graph_html,
 conversation_username=conversation_username,
 start_date=start_date_str,
 end_date=end_date_str,
 )

 except Exception as e:
 return f"An error occurred: {e}", 500
 finally:
 db.close()


if __name__ == "__main__":
    # You can run this simple app using `python your_file_name.py`
    # It will be accessible at http://127.0.0.1:5000/message_volume
    app.run(host="0.0.0.0", port=5234, debug=True)

from datetime import datetime
import statistics
from flask import Blueprint, request, jsonify
from sqlalchemy import func
import plotly.graph_objs as go
import pandas as pd
from collections import Counter
from backend.config import SessionLocal
from backend.models import Message
from sqlalchemy import or_

v1 = Blueprint("v1", __name__)


@v1.route("/message_volume")
def message_volume():
    """
    Displays a Plotly graph of message volume per month, filterable by username.
    """
    db = SessionLocal()
    username_filter = request.args.get("username")  # Get username from query parameter

    try:
        query = db.query(
            func.strftime("%Y-%m", Message.timestamp_iso_dt).label(
                "month"
            ),  # Use timestamp_iso
            func.count().label("message_count"),
        ).group_by("month")

        if username_filter and username_filter != "all":
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

        return jsonify(
            {
                "title": "Message Volume Analysis",
                "username_filter": username_filter,
                "figure": fig.to_plotly_json(),
            }
        )

    except Exception as e:
        return f"An error occurred: {e}", 500
    finally:
        db.close()


@v1.route("/word_cloud")
def word_cloud():
    """
    Analyzes messages for a given username and date range to find the most frequent words.
    """
    db = SessionLocal()
    username = request.args.get("username")
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    if not username or not start_date_str or not end_date_str:
        return (
            "Please provide 'username', 'start_date', and 'end_date' parameters.",
            400,
        )

    try:
        # Base query filtered by conversation and date range
        query = db.query(Message.message).filter(
            Message.conversation_username == username,
            Message.timestamp_iso_dt >= start_date_str,
            Message.timestamp_iso_dt <= end_date_str,
        )
        # Exclude messages that are reactions, have attachments, or are audio/photo/video
        query = query.filter(
            ~Message.message.like("Reacted % to your message"),
            or_(Message.attachment.is_(None), Message.attachment.isnot(True)),
            or_(Message.audio.is_(None), Message.audio.is_(False)),
            or_(Message.photo.is_(None), Message.photo.is_(False)),
            or_(Message.video.is_(None), Message.video.is_(False)),
        )

        messages = query.all()

        if not messages:
            return jsonify({"top_words": []})

        # Combine all messages into a single string
        all_messages_text = " ".join([m[0] for m in messages if m[0]])

        # Simple tokenization and lowercasing
        words = all_messages_text.lower().split()

        # Define common English stop words (can be expanded)
        stop_words = set(
            [
                "the",
                "a",
                "an",
                "is",
                "it",
                "in",
                "on",
                "at",
                "for",
                "with",
                "and",
                "or",
                "but",
                "not",
                "i",
                "you",
                "he",
                "reacted",
                "message",
                "sent",
                "she",
                "it",
                "we",
                "they",
                "my",
                "your",
                "his",
                "her",
                "its",
                "our",
                "their",
                "to",
                "of",
                "from",
                "by",
                "as",
                "so",
                "that",
                "this",
                "these",
                "those",
                "be",
                "am",
                "are",
                "was",
                "were",
                "been",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "can",
                "could",
                "will",
                "would",
                "get",
                "like",
            ]
        )

        # Filter out stop words and punctuation
        filtered_words = [
            word for word in words if word not in stop_words and word.isalnum()
        ]

        # Count word frequencies
        word_counts = Counter(filtered_words)

        # Get the top 5 most frequent words
        top_words = word_counts.most_common(5)

        return jsonify(
            {"top_words": [{"word": word, "count": count} for word, count in top_words]}
        )

    except Exception as e:
        return f"An error occurred: {e}", 500
    finally:
        db.close()


@v1.route("/message_volume_by_period")
def message_volume_by_period():
    """
    Calculates and displays the message volume by time period for a given
    username and date range.
    """
    db = SessionLocal()
    username_filter = request.args.get("username")
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    if not username_filter or not start_date_str or not end_date_str:
        return (
            "Please provide 'username', 'start_date', and 'end_date' parameters.",
            400,
        )

    try:
        # Query only the columns we actually use: timestamp_iso_dt and sender
        query = db.query(Message.timestamp_iso_dt, Message.sender).filter(
            Message.conversation_username == username_filter,
            Message.timestamp_iso_dt >= start_date_str,
            Message.timestamp_iso_dt <= end_date_str,
        )
        messages = query.all()

        # Initialize volume counts for each period and sender
        volume_by_period = {
            "12 AM - 6 AM": {"self": 0, "unknown": 0, "total": 0},
            "6 AM - 12 PM": {"self": 0, "unknown": 0, "total": 0},
            "12 PM - 6 PM": {"self": 0, "unknown": 0, "total": 0},
            "6 PM - 12 AM": {"self": 0, "unknown": 0, "total": 0},
        }

        for message in messages:
            try:
                timestamp = message.timestamp_iso_dt
                hour = timestamp.hour
                sender = message.sender

                if 0 <= hour < 6:
                    period = "12 AM - 6 AM"
                elif 6 <= hour < 12:
                    period = "6 AM - 12 PM"
                elif 12 <= hour < 18:
                    period = "12 PM - 6 PM"
                elif 18 <= hour < 24:
                    period = "6 PM - 12 AM"
                else:
                    continue  # Should not happen

                volume_by_period[period]["total"] += 1
                if sender in volume_by_period[period]:
                    volume_by_period[period][sender] += 1

            except Exception:
                # Skip messages with invalid timestamps
                continue

        # Prepare data for Plotly chart
        periods = list(volume_by_period.keys())
        self_volumes = [volume_by_period[p]["self"] for p in periods]
        unknown_volumes = [volume_by_period[p]["unknown"] for p in periods]

        fig = go.Figure(
            data=[
                go.Bar(name="Self", x=periods, y=self_volumes),
                go.Bar(name="Unknown", x=periods, y=unknown_volumes),
            ]
        )
        fig.update_layout(
            barmode="group",
            title=f'Message Volume by Period for "{username_filter}"<br>({start_date_str} to {end_date_str})',
            xaxis_title="Time Period",
            yaxis_title="Number of Messages",
        )

        return jsonify(
            {
                "title": "Message Volume by Period Analysis",
                "description": f'Analyzing messages for username "{username_filter}" from {start_date_str} to {end_date_str}.',
                "username": username_filter,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "figure": fig.to_plotly_json(),  # Use this instead of HTML!
                "volume_data": volume_by_period,  # This is your raw backend data, JSON-serializable
            }
        )

    except Exception as e:
        return f"An error occurred: {e}", 500
    finally:
        db.close()


@v1.route("/message_comparison")
def message_comparison():
    """
    Displays a Plotly pie chart comparing the proportion of messages
    sent by "self" and "unknown" within a conversation and date range.
    """
    db = SessionLocal()
    conversation_username = request.args.get("username")
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    if not conversation_username:
        return (
            "Please provide 'username', 'start_date', and 'end_date' parameters.",
            400,
        )

    try:
        # Base query filtered by conversation and date range
        # Initialize base query
        query = db.query(Message)
        if conversation_username and conversation_username != "all":
            query = query.filter(Message.conversation_username == conversation_username)
        if start_date_str:
            query = query.filter(Message.timestamp_iso_dt >= start_date_str)
        if end_date_str:
            query = query.filter(Message.timestamp_iso_dt <= end_date_str)

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
            title=f'Message Proportion for "{conversation_username if conversation_username != "all" else "All Conversations"}"<br>({start_date_str} to {end_date_str})',
        )

        fig_json = fig.to_plotly_json()
        return jsonify(
            {
                "figure": fig_json,
                "meta": {
                    "username": conversation_username,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                },
            }
        )

    except Exception as e:
        return f"An error occurred: {e}", 500
    finally:
        db.close()


@v1.route("/average_response_time")
def average_response_time():
    """
    Calculates and displays the average response time for a given conversation and date.
    """
    # Get query parameters
    conversation_username = request.args.get("username")
    start_str = request.args.get("start_date")
    end_str = request.args.get("end_date")

    start_dt = start_str if start_str else "Start date not provided"
    end_dt = end_str if end_str else "End date not provided"

    if not conversation_username or not start_str or not end_str:
        return "Missing required query parameters", 400

    db = SessionLocal()
    try:
        # Compare as strings because the column is String
        messages = (
            db.query(Message.timestamp_iso_dt, Message.sender)
            .filter(
                Message.conversation_username == conversation_username,
                Message.timestamp_iso_dt >= start_str,
                Message.timestamp_iso_dt <= end_str,
            )
            .order_by(Message.timestamp_iso_dt)
            .all()
        )

        prev_sender = None
        prev_time = None
        response_durations = {"self": [], "unknown": []}

        for ts, sender in messages:
            if ts is None or sender is None:
                continue
            try:
                cur_time = ts
            except Exception:
                continue

            if prev_sender and prev_sender != sender:
                delta = (cur_time - prev_time).total_seconds()
                response_durations[sender].append(delta)
            prev_sender = sender
            prev_time = cur_time

        MAX_SECONDS = 86400  # 1 day

        # Filter out values > 1 day for average calculation
        filtered_self = [d for d in response_durations["self"] if d <= MAX_SECONDS]
        filtered_unknown = [
            d for d in response_durations["unknown"] if d <= MAX_SECONDS
        ]

        # Median includes all values
        median_self = (
            statistics.median(response_durations["self"])
            if response_durations["self"]
            else None
        )
        median_unknown = (
            statistics.median(response_durations["unknown"])
            if response_durations["unknown"]
            else None
        )

        # Average (mean), excluding outliers
        avg_self = sum(filtered_self) / len(filtered_self) if filtered_self else None
        avg_unknown = (
            sum(filtered_unknown) / len(filtered_unknown) if filtered_unknown else None
        )

        return jsonify(
            {
                "conversation_username": conversation_username,
                "start_dt": start_dt,
                "end_dt": end_dt,
                "avg_self": round(avg_self, 2) if avg_self is not None else None,
                "median_self": (
                    round(median_self, 2) if median_self is not None else None
                ),
                "avg_unknown": (
                    round(avg_unknown, 2) if avg_unknown is not None else None
                ),
                "median_unknown": (
                    round(median_unknown, 2) if median_unknown is not None else None
                ),
            }
        )

    except Exception as e:
        return f"An error occurred: {e}", 500
    finally:
        db.close()

# instagram_analyzer/src/.py

from datetime import datetime
import os
from sqlalchemy import (
    create_engine,
    text,
    Table,
    Column,
    Integer,
    String,
    MetaData,
    select,
    update,
    bindparam,
)
from sqlalchemy.exc import SQLAlchemyError

# --- Configuration ---
# The database file will be created in the root of your project directory
# because we mounted '.' on the host to '/app' in the container, and our
# working directory in the container is '/app'.
DATABASE_FILENAME = os.environ.get("DATABASE_FILENAME")
DATABASE_PATH = os.path.join("/app", DATABASE_FILENAME)  # Path inside the container
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# --- Database Connection ---
# Use SQLAlchemy's engine for connection management
# `echo=True` will print the SQL commands being executed, useful for debugging
engine = create_engine(DATABASE_URL, echo=False)

metadata = MetaData()
your_table = Table(
    "messages",
    metadata,
    Column("id", Integer, primary_key=True),  # Adjust type if PK is not Integer
    Column("timestamp", String),
    Column("timestamp_iso", String),
    # Add other columns if you want to reflect the whole table, or use autoload_with=engine
)


def add_message_row(data):
    """
    Adds a row to the 'messages' table in the SQLite database.

    Args:
        data (dict): A dictionary containing the column names as keys and their respective values.
    """
    insert_query = text(
        """
        INSERT INTO messages (
        conversation_username, sender, message, timestamp, story_reply, liked, timestamp_liked,
            attachment, attachment_link, reference_account, audio, video, photo
        ) VALUES (
            :conversation_username, :sender, :message, :timestamp, :story_reply, :liked, :timestamp_liked,
            :attachment, :attachment_link, :reference_account, :audio, :video, :photo
        )
    """
    )
    try:
        with engine.begin() as connection:  # engine.begin() handles transaction + commit
            connection.execute(insert_query, data)
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        exit(-1)


def add_conversation_row(data):
    """
    Adds a row to the 'conversations' table in the SQLite database.

    Args:
        data (dict): A dictionary containing the column names as keys and their respective values.
    """
    insert_query = text(
        """
                    INSERT INTO conversations (
                        username, name
                    ) VALUES (
                        :username, :name
                    )
                    """
    )
    try:
        with engine.begin() as connection:  # engine.begin() handles transaction + commit
            connection.execute(insert_query, data)
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        exit(-1)


def generate_timestamp_iso():
    print("Generating ISO timestamps...")
    rows_to_process = []

    # Phase 1: Read data that needs conversion
    # We use engine.connect() here as it's a read-only operation for now.
    # The actual update will be in an engine.begin() block

    with engine.connect() as connection:
        # Select rows where the new timestamp column is NULL (to avoid re-processing)
        # and the old timestamp column is NOT NULL
        stmt_select = select(
            your_table.c["id"],  # Use .c to access columns of a Table object
            your_table.c["timestamp"],
        ).where(
            your_table.c["timestamp_iso"].is_(None),
            your_table.c["timestamp"].is_not(None),
        )

        result = connection.execute(stmt_select)
        rows_to_process = result.fetchall()  # Fetches all rows as tuples

    if not rows_to_process:
        print("No timestamps found to convert or all are already converted.")
        return

    updates_for_db = []
    print(f"Found {len(rows_to_process)} rows to process.")

    for pk_value, old_ts_str in rows_to_process:
        if not old_ts_str:  # Should be caught by IS NOT NULL, but good for safety
            print(
                f"Skipping PK {pk_value} due to empty old timestamp (should not happen with query)."
            )
            continue

        try:
            # Parse the old timestamp string
            dt_object = datetime.strptime(old_ts_str, "%b %d, %Y %I:%M %p")
            # Format it to ISO 8601 ("YYYY-MM-DD HH:MM:SS")
            iso_ts_str = dt_object.strftime("%Y-%m-%d %H:%M:%S")

            # Prepare data for executemany-style update
            # The keys here ('_pk', '_new_ts') will be used with bindparam
            updates_for_db.append({"_pk": pk_value, "_new_ts": iso_ts_str})

        except ValueError as e:
            print(f"Error parsing timestamp '{old_ts_str}' for PK {pk_value}: {e}")
        except TypeError as e:
            print(
                f"TypeError for timestamp '{old_ts_str}' (possibly None) for PK {pk_value}: {e}"
            )

    if not updates_for_db:
        print("No valid timestamps could be parsed for update.")
        return

    # Phase 2: Batch update the database using your preferred style
    try:
        # Define the update statement using SQLAlchemy Core and bindparams
        # This allows SQLAlchemy to perform an "executemany" efficiently.
        stmt_update = (
            update(your_table)
            .where(
                your_table.c["id"] == bindparam("_pk")
            )  # Matches key in 'updates_for_db' dict
            .values(
                {"timestamp_iso": bindparam("_new_ts")}
            )  # Matches key in 'updates_for_db' dict
        )
        # For rowid: .where(column('rowid') == bindparam('_pk'))

        with engine.begin() as connection:  # Handles transaction + commit/rollback
            connection.execute(stmt_update, updates_for_db)
        print(
            f"Successfully updated {len(updates_for_db)} rows with standardized timestamps."
        )

    except Exception as e:  # Catch generic SQLAlchemy errors or others
        print(f"An error occurred during database update: {e}")
        # The 'engine.begin()' context manager will automatically roll back on exception.


if __name__ == "__main__":
    generate_timestamp_iso()

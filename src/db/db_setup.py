# instagram_analyzer/src/.py

import os
from sqlalchemy import create_engine, text

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


def drop_tables():
    """Drops the 'messages' and 'conversations' tables if they exist."""
    print(f"Connecting to database at: {DATABASE_URL}")
    try:
        with engine.begin() as connection:
            drop_conversation_table_sql = text(
                """
                DROP TABLE IF EXISTS conversations;
                """
            )
            connection.execute(drop_conversation_table_sql)
            drop_table_sql = text(
                """
                DROP TABLE IF EXISTS messages;
                """
            )
            connection.execute(drop_table_sql)
        print("✅ Tables dropped successfully.")
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        exit(-1)


def initialize_database():
    """Creates a simple 'messages' table if it doesn't exist."""
    print(f"Connecting to database at: {DATABASE_URL}")
    try:
        with engine.begin() as connection:
            # Use 'text' for raw SQL execution with SQLAlchemy
            create_conversation_table_sql = text(
                """
                CREATE TABLE conversations (
                username TEXT PRIMARY KEY,   
                name TEXT,                   
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
                """
            )
            connection.execute(create_conversation_table_sql)
            create_table_sql = text(
                """
                CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_username TEXT NOT NULL REFERENCES conversations(username),
                sender TEXT,
                message TEXT,
                timestamp DATETIME,
                story_reply TEXT,
                liked BOOLEAN,
                timestamp_liked DATETIME,
                attachment TEXT,
                attachment_link TEXT,
                reference_account TEXT,
                audio BOOLEAN,
                photo BOOLEAN,
                video BOOLEAN
                );
                """
            )
            connection.execute(create_table_sql)
            # Commit is often implicit with execute in autocommit mode or when block ends,
            # but can be explicit if needed: connection.commit()
        print(
            "✅ Database initialized successfully (table 'messages' checked/created)."
        )
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        exit(-1)

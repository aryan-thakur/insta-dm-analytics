# instagram_analyzer/src/main.py

from db.db_main import add_conversation_row, add_message_row
from db.db_setup import initialize_database
from db.db_setup import drop_tables
import os
from parsing.parser import parse_html_file

if __name__ == "__main__":
    print("Running main script...")
    print("Choose an option or enter any other key to skip:")
    print("1. Drop tables")
    print("2. Initialize database")
    print("3. Drop tables and then initialize database")

    choice = input("Enter your choice (1/2/3): ")

    if choice == "1":
        drop_tables()
    elif choice == "2":
        initialize_database()
    elif choice == "3":
        drop_tables()
        initialize_database()
    else:
        print("Skipping.")

    instagram_names = {}

    with open("usernames.txt", "r") as file:
        for line in file:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                instagram_names[key] = value

    base_path = "../data/instagram-aryanthakxr/your_instagram_activity/messages/inbox"

    for subdir_name in os.listdir(base_path):
        if (subdir_name.split("_")[0] in instagram_names) and instagram_names[
            subdir_name.split("_")[0]
        ] not in [
            "bot",
            "group",
        ]:
            full_subdir_path = os.path.join(base_path, subdir_name)

            if os.path.isdir(full_subdir_path):
                # Find which prefix (if any) matches this subdir
                matching_prefix = next(
                    (
                        prefix
                        for prefix in instagram_names.keys()
                        if subdir_name.startswith(prefix)
                    ),
                    None,
                )

                if matching_prefix:
                    print("Processing:", matching_prefix)
                    conversation_data = {
                        "username": instagram_names[matching_prefix],
                        "name": matching_prefix,
                    }
                    add_conversation_row(conversation_data)

                    for file_name in os.listdir(full_subdir_path):
                        if file_name.endswith(".html"):
                            full_path = os.path.join(full_subdir_path, file_name)
                            data_list = parse_html_file(full_path)
                            for data in data_list:
                                if data:
                                    data["conversation_username"] = instagram_names[
                                        matching_prefix
                                    ]
                                    # print(data)
                                    add_message_row(data)

    print("Main script finished.")

from bs4 import BeautifulSoup


def parse_html_file(file_path):
    """
    Opens an HTML file and parses it using BeautifulSoup with the lxml parser.

    Args:
        file_path (str): The path to the HTML file to be parsed.

    Returns:
        BeautifulSoup: A BeautifulSoup object representing the parsed HTML.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            soup = BeautifulSoup(content, "lxml")
            # Remove the head section
            if soup.head:
                soup.head.decompose()

            # Find all divs with the class 'uiBoxWhite' in the body
            divs = soup.body.find_all("div", class_="uiBoxWhite")

            extracted_data = []

            for div in divs:
                # Extract sender
                sender_div = div.find("div", class_="_3-95 _2pim _a6-h _a6-i")
                sender = sender_div.get_text(strip=True) if sender_div else None
                if sender and sender.startswith("Aryan Thakur"):
                    sender = "self"
                else:
                    sender = "unknown"

                # Extract message
                message = None
                wrapper_div = div.find("div", class_="_3-95 _a6-p")
                if wrapper_div:
                    inner_wrapper = wrapper_div.find(
                        "div"
                    )  # No class, just the first inner <div>
                    if inner_wrapper:
                        sibling_divs = inner_wrapper.find_all("div", recursive=False)
                        if len(sibling_divs) > 1:
                            message = sibling_divs[1].get_text(strip=True)

                # Extract timestamp (from parent div, not wrapper)
                timestamp_div = div.find("div", class_="_3-94 _a6-o")
                timestamp = (
                    timestamp_div.get_text(strip=True) if timestamp_div else None
                )

                # Check if the div contains an anchor tag with href containing "/stories/"
                story_reply = False
                anchor_tag = div.find("a", href=True)
                if anchor_tag and "/stories/aryanthakxr" in anchor_tag["href"]:
                    story_reply = True

                # Check if the div contains a <span> tag
                liked = False
                timestamp_liked = None
                span_tag = div.find("span")
                if span_tag:
                    liked = True
                    # Extract timestamp from the child <span> tag
                    timestamp_span = span_tag.find("span")
                    if timestamp_span:
                        timestamp_liked = timestamp_span.get_text(strip=True)
                        if (
                            timestamp_liked
                            and timestamp_liked.startswith("(")
                            and timestamp_liked.endswith(")")
                        ):
                            timestamp_liked = timestamp_liked[
                                1:-1
                            ]  # Remove the surrounding parentheses

                reference_account = None

                if wrapper_div:
                    inner_wrapper = wrapper_div.find("div")
                    if inner_wrapper:
                        sibling_divs = inner_wrapper.find_all("div", recursive=False)
                        if len(sibling_divs) >= 3:
                            container_div = sibling_divs[2]
                            anchor_tag = container_div.find("a", href=True)
                            if anchor_tag and "/stories/" in anchor_tag["href"]:
                                message = "Sent a story"

                                # Extract username from href
                                href = anchor_tag["href"]
                                parts = href.split("/stories/")
                                if len(parts) > 1:
                                    reference_account = parts[1].split("/")[0]

                audio = False

                # Check if the div contains an <audio> tag
                if div.find("audio"):
                    audio = True
                    message = "Sent a voice recording"

                video = False

                # Check if the div contains a <video> tag
                if div.find("video"):
                    video = True
                    message = "Sent a video"

                photo = False

                # Check if the div contains an <img> tag
                if div.find("img"):
                    photo = True
                    message = "Sent a photo"

                attachment = False
                attachment_link = None

                # Check if the message contains "sent an attachment."
                if message and "sent an attachment." in message.lower():
                    attachment = True

                # Find an anchor tag with /reel/ or /p/ in the href
                anchor_tag = div.find("a", href=True)
                if anchor_tag and (
                    "/reel/" in anchor_tag["href"] or "/p/" in anchor_tag["href"]
                ):
                    attachment_link = anchor_tag["href"]

                # Skip if the message starts with a Hindi/Devanagari character
                if message and ord(message[0]) in range(0x0900, 0x097F):
                    continue
                if message and message.startswith("Liked a message"):
                    continue

                extracted_data.append(
                    {
                        "sender": sender,
                        "message": message,
                        "timestamp": timestamp,
                        "story_reply": story_reply,
                        "liked": liked,
                        "timestamp_liked": timestamp_liked if liked else None,
                        "attachment": attachment,
                        "attachment_link": attachment_link,
                        "reference_account": reference_account,
                        "audio": audio,
                        "video": video,
                        "photo": photo,
                    }
                )

            if not extracted_data:
                print(f"No divs found!")
                exit(-1)

            return extracted_data

    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Pure testing
    parsed_divs = parse_html_file(
        "../../data/instagram-aryanthakxr-2025-04-26-7b2E1Ht0/your_instagram_activity/messages/inbox/rohilkishinchandani_825301365535178/message_1.html"
    )
    if parsed_divs:
        for i, div in enumerate(parsed_divs, start=1):
            print(f"Div {i}: {div}")

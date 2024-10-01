
import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
from config import ADMINS, CUSTOM_CAPTION, CD_CHANNEL, CHANNEL_ID
from helper_func import encode, get_message_id
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
import asyncio

# Helper function to clean the caption
def clean_caption(caption):
    # Remove words starting with # or @, and URLs
    caption = re.sub(r'\s?[@#]\S+', '', caption)
    caption = re.sub(r'http\S+', '', caption)
    return caption

@StreamBot.on_message(filters.private & filters.user(ADMINS) & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            # Prompt the user to provide the first message from the DB Channel
            first_message = await client.ask(
                text="Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return  # Return if there's an exception (e.g., timeout)

        # Get the message ID from the provided message or link
        f_msg_id = await get_message_id(client, first_message)

        if f_msg_id:
            break
        else:
            # Inform the user of an error if the message/link is not from the DB Channel
            await first_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote=True)
            continue

    while True:
        try:
            # Prompt the user to provide the last message from the DB Channel
            second_message = await client.ask(
                text="Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link",
                chat_id=message.from_user.id,
                filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                timeout=60
            )
        except:
            return  # Return if there's an exception (e.g., timeout)

        # Get the message ID from the provided message or link
        s_msg_id = await get_message_id(client, second_message)

        if s_msg_id:
            break
        else:
            # Inform the user of an error if the message/link is not from the DB Channel
            await second_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote=True)
            continue

    xyz = "{{botUsername}}"
    message_links = []
    for msg_id in range(min(f_msg_id, s_msg_id), max(f_msg_id, s_msg_id) + 1):
        try:
            string = f"get-{msg_id * abs(client.db_channel.id)}"
            base64_string = await encode(string)
            link = f"https://t.me/{client.username}?start={base64_string}"
            linka = f"https://t.me/{xyz}?start={base64_string}"
            message_links.append((linka, msg_id))  # Append a tuple with link and msg_id
        except Exception as e:
            await message.reply(f"Error generating link for message {msg_id}: {e}")

    # PART 1: Send the generated links and captions to the CHANNEL_ID (Code 1 functionality)
    for linka, msg_id in message_links:
        try:
            # Fetch the message object for the current msg_id
            current_message = await client.get_messages(client.db_channel.id, msg_id)

            # Determine the caption for this message
            if bool(CUSTOM_CAPTION) and current_message.document:
                raw_caption = "" if not current_message.caption else current_message.caption.html
                cleaned_caption = clean_caption(raw_caption)
                caption = CUSTOM_CAPTION.format(
                    previouscaption=cleaned_caption,
                    filename=current_message.document.file_name
                )
            else:
                raw_caption = "" if not current_message.caption else current_message.caption.html
                caption = clean_caption(raw_caption)

            # Send the caption followed by the link to CHANNEL_ID
            try:
                await client.send_message(chat_id=CHANNEL_ID, text=f"{caption}\n{linka}")
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await client.send_message(chat_id=CHANNEL_ID, text=f"{caption}\n{linka}")

        except Exception as e:
            await message.reply(f"Error processing message {msg_id}: {e}")

    # PART 2: Further process the links and captions to clean and send them to the user (Code 2 functionality)
    for linka, msg_id in message_links:
        try:
            # Fetch the message object for the current msg_id
            current_message = await client.get_messages(client.db_channel.id, msg_id)

            # Clean and format the caption for the user
            if bool(CUSTOM_CAPTION) and current_message.document:
                caption = CUSTOM_CAPTION.format(
                    previouscaption="" if not current_message.caption else current_message.caption.html,
                    filename=current_message.document.file_name
                )
            else:
                caption = "" if not current_message.caption else current_message.caption.html

            clean_caption = re.sub(r'https?://[^\s]+', '', caption).strip()

            # Send the cleaned caption followed by the link to the user who triggered the batch command
            try:
                await client.send_message(chat_id=message.from_user.id, text=f"{clean_caption}\n{linka}")
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await client.send_message(chat_id=message.from_user.id, text=f"{clean_caption}\n{linka}")

        except Exception as e:
            await message.reply(f"Error processing message {msg_id}: {e}")

    # Inform the user that batch processing is completed
    await message.reply("Batch processing completed.")


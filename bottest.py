import requests
import logging
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

BOT_TOKEN = '8142388383:'
BOT_USERNAME = 'QafaryBot'  # Bot's username without '@'

def get_chat_id(bot_token, bot_username):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError for bad responses
        data = response.json()
        
        # Pretty-print the entire JSON response
        pretty_json = json.dumps(data, indent=4)
        logging.debug(f"Telegram API response:\n{pretty_json}")
        
        for result in data.get('result', []):
            message = result.get('message', {})
            from_user = message.get('from', {})
            username = from_user.get('username')
            if username == bot_username:
                chat_id = message.get('chat', {}).get('id')
                logging.debug(f"Found Chat ID: {chat_id} for username: {username}")
                return chat_id
        logging.warning("No matching messages found for the specified bot username.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching updates from Telegram API: {e}")
    except ValueError as ve:
        logging.error(f"Error parsing JSON response: {ve}")
    return None

def get_all_updates_pretty(bot_token):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Pretty-print the entire JSON response
        pretty_json = json.dumps(data, indent=4)
        print(pretty_json)
        
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching updates from Telegram API: {e}")
    except ValueError as ve:
        logging.error(f"Error parsing JSON response: {ve}")
    return None

if __name__ == "__main__":
    # Method 1: Retrieve Chat ID by matching bot username
    chat_id = get_chat_id(BOT_TOKEN, BOT_USERNAME)
    print(f"Your Chat ID is: {chat_id}")
    
    # Method 2: Optionally, retrieve and display all updates in a pretty format
    # Uncomment the following lines if you want to see all updates nicely formatted
    updates = get_all_updates_pretty(BOT_TOKEN)
    if updates:
        print(json.dumps(updates, indent=4))
    else:
        print("No updates received.")


# import requests
# import logging

# # Configure logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

# BOT_TOKEN = '8142388383:'
# BOT_USERNAME = 'QafaryBot'  # Bot's username without '@'

# def get_chat_id(bot_token, bot_username):
#     url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
#     try:
#         response = requests.get(url)
#         response.raise_for_status()  # Raises HTTPError for bad responses
#         data = response.json()
#         logging.debug(f"Telegram API response: {data}")
#         for result in data.get('result', []):
#             message = result.get('message', {})
#             from_user = message.get('from', {})
#             username = from_user.get('username')
#             if username and username != bot_username:
#                 chat_id = message.get('chat', {}).get('id')
#                 logging.debug(f"Found Chat ID: {chat_id} for username: {username}")
#                 return chat_id
#         logging.warning("No matching messages found for the specified bot username.")
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Error fetching updates from Telegram API: {e}")
#     except ValueError as ve:
#         logging.error(f"Error parsing JSON response: {ve}")
#     return None

# chat_id = get_chat_id(BOT_TOKEN, BOT_USERNAME)
# print(f"Your Chat ID is: {chat_id}")


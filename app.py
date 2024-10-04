from bson.objectid  import ObjectId
import json
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for
from moderation_model import ModerationModel
from database_manager import DatabaseManager

from status_package import Status

from log import logger
from config import Config

# Initialization
config = Config()
processed_comments = set()
app = Flask(__name__)

Status(app, config.MONGO_URI)

# MongoDB setup
client = DatabaseManager().get_instance()
db = client.get_db()
comments_collection = db['comments']

db_2 = client.get_db("HaSpDeDash")

# Use configurations from config
INSTAGRAM_ACCESS_TOKEN = config.INSTAGRAM_ACCESS_TOKEN
INSTAGRAM_API_VERSION = config.INSTAGRAM_API_VERSION
INSTAGRAM_VERIFY_TOKEN = config.INSTAGRAM_VERIFY_TOKEN
IMPROVE = config.IMPROVE
HUMAN_REVIEW = config.HUMAN_REVIEW
ERROR_STATUS = json.dumps({'status': 'error'}), 200

# Load models that we need
moderation_model = ModerationModel(IMPROVE, HUMAN_REVIEW, certainty_needed=config.CERTAINTY_NEEDED)

def update_skipped_comments():
    """Update comments with status 'skipped' to 'PENDING_REVIEW'."""
    logger.info("Checking for comments with status 'skipped' to update to 'PENDING_REVIEW'.")

    try:
        result = comments_collection.update_many(
            {'status': 'SKIPPED'},
            {'$set': {'status': 'PENDING_REVIEW', 'updated_at': datetime.utcnow()}}
        )
        logger.info(f"Updated {result.modified_count} comments from 'skipped' to 'PENDING_REVIEW'.")
    except Exception as e:
        logger.error(f"Error updating comments: {e}")

# Set up the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_skipped_comments, trigger="interval", minutes=15)
scheduler.start()

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """
    Handle incoming webhook requests for verification and event processing.
    Returns:
    Response: JSON response based on the request type.
    """
    data = "\n=== New Request ==="
    data += f"Request Method: {request.method}\n"
    data += f"Request Headers: {request.headers}\n"
    data += f"Request Args: {request.args}\n"
    data += f"Request Data (raw): {request.data.decode('utf-8')}\n"
    logger.debug(data)

    if request.method == 'GET':
        return handle_verification(request)

    elif request.method == 'POST':
        return handle_webhook_event(request)

    # If the request method is neither GET nor POST
    return method_not_allowed()

def handle_verification(request):
    """
    Verify the Instagram webhook subscription.
    Parameters:
    request (flask.Request): The incoming request containing verification parameters.
    Returns:
    Response: A plain text response with the challenge code on success or a JSON error message on failure.
    """
    # Extract verification parameters from the request
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    # Verify the subscription request
    if mode == 'subscribe' and token == INSTAGRAM_VERIFY_TOKEN:
        logger.info("Instagram verification successful!")
        return challenge, 200  # Return the challenge code for verification

    logger.critical("Invalid verification token!")
    return jsonify({'error': 'Invalid verification token'}), 403  # Return an error response

def handle_webhook_event(request):
    """
    Handle incoming webhook events from Facebook and Instagram and process comments.
    
    Parameters:
    request (flask.Request): The incoming request containing webhook data.
    
    Returns:
    Response: A JSON response indicating the status of the operation.
    """
    # Parse JSON data from the request
    data = request.json
    logger.debug("Received webhook data:")
    logger.debug(json.dumps(data, indent=2))  # Pretty-print the received data for debugging

    # Process Facebook Page events
    if data.get("object") == "page":
        logger.info("The comment is facebook")

        for entry in data.get("entry", []):
            print(entry)
            if 'changes' in entry and isinstance(entry['changes'], list):
                for change in entry['changes']:
                    if change.get('field') == 'feed' and 'value' in change:
                        comment_data = change['value']
                        if comment_data.get('item') == 'comment':
                            process_facebook_comment(comment_data)
                        
                        if comment_data.get("item") == 'reaction':
                            logger.debug("Received reaction")

    # Process Instagram events
    elif data.get('object') == 'instagram':
        logger.info("The comment is instagram")

        for entry in data.get('entry', []):
            if 'changes' in entry and isinstance(entry['changes'], list):
                for change in entry['changes']:
                    if change.get('field') == 'comments' and 'value' in change:
                        comment_data = change['value']
                        process_instagram_comment(comment_data)

    else:
        logger.error("CRITICAL ERROR")

    return jsonify({'status': 'ok'}), 200
def process_facebook_comment(comment_data):
    """
    Process a Facebook comment and store it in the database.
    
    Parameters:
    comment_data (dict): The data of the Facebook comment from the webhook.
    """
    # Check if the comment_data contains the necessary fields
    if comment_data.get('item') == 'comment':
        comment_id = comment_data.get('comment_id')
        comment_text = comment_data.get('message', '')
        post_id = comment_data.get('post_id')
        user_id = comment_data['from']['id']
        user_name = comment_data['from'].get('name', 'Unknown User')
        platform = 'facebook'

        # Extract owner ID from the post_id (i.e., the part before the underscore)
        owner_id = post_id.split('_')[0] if post_id else None

        # Ensure comment_id is present before proceeding
        if comment_id:
            # Store comment in MongoDB if it doesn't already exist
            if not comments_collection.find_one({'id': comment_id}):
                comment_to_db(comment_id, comment_text, platform, user_id, user_name, post_id)

            # Pass the owner_id to the moderation model
            if not HUMAN_REVIEW:
                handle_comment(comment_data, owner_id)
        else:
            logger.error("Comment ID is missing in the comment data.")


def process_instagram_comment(comment_data):
    """
    Process an Instagram comment and store it in the database.
    
    Parameters:
    comment_data (dict): The data of the Instagram comment from the webhook.
    """
    # Extract necessary data from the comment_data
    comment_id = comment_data.get('id')
    comment_text = comment_data.get('text', '')
    user_id = comment_data['from']['id']
    user_name = comment_data['from'].get('username', 'Unknown User')
    media_id = comment_data['media']['id']
    platform = 'instagram'

    # Ensure comment_id is present before proceeding
    if comment_id:
        owner_id = get_instagram_owner_id(media_id)
        # Store comment in MongoDB if it doesn't already exist
        if not comments_collection.find_one({'id': comment_id}):
            comment_to_db(comment_id, comment_text, platform, user_id, user_name, media_id)

        # If human review is disabled, handle the comment
        if not HUMAN_REVIEW:
            handle_comment(comment_data, owner_id)
            
    else:
        logger.error("Comment ID is missing in the comment data.")

def comment_to_db(comment_id, comment_text, platform, user_id=None, user_name='Unknown User', media_id=None):
    """
    Store a comment in the database.
    
    Parameters:
    comment_id (str): The unique identifier for the comment.
    comment_text (str): The text content of the comment.
    platform (str): The platform from which the comment originated.
    user_id (str, optional): The ID of the user who made the comment.
    user_name (str, optional): The name of the user who made the comment.
    media_id (str, optional): The ID of the media associated with the comment (for Instagram).
    """
    try:
        # Prepare the comment data for insertion
        comment_data = {
            'id': comment_id,
            'text': comment_text,
            'status': 'PENDING',
            'evaluation': evaluate_comment(comment_text),
            'platform': platform,
            'user_id': user_id,
            'user_name': user_name,
            'media_id': media_id
        }

        # Insert the comment into the database
        comments_collection.insert_one(comment_data)
        logger.info(f"Comment with ID {comment_id} successfully added to the database.")

    except Exception as e:
        logger.error(f"Error inserting comment with ID {comment_id}: {e}")

def approve_comment(comment_id):
    """Approve the comment."""
    #approve(comment_id)
    logger.debug(f"Comment {comment_id} has been approved.")

def send_for_human_review(comment_id):
    """Queue the comment for human review and hide it in the meantime."""
    comments_collection.update_one({'id': comment_id}, {'$set': {'status': 'PENDING_REVIEW', 'hidden': '1'}})
    logger.info(f"Comment {comment_id} is now queued for human review.")
    hide_comment(comment_id, log=False)  # Hide the comment while pending review

def handle_action_based_on_mode(comment_id, fallback_action):
    """Handle actions based on the config mode."""
    if config.MODE == "full":
        action_2(comment_id)
    else:
        send_for_human_review(comment_id)
        
def handle_comment(comment_data, owner_id=None):
    """
    Process an incoming comment for moderation.
    
    Parameters:
    comment_data (dict): The data of the comment, including its ID and text.
    owner_id (str, optional): The owner ID of the post where the comment was made.
    """
    # Extract comment ID and text based on the platform
    comment_id = comment_data.get('comment_id') or comment_data.get('id')
    comment_text = comment_data.get('message') or comment_data.get('text', '')

    # Validate comment ID
    if not comment_id:
        logger.error("Missing comment ID in the comment data.")
        return

    # Skip processing if the comment has already been processed
    if comment_id in processed_comments:
        logger.warning(f"Comment with id '{comment_id}' has already been processed. Skipping.")
        return

    # Add comment ID to the processed set to avoid re-processing
    processed_comments.add(comment_id)

    # Retrieve the owner's configuration if needed
    owner_config = get_owner_config(owner_id)
    if owner_config is None:
        logger.warning(f"No configuration found for owner ID '{owner_id}'. Proceeding with default settings.")

    """OWNER CONFIG
    {
  "filters": [
    {
      "name": "filter1",
      "_id": 
    },
    {
      "name": "filter2",
      "
    }
    // Add more filters as needed
  ],
  "max_hide": false,
  "threshold": 80
}

    """


    # Moderate the comment using the moderation model, including owner ID if necessary
    moderation_result = moderation_model.moderate_comment(comment_text, owner_config)

    # Define action based on moderation result
    result_action_map = {
        0: approve_comment,
        1: hide_comment,
        2: lambda cid: handle_action_based_on_mode(cid, "max_hide"),
        3: lambda cid: handle_action_based_on_mode(cid, "max_hide"),
        4: send_for_human_review
    }

    # Execute the corresponding action
    result_action = result_action_map.get(int(moderation_result))
    if result_action:
        result_action(comment_id)
    else:
        logger.error(f"Unknown moderation result: {moderation_result} for comment {comment_id}")

def get_owner_config(owner_id):
    """
    Retrieve the configuration for the owner based on their ID.

    Parameters:
    owner_id (str): The ID of the owner whose configuration is to be retrieved.

    Returns:
    dict: The owner's configuration or None if not found.
    """
    # Assuming you have a collection for owner configurations in the database
    owner_config = db_2.owner_configs.find_one({'owner_id': owner_id})
    return owner_config


def get_instagram_owner_id(media_id):
    """
    Retrieve the owner ID for a given Instagram media or comment.
    
    Parameters:
    media_id (str): The ID of the Instagram media or comment.

    Returns:
    str: The owner ID of the media or comment.
    """
    url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/{media_id}"
    params = {
        'fields': 'owner',
        'access_token': INSTAGRAM_ACCESS_TOKEN
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get('owner', {}).get('id')
        else:
            logger.warning(f"Failed to get owner ID for media {media_id}. Status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        logger.error(f"An error occurred while retrieving owner ID for media {media_id}: {e}")
        return None


def action_2(comment_id):
    remove(comment_id)  # Remove the comment if it is deemed inappropriate
    logger.info(f"Comment {comment_id} has been removed.")

@app.route('/review', methods=['GET'])
def review():
    """
    Retrieve and render a pending comment for review.
    Returns:
    Response: Rendered HTML template for comment review or a message indicating no comments are pending.
    """
    # Find a pending comment from the database
    pending_comment = comments_collection.find_one({'status': 'PENDING_REVIEW'})
    
    if pending_comment:
        comment_id = pending_comment['id']
        comment_text = pending_comment['text']
        evaluation_result = pending_comment['evaluation']

        # Update the status of the comment to 'in_review'
        comments_collection.update_one({'id': comment_id}, {'$set': {'status': 'IN_REVIEW'}})

        return render_template('review.html', comment_id=comment_id, comment_text=comment_text, evaluation_result=evaluation_result)
    else:
        return render_template("nothing_to_review.html")  # Render a template indicating no comments are available for review

@app.route('/skip/<comment_id>', methods=["POST"])
def skip(comment_id):
    # Update the comment status in MongoDB    
    comments_collection.update_many({'id': comment_id}, {'$set': {'status': 'SKIPPED'}})
    return redirect(url_for('review'))

@app.route('/approve/<comment_id>', methods=['POST'])
def approve(comment_id):
    # Update the comment status in MongoDB
    comment = comments_collection.find_one({'id': comment_id})
    moderation_model._log_comment(action_type=0, comment=comment["text"], label=0)
    comments_collection.update_many({'id': comment_id}, {'$set': {'status': 'APPROVED'}})
    hide_comment(comment_id, False, unhide=True)
    return redirect(url_for('review'))

@app.route('/remove/<comment_id>', methods=['POST'])
def remove(comment_id):
    comment = comments_collection.find_one({'id': comment_id})  # Find the comment from the database
    
    comments_collection.update_many({'id': comment_id}, {'$set': {'status': 'PENDING_REMOVE'}})  # Let database know, that we will soon remove the comment from the social media platform
    
    moderation_model._log_comment(action_type=2, comment=comment["text"], label=1)  # On our AI model, add to training data
    
    remove_comment(comment_id)
    
    return redirect(url_for('review'))

def evaluate_comment(comment_text):
    """
    Evaluate the given comment for profanity using the profane_detector model 
    designed for HaSpDe. Note: The profanity detection feature has been deprecated 
    and will no longer be supported in future updates.
    
    Parameters:
    comment_text (str): The text of the comment to evaluate.
    
    Returns:
    str: "Positive" if no profanity is detected, "Negative" otherwise.
    """
    logger.debug(f"Evaluating comment: {comment_text}")

    result = False  # This would normally involve a detection model
    logger.debug(f"Profane detector result: {result}")

    # Determine evaluation based on detection result
    evaluation = "Negative" if result else "Positive"
    logger.debug(f"Evaluation result: {evaluation}")

    return evaluation


def init_comment(comment_id):
    # Fetch the comment details to get the media ID and platform
    comment = comments_collection.find_one({'id': comment_id})
    if not comment:
        logger.critical(f"Comment with ID {comment_id} not found in the database.")
        return

    media_id = comment.get('media_id')
    platform = comment.get('platform')  # Assuming you have a field for the platform

    if not media_id:
        logger.error(f"No media ID found for comment ID {comment_id}.")
        return

    return comment, media_id, platform


def remove_comment(comment_id):
    """
    Remove a comment from Facebook or Instagram using the Graph API.
    Parameters:
    comment_id (str): The unique identifier for the comment to be removed.
    """
    comment, media_id, platform = init_comment(comment_id)

    url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/{comment_id}"

    headers = token_(media_id, platform)

    try:
        # Send a DELETE request to remove the comment
        response = requests.delete(url, headers=headers)

        if response.status_code == 200:
            logger.info(f"Comment with ID {comment_id} removed successfully.")
            # Update the comment status in the database
            comments_collection.update_many({'id': comment_id}, {'$set': {'status': 'REMOVED'}})
        else:
            logger.warning(f"Failed to remove comment with ID {comment_id}. Status code: {response.status_code}, Response: {response.text}")

    except requests.RequestException as e:
        logger.error(f"An error occurred while trying to remove comment with ID {comment_id}: {e}")

def token_(media_id, platform):
    if platform == "instagram":
        access_token = INSTAGRAM_ACCESS_TOKEN

    elif platform == "facebook":
        owner_id = media_id.split('_')[0]  # Get the part before the underscore
        access_token = get_facebook_token(owner_id)

    headers = {'Authorization': f'Bearer {access_token}'}
    return headers

def _str_bool(value):
    # If the input is a boolean, return its string representation
    if isinstance(value, bool):
        return "true" if value else "false"
    
    # If the input is a string, check its value and return the corresponding boolean
    elif isinstance(value, str):
        value = value.lower()
        if value == "true":
            return True
        elif value == "false":
            return False
    
    # If the input is neither a boolean nor a recognized string, return None or raise an error
    return None  # or raise ValueError("Input must be a boolean or a string.")
def hide_comment(comment_id, log=True, unhide=False):
    """
    Hide or unhide a comment on Instagram using the Instagram Graph API.

    :param comment_id: The ID of the comment to hide or unhide.
    :param log: Whether to log the operation status (default is True).
    :param unhide: If True, the comment will be unhidden; if False, it will be hidden (default is False).
    :return: Response of the API request.
    """
    # Initialize the comment, media_id, and platform
    comment, media_id, platform = init_comment(comment_id)

    # Construct the API endpoint URL
    url = f"https://graph.facebook.com/{INSTAGRAM_API_VERSION}/{comment_id}"

    # Prepare the headers and parameters for the request
    headers = token_(media_id, platform)
    params = {
        "is_hidden": str(unhide).lower(),  # Set to 'true' for hiding, 'false' for unhiding
        "hide": unhide  # Use the same boolean value for the 'hide' parameter
    }

    # Send the POST request to the API
    response = requests.post(url, params=params, headers=headers)

    # Process the response
    if response.status_code == 200:
        # Determine the new status and hidden state based on the operation
        status = "APPROVED" if unhide else "HIDDEN"
        hidden = 0 if unhide else 1

        # Update the comment status in the database
        to_set = {'hidden': hidden}
        if log:
            to_set['status'] = status

        comments_collection.update_many({'id': comment_id}, {'$set': to_set})

        # Log the action if logging is enabled
        if log:
            logger.info(f"Comment with ID {comment_id} has been {'un' if unhide else ''}hidden successfully.")
    else:
        logger.warning(f"Failed to {'un' if unhide else ''}hide comment with ID {comment_id}. "
                       f"Status code: {response.status_code}, Response: {response.text}")

def method_not_allowed():
    logger.warning("Method not allowed!")
    return jsonify({'error': 'Method not allowed'}), 405

def get_facebook_token(owner_id):
    # Fetch user info to find the corresponding page access token
    user = db_2.users.find_one({'managed_pages.page_id': owner_id})
    if user:
        for page in user['managed_pages']:
            if page['page_id'] == owner_id:
                page_access_token = page['page_access_token']
                return page_access_token
        else:
            logger.critical(f"No access token found for owner ID {owner_id}.")
            return
    else:
        logger.critical(f"No user found for owner ID {owner_id}.")
        return

def facebook_remove_handler(media_id): # For Facebook, derive the owner ID
    owner_id = media_id.split('_')[0]  # Get the part before the underscore
    page_access_token = get_facebook_token(owner_id)

    headers = {'Authorization': f'Bearer {page_access_token}'}

    return headers


@app.route('/get_comments', methods=['GET'])
def get_comments():
    limit = int(request.args.get('limit', 10))  # Default to 10 if not specified
    # Fetch the most recent comments
    comments = list(comments_collection.find().sort('_id', -1).limit(limit))
    
    # Prepare comments for response (convert ObjectId to str)
    for comment in comments:
        comment['_id'] = str(comment['_id'])
    
    return jsonify(comments)

@app.route('/get_new_comments', methods=['GET'])
def get_new_comments():
    after_id = request.args.get('afterId')
    new_comments = []
    
    if after_id:
        # Fetch comments that were added after the given comment ID
        new_comments = list(comments_collection.find({
            '_id': {'$gt': ObjectId(after_id)}
        }).sort('_id', 1))  # Sort ascending to get newer comments

    # Prepare comments for response
    for comment in new_comments:
        comment['_id'] = str(comment['_id'])

    return jsonify(new_comments)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=config.FLASK_DEBUG, port=config.FLASK_PORT)

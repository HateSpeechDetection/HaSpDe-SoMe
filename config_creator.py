import json

def prompt_user_for_config():
    config = {}

    print("Please enter the following configuration details:")

    # Prompting user for MongoDB URI
    config['mongodb_uri'] = input("MongoDB URI (default: mongodb://localhost:27017/): ") or "mongodb://localhost:27017/"
    
    # Prompting user for Database name
    config['db_name'] = input("Database name (default: comment_moderation): ") or "comment_moderation"
    
    # Prompting user for Instagram Access Token
    config['instagram_access_token'] = input("Instagram Access Token: ")
    
    # Prompting user for Instagram API Version
    config['instagram_api_version'] = input("Instagram API Version (default: v20.0): ") or "v20.0"
    
    # Prompting user for Instagram Verify Token
    config['instagram_verify_token'] = input("Instagram Verify Token: ")

    # Prompting user for improve option (Y/N)
    improve_input = input("Improve (Y/N, default: Y): ").strip().upper()
    config['improve'] = True if improve_input in ['Y', ''] else False

    # Prompting user for human review option (Y/N)
    human_review_input = input("Human Review (Y/N, default: N): ").strip().upper()
    config['human_review'] = True if human_review_input == 'Y' else False

    # Prompting user for flask_debug option (Y/N)
    flask_debug_input = input("Flask Debug (Y/N, default: N): ").strip().upper()
    config['flask_debug'] = True if flask_debug_input == 'Y' else False

    # Prompting user for Flask Port
    config['flask_port'] = int(input("Flask Port (default: 5000): ") or "5000")

    # Prompting user for mode with validation
    while True:
        mode_input = input("Mode (options: MAX_HIDE, FULL, default: MAX_HIDE): ").strip().upper()
        if mode_input in ['MAX_HIDE', 'FULL', '']:
            config['mode'] = mode_input or 'MAX_HIDE'
            break
        else:
            print("Invalid input. Please enter either 'MAX_HIDE' or 'FULL'.")

    # Prompting user for certainty_needed with validation
    while True:
        certainty_needed_input = int(input("Certainty Needed (51 to 100, default: 95): ") or "95")
        if 51 <= certainty_needed_input <= 100:
            config['certainty_needed'] = certainty_needed_input
            break
        else:
            print("Invalid input. Please enter a value between 51 and 100.")

    return config

def save_config_to_json(config, filename='config.json'):
    with open(filename, 'w') as json_file:
        json.dump(config, json_file, indent=4)
    print(f"Configuration saved to {filename}")

def main():
    config = prompt_user_for_config()
    save_config_to_json(config)

if __name__ == "__main__":
    main()

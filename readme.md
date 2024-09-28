# HaSpDe SoMe

### Supported Platforms

HaSpDe offers powerful moderation tools to enhance your community engagement on the following social media platforms:

- **Facebook**: Ensure compliance with community standards by moderating comments, fostering a respectful environment.
- **Instagram**: Manage comment interactions on your posts, preventing harmful content and encouraging positive dialogue.

### Getting Started

To set up HaSpDe SoMe, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/HateSpeechDetection/HaSpDe-SoMe.git
   cd HaSpDe-SoMe
   ```

2. **Create Your Configuration File**:
   Use the `config_creator.py` script to generate your `config.json` file. Run the following command:
   ```bash
   python config_creator.py
   ```

   During the configuration process, you will be prompted to input the following options:

   - **mongodb_uri**: Enter your MongoDB URI (default: `mongodb://localhost:27017/`).
   - **db_name**: Specify the database name (default: `comment_moderation`).
   - **instagram_access_token**: Provide your Instagram access token.
   - **instagram_api_version**: Set your Instagram API version (default: `v20.0`).
   - **instagram_verify_token**: Enter your Instagram verify token.
   - **improve**: Enable improvement (default: `true`, options: Y/N).
   - **human_review**: Enable human review (default: `false`, options: Y/N).
   - **flask_debug**: Set Flask debug mode (default: `false`, options: Y/N).
   - **flask_port**: Specify the port for Flask (default: `5000`).
   - **mode**: Choose a mode (`MAX_HIDE` or `FULL`, default: `MAX_HIDE`).
   - **certainty_needed**: Set the certainty needed (minimum: `51`, maximum: `100`, default: `95`).

3. **Run HaSpDe SoMe**: Once your `config.json` file is set up, you can start using the HaSpDe SoMe moderation tools.

For more details and to get started, visit our [HaSpDe SoMe page](https://luova.club/HaSpDe/SoMe/).
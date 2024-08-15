import os
import requests
from log import logger

class ModelUpdater:
    def __init__(self, model_file, version_file, model_url, version_url):
        self.model_file = model_file
        self.version_file = version_file
        self.model_url = model_url
        self.version_url = version_url

    def download_file(self, url, save_path):
        """Download a file from a given URL and save it to the specified path."""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            logger.info(f"Downloaded file from {url} to {save_path}.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download the file from {url}: {e}")
            exit(1)
        except OSError as e:
            logger.error(f"Failed to save the file to {save_path}: {e}")
            exit(2)

    def get_local_version(self):
        """Read the local model version from a file."""
        if os.path.exists(self.version_file):
            try:
                with open(self.version_file, 'r') as file:
                    return file.read().strip()
            except OSError as e:
                logger.error(f"Failed to read the local version file: {e}")
                exit(3)
        return None

    def get_github_version(self):
        """Fetch the model version from the GitHub URL."""
        try:
            response = requests.get(self.version_url)
            response.raise_for_status()
            return response.text.strip()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch the version from GitHub: {e}")
            return None

    def is_newer_version_available(self, local_version, github_version):
        """Compare local and GitHub versions to determine if an update is needed."""
        if local_version is None:
            return True  # If no local version, assume we need to update
        return github_version > local_version

    def update_model(self):
        """Check for updates and download the new model if a newer version is available."""
        local_version = self.get_local_version()
        github_version = self.get_github_version()

        if github_version:
            if not local_version or self.is_newer_version_available(local_version, github_version):
                logger.info(f"Newer model version ({github_version}) available. Updating...")
                self.download_file(self.model_url, self.model_file)
                self.download_file(self.version_url, self.version_file)
                logger.info(f"Model updated to version {github_version}.")
            else:
                logger.info("Local model is up to date.")
        else:
            logger.error("Failed to determine the latest model version. Update aborted.")

if __name__ == "__main__":
    updater = ModelUpdater(
        model_file='moderation_model.joblib',
        version_file='model_version.txt',
        model_url="https://raw.githubusercontent.com/botsarefuture/HaSpDe/main/moderation_model.joblib",
        version_url="https://raw.githubusercontent.com/botsarefuture/HaSpDe/main/model_version.txt"
    )
    updater.update_model()

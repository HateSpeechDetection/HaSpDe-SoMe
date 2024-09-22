import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,  # This will capture all levels from DEBUG and above
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Ensure logs are output to the console
)

# Create logger instance
logger = logging.getLogger("HaSpDe SoMe")
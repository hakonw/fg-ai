import logging
import time
from collector.scan_batch import scan_from_start

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

HOUR_IN_SECONDS = 3600
MAX_PAGES = 10

def main():
    logging.info("Starting image scanner")
    
    while True:
        try:
            found_new = scan_from_start(max_pages=MAX_PAGES)

            if not found_new:
                logging.info("No new images found, sleeping for one hour")
                time.sleep(HOUR_IN_SECONDS)
                
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            logging.info("Retrying in 180 seconds")
            time.sleep(180)
        break;

if __name__ == "__main__":
    main()

# python -m collector.runner
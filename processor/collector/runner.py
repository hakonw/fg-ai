import logging
import time
from collector.scan_batch import scan_from_start

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

HOUR_IN_SECONDS = 3600
MAX_PAGES = 200
MAX_STALE_PAGES = 5

def main():
    logging.info("Starting image scanner")
    
    while True:
        try:
            scan_from_start(start=1, max_pages=MAX_PAGES, max_stale_pages=MAX_STALE_PAGES)
            time.sleep(HOUR_IN_SECONDS)
                
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            logging.info("Retrying in 180 seconds")
            time.sleep(180)

if __name__ == "__main__":
    main()

# python -m collector.runner
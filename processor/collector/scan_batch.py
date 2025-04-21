import collector.page
import collector.worker_queue
import logging
import time

def scan_single_page(page_number):
    """Scan a single page and return found images"""
    page_html = collector.page.get(page_number)
    images_in_page = collector.page.process(page_html)
    unseen = collector.page.remove_seen(images_in_page)
    return unseen

def queue_images(images):
    """Queue the found images for processing"""
    for image in images:
        collector.worker_queue.queue(image)

def scan_from_start(start=1, max_pages=100, max_stale_pages=5):
    stale = 0
    for page in range(start, max_pages + 1):
        if stale >= max_stale_pages:
            logging.info("No new images found in the last few pages, stopping scan.")
            break
        try:
            logging.info(f"Scanning page {page}")
            new_images = scan_single_page(page)
            if new_images:
                stale=0
                queue_images(new_images)
                logging.info(f"Queued {len(new_images)} new images from page {page}")
            else:
                stale+=1

        except Exception as e:
            logging.error(f"Error scanning page {page}: {str(e)}")

        time.sleep(3)

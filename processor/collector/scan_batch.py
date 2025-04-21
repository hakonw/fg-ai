import collector.page
import collector.worker_queue
import logging

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

def scan_from_start(max_pages=10):
    """
    Scan pages from page 1 up to max_pages.
    Returns True if any new images were found.
    """
    total_queued = 0
    
    for page in range(1, max_pages + 1):
        try:
            logging.info(f"Scanning page {page}")
            new_images = scan_single_page(page)
            
            if new_images:
                queue_images(new_images)
                queued = len(new_images)
                total_queued += queued
                logging.info(f"Queued {queued} new images from page {page}")
                
        except Exception as e:
            logging.error(f"Error scanning page {page}: {str(e)}")
            
    return total_queued > 0
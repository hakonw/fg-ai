import collector.page
import collector.worker_queue

start = 307

max = start+20 # Ikke inkludert

if __name__ == "__main__":
    page = start
    while page < max:
        print(f"Running page {page}")

        page_html = collector.page.get(page)
        images_in_page = collector.page.process(page_html)
        images = collector.page.remove_seen(images_in_page)

        print(f"on page: {len(images_in_page)}, unprocessed: {len(images)}")

        if len(images) == 0:
            # A problem here is that remove_seen assumes the files has been processed.
            # The best would be to search the queue and db
            print("Seen every picture before. Stopping")
            #break

        for image in images:
            collector.worker_queue.queue(image)

        page += 1

import core
import db

def main():
    index = 0
    stale = 0
    max_pages = 100

    session = core.create_photo_session()

    for _ in range(max_pages):
        result = core.scrape_page(session, index)
        index += 1

        if result.error or result.queued == 0:
            stale += 1
        else:
            stale = 0
        if result.end_of_archive or stale >= 3:
            break


if __name__ == "__main__":
    print("Starting search")
    main()
    print("Done")
    print(db.get_stats())

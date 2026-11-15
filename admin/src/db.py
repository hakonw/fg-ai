from supabase import create_client
from dotenv import load_dotenv
import os
from postgrest import CountMethod

load_dotenv()


def get_supabase_client():
    try:
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        return supabase
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        print("Make sure .env is set up correctly.")
        import sys
        sys.exit(1)


_supabase = None


def get_supabase():
    global _supabase
    if _supabase:
        return _supabase
    else:
        _supabase = get_supabase_client()
        return _supabase


def get_stats():
    stats = {}
    for s in ["pending", "processing", "indexed", "failed"]:
        res = (get_supabase().table("images")
               .select("*", count=CountMethod.exact, head=True)
               .eq("status", s)
               .execute())
        stats[s] = res.count
    return stats


def reset_processing():
    res = (
        get_supabase().table("images")
        .update({"status": "pending"})
        .eq("status", "processing")
        .execute()
    )
    count = len(res.data) if res.data else 0
    return f"Reset {count} processing jobs to pending."


def reset_failed():
    res = (
        get_supabase().table("images")
        .update({"status": "pending"})
        .eq("status", "failed")
        .execute()
    )
    count = len(res.data) if res.data else 0
    return f"Reset {count} failed jobs to pending."


def upsert_motive(motive):
    response = get_supabase().table("motives").upsert(motive, on_conflict="fg_motive_id").execute()
    return response.data[0]["id"]


def queue_images(images):
    response = get_supabase().table("images").upsert(
        images, on_conflict="fg_photo_id", ignore_duplicates=True
    ).execute()
    return response

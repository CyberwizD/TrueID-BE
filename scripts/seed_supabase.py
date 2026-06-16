from dotenv import load_dotenv
load_dotenv()

from TrueID_BE.config import get_settings
from TrueID_BE.repository import SupabaseRepository
from TrueID_BE.seeds import SEED_CONTRIBUTIONS, SEED_PROFILES, SEED_REPORTS

def seed():
    settings = get_settings()
    if settings.resolved_backend != "supabase":
        print(f"Not using supabase backend. Current: {settings.resolved_backend}. Please set TRUEID_DATA_BACKEND=supabase in your env.")
        return
    
    repo = SupabaseRepository(settings)
    
    print(f"Upserting {len(SEED_PROFILES)} profiles...")
    repo.upsert_caller_profiles(SEED_PROFILES)
    
    print(f"Upserting {len(SEED_CONTRIBUTIONS)} contact contributions...")
    repo.save_contact_contributions(SEED_CONTRIBUTIONS)
    
    print(f"Upserting {len(SEED_REPORTS)} spam reports...")
    for report in SEED_REPORTS:
        try:
            repo.save_spam_report(report)
        except Exception as e:
            # might fail if reporter_id doesn't exist, though we don't have FKs in the migration usually
            pass
            
    print("Database seeding completed.")

if __name__ == "__main__":
    seed()

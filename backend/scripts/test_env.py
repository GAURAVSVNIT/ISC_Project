import os
from dotenv import load_dotenv
load_dotenv()

print(f"Direct OS Env Check: {'FOUND' if os.getenv('GROQ_API_KEY') else 'MISSING'}")

try:
    from backend.config import settings
    print(f"Settings Config Check: {'FOUND' if settings.GROQ_API_KEY else 'MISSING'}")
    if settings.GROQ_API_KEY:
        print(f"Key Length: {len(settings.GROQ_API_KEY)}")
except ImportError:
    print("Could not import backend.config settings")
except Exception as e:
    print(f"Settings Check Error: {e}")

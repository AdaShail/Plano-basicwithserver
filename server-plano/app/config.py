import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    BING_API_KEY = os.getenv("BING_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
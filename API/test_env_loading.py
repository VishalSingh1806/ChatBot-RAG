import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_var(var_name):
    value = os.getenv(var_name)
    if value:
        print(f"✅ {var_name} is set.")
        # print(f"   Value: {value}") # Uncomment to see values
    else:
        print(f"❌ {var_name} is NOT set.")

print("--- Verifying Environment Variables ---")
check_env_var("GOOGLE_API_KEY")
check_env_var("SECRET_KEY")
check_env_var("ALLOWED_ORIGINS")
check_env_var("CONTACT_EMAIL")
check_env_var("SMTP_PASSWORD") # Check this one too as it was seen in other files

print("\n--- Verification Complete ---")

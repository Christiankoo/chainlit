import os
# UNCOMMENT the following two lines if you are using a .env file to manage environment variables
# from dotenv import load_dotenv
# load_dotenv()

TENANT_ID = os.environ.get("AZURE_TENANT_ID")
CLIENT_ID = os.environ.get("AZURE_CLIENT_ID")
REDIRECT_URI = os.environ.get("AZURE_REDIRECT_URI")
SECRET_ID = os.environ.get("AZURE_SECRET_ID")
SESSION_SECRET= os.environ.get("SESSION_SECRET")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0"
AUTHORIZE_URL = f"{AUTHORITY}/authorize"
TOKEN_URL = f"{AUTHORITY}/token"
JWKS_URL = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"

PUBLIC_PATHS = {
    "/healthz",
    "/api/auth/login",
    "/api/auth/callback",
    "/docs",
    "/openapi.json"
}

SERVER = os.getenv("AZURE_SQL_SERVER")
DATABASE = os.getenv("AZURE_SQL_DB")
USERNAME = os.getenv("AZURE_SQL_USER")
PASSWORD = os.getenv("AZURE_SQL_PASSWORD")
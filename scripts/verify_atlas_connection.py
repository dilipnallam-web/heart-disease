"""
MongoDB Atlas Connectivity and Health Diagnostic Utility.
Verifies credentials, SRV resolution, cluster ping, and collection access.
Run via:
    python scripts/verify_atlas_connection.py [optional_connection_string]
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend can be imported
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

env_path = repo_root / "backend" / ".env"
load_dotenv(env_path)

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError

def verify_connection(uri: str = None, db_name: str = "heart_disease_db"):
    uri = uri or os.getenv("MONGODB_URI", "").strip()

    print("=" * 65)
    print("      MongoDB Atlas Connection Diagnostic Utility      ")
    print("=" * 65)

    if not uri:
        print("[!] No MongoDB Atlas URI provided.")
        print(f"    Please configure MONGODB_URI in '{env_path}' or pass it as an argument.")
        print("    Format: mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority")
        return False

    # Mask credentials for safe terminal logging
    if "@" in uri:
        prefix, host_part = uri.split("@", 1)
        scheme_part = prefix.split("://")[0]
        masked_uri = f"{scheme_part}://*****:*****@{host_part}"
    else:
        masked_uri = uri[:15] + "..."

    print(f"[*] Target URI: {masked_uri}")
    print(f"[*] Target Database: '{db_name}'")
    print("[*] Initiating connection with 5-second timeout...")

    try:
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            retryWrites=True
        )
        # Ping the admin database
        client.admin.command("ping")
        print("\n[+] SUCCESS: Successfully reached MongoDB Atlas cluster!")

        # Check server info
        build_info = client.server_info()
        print(f"    - MongoDB Version: {build_info.get('version', 'Unknown')}")
        print(f"    - Cluster Host: {client.address[0] if client.address else 'Atlas Cluster'}")

        db = client[db_name]
        collections = db.list_collection_names()
        print(f"    - Existing Collections in '{db_name}': {collections or '(none yet - will create on write)'}")

        # Test index creation
        from backend.database.indexes import create_database_indexes
        idx_res = create_database_indexes(db)
        print(f"    - Indexes Ensured: users={len(idx_res.get('users', []))}, predictions={len(idx_res.get('predictions', []))}")

        print("\n[+] MongoDB Atlas is 100% ready for production heart disease predictions!")
        print("=" * 65)
        return True

    except ConfigurationError as e:
        print(f"\n[-] CONFIGURATION ERROR: Invalid connection string scheme or DNS SRV record: {e}")
        return False
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"\n[-] CONNECTION TIMEOUT: Could not reach MongoDB Atlas cluster.")
        print(f"    Details: {e}")
        print("\n    Common fixes:")
        print("    1. Check your Atlas Network Access (IP Access List): ensure your current IP or 0.0.0.0/0 is whitelisted.")
        print("    2. Verify your database username and password in MongoDB Atlas.")
        print("    3. Ensure dnspython is installed (`pip install dnspython`).")
        return False
    except Exception as e:
        print(f"\n[-] UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    cli_uri = sys.argv[1] if len(sys.argv) > 1 else None
    success = verify_connection(cli_uri)
    sys.exit(0 if success else 1)

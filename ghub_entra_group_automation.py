import requests
import sys

# ================================
# 1. CONFIGURATION - REPLACE THESE
# ================================

# Microsoft Entra (Azure AD) App Registration
TENANT_ID = "YOUR_TENANT_ID"
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"

# GitHub Organization + Token
GITHUB_ORG = "YOUR_GITHUB_ORG"
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"

# Mapping from Entra group display name (with trailing period) to GitHub team slug
ENTRA_TO_GITHUB_MAP = {
    "Frontend Team.": "frontend-team",
    "Backend Services Team.": "backend-services-team",
    "AI & ML Team.": "ai-ml-team",
    # Add more as needed...
}

# ================================
# 2. HELPER FUNCTIONS
# ================================

def get_graph_token():
    """
    Get an OAuth 2.0 token from Microsoft Entra (Azure AD)
    using the client_credentials flow.
    """
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }
    resp = requests.post(token_url, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_user_object_id_by_email(access_token, user_email):
    """
    Look up the user's object ID in Entra by email address.
    Returns the user's object ID if found, else None.
    """
    url = "https://graph.microsoft.com/v1.0/users"
    headers = {"Authorization": f"Bearer {access_token}"}
    # Filter by mail (primary email)
    params = {"$filter": f"mail eq '{user_email}'"}
    
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()

    # If user found, return the first match's 'id'
    if data.get("value"):
        return data["value"][0]["id"]
    else:
        return None


def add_user_to_entra_group(access_token, user_object_id, group_name):
    """
    Add a user to a specified Entra group (by group display name).
    """
    # 1) Find the group's ID by name
    groups_url = "https://graph.microsoft.com/v1.0/groups"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"$filter": f"displayName eq '{group_name}'"}
    
    group_resp = requests.get(groups_url, headers=headers, params=params)
    group_resp.raise_for_status()
    group_data = group_resp.json()

    if not group_data.get("value"):
        print(f"ERROR: Could not find Entra group with displayName '{group_name}'")
        return False

    group_id = group_data["value"][0]["id"]

    # 2) Add the user to the group
    add_member_url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"
    body = {
        "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_object_id}"
    }

    add_resp = requests.post(add_member_url, headers=headers, json=body)
    if add_resp.status_code in [200, 204]:
        print(f"SUCCESS: User added to Entra group '{group_name}'")
        return True
    else:
        print(f"ERROR: Failed to add user to Entra group '{group_name}'. "
              f"Status: {add_resp.status_code}, Message: {add_resp.text}")
        return False


def add_user_to_github_team(user_email, github_team_slug):
    """
    Add (or invite) a user to a GitHub team by email address.
    This uses the GitHub REST API and a Personal Access Token (PAT).
    """
    url = f"https://api.github.com/orgs/{GITHUB_ORG}/teams/{github_team_slug}/memberships/{user_email}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    # role=member => user is added as a member
    payload = {"role": "member"}

    resp = requests.put(url, headers=headers, json=payload)
    if resp.status_code in [200, 201]:
        print(f"SUCCESS: User added to GitHub team '{github_team_slug}'")
        return True
    else:
        print(f"ERROR: Failed to add user to GitHub team '{github_team_slug}'. "
              f"Status: {resp.status_code}, Message: {resp.text}")
        return False


# ================================
# 3. MAIN FUNCTION
# ================================

def sync_user(user_email, entra_group_name):
    """
    1) Get a Graph token
    2) Find user's Entra object ID
    3) Add user to specified Entra group
    4) Find matching GitHub team from the mapping
    5) Add user to that GitHub team
    """
    # Get Graph token
    token = get_graph_token()

    # Lookup user in Entra by email -> get object ID
    user_object_id = get_user_object_id_by_email(token, user_email)
    if not user_object_id:
        print(f"ERROR: No Entra user found with email '{user_email}'")
        return

    # Add user to Entra group
    success_entra = add_user_to_entra_group(token, user_object_id, entra_group_name)
    if not success_entra:
        return  # Stop if we can't add them to Entra

    # Map Entra group name to GitHub team
    github_team = ENTRA_TO_GITHUB_MAP.get(entra_group_name)
    if not github_team:
        print(f"ERROR: No matching GitHub team for Entra group '{entra_group_name}' in ENTRA_TO_GITHUB_MAP.")
        return

    # Add user to GitHub team
    add_user_to_github_team(user_email, github_team)


# ================================
# 4. RUN SCRIPT
# ================================
if __name__ == "__main__":
    """
    Example usage:
      python entra_github_sync.py user@example.com "Frontend Team."
    """
    if len(sys.argv) != 3:
        print("Usage: python entra_github_sync.py <user_email> <entra_group_name>")
        sys.exit(1)

    email_arg = sys.argv[1]
    group_arg = sys.argv[2]

    sync_user(email_arg, group_arg)
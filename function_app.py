import os
import logging
import requests
import azure.functions as func
from azure.functions import FunctionApp

# ---------------------------------------------------------
# Create the Azure Functions app object (new Python model)
# ---------------------------------------------------------
app = FunctionApp()

# ---------------------------------------------------------
# Environment Variables for Microsoft Entra & GitHub
# (Set these in Azure Portal -> Your Function App -> Configuration -> Application Settings)
# ---------------------------------------------------------
TENANT_ID = os.getenv("TENANT_ID")       # e.g. "00000000-1111-2222-3333-444444444444"
CLIENT_ID = os.getenv("CLIENT_ID")       # e.g. "55555555-6666-7777-8888-999999999999"
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GITHUB_ORG = os.getenv("GITHUB_ORG")     # e.g. "my-github-org"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # e.g. "ghp_..."

# ---------------------------------------------------------
# Mapping of Entra Group Display Names to GitHub Team Slugs
# Adjust as needed for your organization
# ---------------------------------------------------------
ENTRA_TO_GITHUB_MAP = {
    "AI & Machine Learning Team.": "ai-machine-learning-team",
    "All Company": "all-company",
    "Backend Development Team.": "backend-development-team",
    "Cloud Engineering Team.": "cloud-engineering-team",
    "Compliance & Governance Team.": "compliance-governance-team",
    "Cybersecurity Team.": "cybersecurity-team",
    "Data Engineering Team.": "data-engineering-team",
    "Developer Relations & Community Engagement Team.": "developer-relations-community-engagement-team",
    "DevOps & Automation Team.": "devops-automation-team",
    "Frontend Development Team.": "frontend-development-team",
    "Network Engineering Team.": "network-engineering-team",
    "Product Management Team.": "product-management-team",
    "Research & Development (R&D) Team.": "research-development-team",
    "Sales & Business Development Team.": "sales-business-development-team",
    "Saphyre Solutions LLC": "saphyre-solutions-llc",
    "Software Development Team.": "software-development-team",
    "Technical Support & IT Operations Team.": "technical-support-it-operations-team",
    "UI/UX & Design Team.": "ui-ux-design-team"
}

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------
def get_graph_token():
    """
    Acquire an OAuth 2.0 token from Microsoft Entra (Azure AD)
    using the client_credentials flow.
    """
    if not (TENANT_ID and CLIENT_ID and CLIENT_SECRET):
        raise ValueError("Missing Microsoft Entra credentials in Azure App Settings.")

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
    Look up the user's object ID in Microsoft Entra by email address.
    Returns the user's object ID if found, else None.
    """
    url = "https://graph.microsoft.com/v1.0/users"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"$filter": f"mail eq '{user_email}'"}

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()

    if data.get("value"):
        return data["value"][0]["id"]
    else:
        return None


def add_user_to_entra_group(access_token, user_object_id, group_name):
    """
    Add a user to a specified Entra group by display name.
    """
    groups_url = "https://graph.microsoft.com/v1.0/groups"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"$filter": f"displayName eq '{group_name}'"}

    group_resp = requests.get(groups_url, headers=headers, params=params)
    group_resp.raise_for_status()
    group_data = group_resp.json()

    if not group_data.get("value"):
        raise ValueError(f"Entra group '{group_name}' not found.")

    group_id = group_data["value"][0]["id"]

    add_member_url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"
    body = {
        "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_object_id}"
    }

    add_resp = requests.post(add_member_url, headers=headers, json=body)
    if add_resp.status_code not in (200, 204):
        raise RuntimeError(
            f"Failed to add user to Entra group '{group_name}'. "
            f"Status: {add_resp.status_code}, Response: {add_resp.text}"
        )


def add_user_to_github_team(user_email, github_team_slug):
    """
    Add (or invite) a user to a GitHub team by email address,
    using a GitHub Personal Access Token (PAT).
    """
    if not (GITHUB_ORG and GITHUB_TOKEN):
        raise ValueError("Missing GitHub credentials in Azure App Settings.")

    url = f"https://api.github.com/orgs/{GITHUB_ORG}/teams/{github_team_slug}/memberships/{user_email}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {"role": "member"}

    resp = requests.put(url, headers=headers, json=payload)
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Failed to add user to GitHub team '{github_team_slug}'. "
            f"Status: {resp.status_code}, Response: {resp.text}"
        )


def sync_user(user_email, entra_group_name):
    """
    Orchestrates the entire process:
    1) Acquire a Graph token
    2) Find the user's Entra Object ID by email
    3) Add them to the specified Entra group
    4) Map the Entra group to a GitHub team
    5) Add them to that GitHub team
    """
    token = get_graph_token()

    user_object_id = get_user_object_id_by_email(token, user_email)
    if not user_object_id:
        raise ValueError(f"No Entra user found with email '{user_email}'.")

    add_user_to_entra_group(token, user_object_id, entra_group_name)

    github_team_slug = ENTRA_TO_GITHUB_MAP.get(entra_group_name)
    if not github_team_slug:
        raise ValueError(
            f"No matching GitHub team slug for Entra group '{entra_group_name}' "
            "in ENTRA_TO_GITHUB_MAP."
        )

    add_user_to_github_team(user_email, github_team_slug)


# ---------------------------------------------------------
# Define the HTTP-triggered function using the v2 model
# ---------------------------------------------------------
@app.function_name(name="SyncUserFunction")
@app.route(route="syncUserFunction", auth_level=func.AuthLevel.FUNCTION)
def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Deployed to Azure:
      https://ghub-entra-group-automation.azurewebsites.net/api/syncUserFunction?userEmail=user@example.com&entraGroupName=Frontend%20Team.
    """
    logging.info("SyncUserFunction triggered for Entra->GitHub membership.")

    user_email = req.params.get("userEmail")
    entra_group_name = req.params.get("entraGroupName")

    if not user_email or not entra_group_name:
        return func.HttpResponse(
            "Missing userEmail or entraGroupName in query string.",
            status_code=400
        )

    try:
        sync_user(user_email, entra_group_name)
        return func.HttpResponse(
            f"Successfully synced {user_email} to {entra_group_name}.",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(
            f"An error occurred: {str(e)}",
            status_code=500
        )
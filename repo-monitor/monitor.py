import sys
import os
import requests
import yaml
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def load_config(path: str = "config.yaml") -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: config file not found: {path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print("ERROR: failed to parse YAML config")
        print("Details:", e)
        sys.exit(1)


def send_email(subject: str, body: str) -> None:
    """
    Sends an email via SendGrid.
    Reads API key from environment variable: SENDGRID_API_KEY
    Reads sender/recipient from environment variables:
      - SENDGRID_SENDER_EMAIL  (must be your verified sender in SendGrid)
      - EMAIL_ADDRESS_NAHAR    (recipient)
    """
    api_key = os.getenv("SENDGRID_API_KEY")
    sender = os.getenv("SENDGRID_SENDER_EMAIL")
    recipient = os.getenv("EMAIL_ADDRESS_NAHAR")

    if not api_key:
        print("ERROR: Missing env var SENDGRID_API_KEY")
        sys.exit(1)
    if not sender:
        print("ERROR: Missing env var SENDGRID_SENDER_EMAIL (verified sender)")
        sys.exit(1)
    if not recipient:
        print("ERROR: Missing env var EMAIL_ADDRESS_NAHAR (recipient)")
        sys.exit(1)

    message = Mail(
        from_email=sender,
        to_emails=recipient,
        subject=subject,
        plain_text_content=body,
    )

    try:
        client = SendGridAPIClient(api_key)
        client.send(message)
    except Exception as e:
        print("ERROR: Failed to send email via SendGrid")
        print("Details:", e)
        sys.exit(1)


def main():
    cfg = load_config("config.yaml")

 owner = cfg.get("owner") or cfg.get("owner ")
repo_name = cfg.get("repo") or cfg.get("repo_name")
task_name = cfg.get("task_id") or cfg.get("task_name")
expected_students = cfg.get("students") or cfg.get("expected_students")

    url = f"https://api.github.com/repos/{owner}/{repo_name}/branches"

    # Step 3: error handling (network + http + json)
    try:
        response = requests.get(url, timeout=15)
    except requests.exceptions.RequestException as e:
        print("ERROR: Network/Request problem while contacting GitHub API")
        print("Details:", e)
        sys.exit(1)

    print("Status code:", response.status_code)

    if response.status_code != 200:
        print("ERROR: GitHub API returned a non-200 response")
        print("Response text:", response.text)
        sys.exit(1)

    try:
        branches = response.json()
    except ValueError:
        print("ERROR: Response is not valid JSON")
        print("Response text:", response.text)
        sys.exit(1)

    if not isinstance(branches, list):
        print("ERROR: Expected a list of branch objects, got:", type(branches))
        print("Raw JSON response:")
        print(branches)
        sys.exit(1)

    # Step 2: extract names
    actual_branches = [b["name"] for b in branches]

    # Step 4: expected branches
    expected_branches = [f"{task_name}-{student}" for student in expected_students]

    missing = sorted(list(set(expected_branches) - set(actual_branches)))

    print("\n=== RESULT ===")
    if missing:
        print("Missing submissions (branches not found):")
        for b in missing:
            print("-", b)
        sys.exit(2)

    # Step 7: Send email ONLY when all submitted
    subject = f"✅ All submissions completed: {task_name}"
    body = (
        f"Repository: {owner}/{repo_name}\n"
        f"Task: {task_name}\n\n"
        "All expected branches were found.\n\n"
        "Expected branches:\n"
        + "\n".join(f"- {b}" for b in expected_branches)
    )

    send_email(subject, body)
    print("Email sent via SendGrid ✅")
    sys.exit(0)


if __name__ == "__main__":
    main()

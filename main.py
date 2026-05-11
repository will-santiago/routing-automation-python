"""
Routing Automation Script
Automates the full routing endpoint flow:
  1. Auth API Token
  2. Base Project Routing
  3. Base Project Resource
  4. Change Project Resource Params
  5. Upload Project Resource Content
  6. Create Multi-Project

Requirements: requests, python-dotenv
"""

import json
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
HOST            = os.getenv("HOST", "").rstrip("/")
API_KEY         = os.getenv("API_KEY", "")
API_SECRET      = os.getenv("API_SECRET", "")
FILE_PATH       = os.getenv("FILE_PATH", "")
CONFIG_UUID     = os.getenv("CONFIG_UUID", "")
CLIENT_UUID     = os.getenv("CLIENT_UUID", "")
SOURCE_LOCALE   = os.getenv("SOURCE_LOCALE", "en_us")
RESOURCE_NAME   = os.getenv("RESOURCE_NAME", "teste.dita")
REFERENCE_NAME  = os.getenv("REFERENCE_NAME", "")
MULTI_PROJECT_REFERENCE = os.getenv("MULTI_PROJECT_REFERENCE", "MULTI PROJECT TEST 777")
RESPONSE_LOG_FILE = os.getenv("RESPONSE_LOG_FILE", "responses.txt")

# ── Validation ────────────────────────────────────────────────────────────────
def validate_config():
    required = {
        "HOST":        HOST,
        "API_KEY":     API_KEY,
        "API_SECRET":  API_SECRET,
        "FILE_PATH":   FILE_PATH,
        "CONFIG_UUID": CONFIG_UUID,
        "CLIENT_UUID": CLIENT_UUID,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    if not os.path.isfile(FILE_PATH):
        print(f"[ERROR] FILE_PATH does not point to a valid file: {FILE_PATH}")
        sys.exit(1)
    print("[INFO] Configuration validated successfully.")


def record_step_response(step_responses, step_name, response, payload=None):
    try:
        body = response.text
    except Exception:
        body = "<unable to decode response body>"

    entry = {
        "step": step_name,
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": body,
    }
    if payload is not None:
        entry["payload"] = payload

    step_responses.append(entry)


def save_step_responses(step_responses):
    output_path = os.path.join(os.getcwd(), RESPONSE_LOG_FILE)
    with open(output_path, "w", encoding="utf-8") as out_file:
        for entry in step_responses:
            out_file.write("=" * 80 + "\n")
            out_file.write(f"Step: {entry['step']}\n")
            out_file.write(f"Status: {entry['status_code']}\n")
            out_file.write("Headers:\n")
            out_file.write(json.dumps(entry["headers"], indent=2, ensure_ascii=False) + "\n")
            if "payload" in entry:
                out_file.write("Payload:\n")
                out_file.write(json.dumps(entry["payload"], indent=2, ensure_ascii=False) + "\n")
            out_file.write("Body:\n")
            out_file.write(entry["body"] + "\n")
            out_file.write("\n")
    print(f"[INFO] Step responses saved to {output_path}")


# ── Step 1 – Auth API Token ───────────────────────────────────────────────────
def authenticate(session: requests.Session, step_responses) -> str:
    auth_url = f"{HOST}/api/v3/auth"
    payload = {
        "accessKey": API_KEY,
        "secret":    API_SECRET,
    }
    print(f"[INFO] Authenticating at {auth_url} ...")
    response = session.post(
        auth_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    record_step_response(step_responses, "Step 1 – Auth API Token", response, payload)
    print(f"[DEBUG] Step 1 response: {response.text}")

    token = response.headers.get("X-AUTH-TOKEN")

    if not token:
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type.lower() and response.text.strip():
            data = response.json()
            token = data.get("token") or data.get("accessToken") or data.get("authToken")

    if not token:
        raise RuntimeError(
            f"Authentication succeeded but no token was found. "
            f"Status: {response.status_code}, Body: {response.text[:500]}"
        )

    session.headers.update({"X-AUTH-TOKEN": token})
    print("[INFO] Authentication successful. Token applied to session headers.")
    return token


# ── Step 2 – Base Project Routing ─────────────────────────────────────────────
def create_base_project(session: requests.Session, step_responses) -> str:
    url = f"{HOST}/api/v3/project"
    params = {
        "id-only":     "true",
        "sourceLocale": SOURCE_LOCALE,
        "clientUuid":  CLIENT_UUID,
    }
    headers = {
        "Accept": "*/*",
        "X-AUTH-TOKEN": session.headers.get("X-AUTH-TOKEN", ""),
    }
    print(f"[INFO] Creating base project at {url} ...")
    response = session.post(url, params=params, headers=headers)
    response.raise_for_status()
    record_step_response(step_responses, "Step 2 – Base Project Routing", response)
    print(f"[DEBUG] Step 2 response: {response.text}")
    project_uuid = response.json().get("uuid")
    if not project_uuid:
        print(f"[ERROR] Could not retrieve projectUuid from response: {response.text}")
        sys.exit(1)
    print(f"[INFO] Base project created. projectUuid = {project_uuid}")
    return project_uuid


# ── Step 3 – Base Project Resource ────────────────────────────────────────────
def create_project_resource(session: requests.Session, project_uuid: str, step_responses) -> str:
    url = f"{HOST}/api/v3/project/{project_uuid}/resource"
    payload = {"name": RESOURCE_NAME}
    print(f"[INFO] Creating project resource at {url} ...")
    response = session.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    record_step_response(step_responses, "Step 3 – Base Project Resource", response, payload)
    print(f"[DEBUG] Step 3 response: {response.text}")
    resource_uuid = response.json().get("uuid")
    if not resource_uuid:
        print(f"[ERROR] Could not retrieve projectResourceUuid from response: {response.text}")
        sys.exit(1)
    print(f"[INFO] Project resource created. projectResourceUuid = {resource_uuid}")
    return resource_uuid


# ── Step 4 – Change Project Resource Params ───────────────────────────────────
def change_resource_params(session: requests.Session, project_uuid: str, resource_uuid: str, step_responses):
    url = f"{HOST}/api/v3/project/{project_uuid}/resource/{resource_uuid}/file-params"
    payload = {
        "applySourceSegmentation": True,
        "extractTerms": True,
        "termsParams": {
            "keepCase": False,
            "maxWordsPerTerm": 3,
            "minOccurrences": 2,
            "minWordsPerTerm": 1,
            "removeSubTerms": True,
            "sortByOccurrence": True,
            "topTermsLimit": 10
        },
        "parameters": {
            "escapeAmp": True,
            "escapeApos": True,
            "escapeGT": True,
            "escapeNbsp": False,
            "escapeQuotes": True,
            "inlineCdata": True,
            "lineBreakAsCode": False,
            "whiteSpaces": True
        },
        "parserFilter": "xmlstream-dita2",
        "tagRegex": "<https:\/\/.*[-a-zA-Z0-9@:%._\\+~#=].+\\.[a-zA-Z0-9()].+\\b([-a-zA-Z0-9()@:%_\\+.~#?&\\/\\/=]*)>|%\\{[^\\}]+\\}%?|\\{[^\\}]+\\}\\}|\\\"([^\\\"]+?)\\\"\\s*:|<[^>]+>|&#\\w+;|\\\\n|\\\\r|&quot;|&lt;[^&gt;]+&gt;",
        "defaultFilterSettings": True,
        "defaultFilter": "DITA"
    }
    if REFERENCE_NAME:
        payload["referenceName"] = REFERENCE_NAME

    print(f"[INFO] Setting resource file-params at {url} ...")
    print(f"[DEBUG] Step 4 payload JSON: {json.dumps(payload)}")
    response = session.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    record_step_response(step_responses, "Step 4 – Change Project Resource Params", response, payload)
    print(f"[DEBUG] Step 4 response: {response.text}")
    print("[INFO] Resource file-params updated successfully.")


# ── Step 5 – Upload Project Resource Content ──────────────────────────────────
def upload_resource_content(session: requests.Session, project_uuid: str, resource_uuid: str, step_responses):
    url = f"{HOST}/api/v3/project/{project_uuid}/resource/{resource_uuid}/content"
    print(f"[INFO] Uploading resource content from '{FILE_PATH}' to {url} ...")
    with open(FILE_PATH, "rb") as f:
        files = {"file": (os.path.basename(FILE_PATH), f)}
        response = session.put(url, files=files)
    response.raise_for_status()
    record_step_response(step_responses, "Step 5 – Upload Project Resource Content", response)
    print(f"[DEBUG] Step 5 response: {response.text}")
    print("[INFO] Resource content uploaded successfully.")


# ── Step 6 – Create Multi-Project ─────────────────────────────────────────────
def create_multi_project(session: requests.Session, project_uuid: str, step_responses):
    url = f"{HOST}/api/v3/multi-project/{CONFIG_UUID}/project-create"
    payload = {
        "baseProjectUuid": project_uuid,
        "reference": MULTI_PROJECT_REFERENCE,
        "sourceLanguage": "en_us",
        "projects": [
            {
                "id": 5672,
                "uuid": "8686c847-8c23-4e6e-98b2-4f219c2af12d",
                "targetLanguages": ["pt_br"],
                "workflows": ["TRANSLATION", "REVIEW"],
                "defaultContactPerson": {"id": 47269},
                "instructions": "Testando Teste",
                "priceList": {"uuid": "66a51aa2-2459-493b-b6f1-3224f582f712"},
                "glossaryList": [{"bwGlossaryId": 10711}],
                "tmList": [{"atlasTmId": 31026}]
            },
            {
                "id": 6334,
                "uuid": "77b6112c-4299-490d-932f-dfe373ff0250",
                "targetLanguages": ["es_es"],
                "workflows": ["TRANSLATION", "REVIEW"],
                "defaultContactPerson": {"id": 47269},
                "instructions": "Testando teste",
                "priceList": {"uuid": "66a51aa2-2459-493b-b6f1-3224f582f712"},
                "glossaryList": [{"bwGlossaryId": 11139}],
                "tmList": [{"atlasTmId": 35477}]
            }
        ]
    }
    print(f"[INFO] Creating multi-project at {url} ...")
    print(f"[DEBUG] Step 6 payload JSON: {json.dumps(payload)}")
    response = session.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    record_step_response(step_responses, "Step 6 – Create Multi-Project", response, payload)
    print(f"[DEBUG] Step 6 response: {response.text}")
    print(f"[INFO] Multi-project created successfully. Response: {response.text}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Routing Automation Script")
    print("=" * 60)

    validate_config()

    session = requests.Session()
    step_responses = []

    try:
        # Step 1 – Authenticate
        authenticate(session, step_responses)

        # Step 2 – Create base project
        project_uuid = create_base_project(session, step_responses)

        # Step 3 – Create project resource
        resource_uuid = create_project_resource(session, project_uuid, step_responses)

        # Step 4 – Change resource params
        change_resource_params(session, project_uuid, resource_uuid, step_responses)

        # Step 5 – Upload resource content
        upload_resource_content(session, project_uuid, resource_uuid, step_responses)

        # Step 6 – Create multi-project
        create_multi_project(session, project_uuid, step_responses)

        save_step_responses(step_responses)

        print("=" * 60)
        print("  All steps completed successfully!")
        print(f"  projectUuid:         {project_uuid}")
        print(f"  projectResourceUuid: {resource_uuid}")
        print("=" * 60)

    except requests.exceptions.HTTPError as http_err:
        print(f"[ERROR] HTTP error occurred: {http_err}")
        print(f"        Response body: {http_err.response.text if http_err.response else 'N/A'}")
        sys.exit(1)
    except requests.exceptions.ConnectionError as conn_err:
        print(f"[ERROR] Connection error: {conn_err}")
        sys.exit(1)
    except requests.exceptions.Timeout as timeout_err:
        print(f"[ERROR] Request timed out: {timeout_err}")
        sys.exit(1)
    except requests.exceptions.RequestException as req_err:
        print(f"[ERROR] An unexpected request error occurred: {req_err}")
        sys.exit(1)


if __name__ == "__main__":
    main()

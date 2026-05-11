# Routing Automation – Python Script

A Python automation script that executes the full routing endpoint flow against the API, from authentication through multi-project creation.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Environment Variables](#environment-variables)
4. [Running the Script](#running-the-script)
5. [Endpoint Flow](#endpoint-flow)
6. [File Upload Notes](#file-upload-notes)
7. [Config UUID Notes](#config-uuid-notes)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3.8 or higher
- `pip` package manager
- A valid API host, access key, and secret
- A file to upload as the project resource content (e.g., an `.xlf` file)

---

## Installation

1. **Clone or download** this project directory to your machine.

2. **Create and activate a virtual environment** (recommended):

   ```bash
   python -m venv venv

   # macOS / Linux
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

---

## Environment Variables

Copy the provided `.env.example` template and fill in your values:

```bash
cp .env.example .env
```

Then edit `.env` with your actual values:

| Variable         | Required | Description                                                                 |
|------------------|----------|-----------------------------------------------------------------------------|
| `HOST`           | ✅ Yes   | Base URL of the API (no trailing slash). E.g. `https://api.example.com`    |
| `API_KEY`        | ✅ Yes   | Your API access key used for authentication.                                |
| `API_SECRET`     | ✅ Yes   | Your API secret used for authentication.                                    |
| `FILE_PATH`      | ✅ Yes   | Path to the file to upload as resource content (e.g. `./resource.xlf`).    |
| `CONFIG_UUID`    | ✅ Yes   | UUID of the multi-project configuration (see [Config UUID Notes](#config-uuid-notes)). |
| `CLIENT_UUID`    | ✅ Yes   | UUID of the client to associate with the base project.                      |
| `SOURCE_LOCALE`  | ⬜ No    | Source locale for the project. Defaults to `en_us`.                        |
| `RESOURCE_NAME`  | ⬜ No    | Name assigned to the project resource. Defaults to `resource.xlf`.         |
| `REFERENCE_NAME` | ⬜ No    | Reference name for the resource file-params step. Leave blank if unused.   |
| `MULTI_PROJECT_REFERENCE` | ⬜ No | Reference value for the multi-project creation step. Defaults to `MULTI PROJECT TEST 777`. |
| `MULTI_PROJECT_SOURCE_LANGUAGE` | ⬜ No | Source language for multi-project creation. Defaults to `SOURCE_LOCALE`. |
| `MULTI_PROJECT_PAYLOAD_JSON` | ⬜ No | Optional inline JSON payload for Step 6. If set, it overrides the default multi-project request body. |
| `MULTI_PROJECT_PAYLOAD_PATH` | ⬜ No | Optional path to a JSON file containing the full Step 6 payload. Overrides the default payload. |

> ⚠️ **Never commit your `.env` file** with real credentials to version control. Add `.env` to your `.gitignore`.

---

## Running the Script

Make sure your `.env` file is filled in, then run:

```bash
python main.py
```

On success, the script will print the `projectUuid` and `projectResourceUuid` created during the run.

---

## Endpoint Flow

The script executes the following steps in order:

### 1. Auth API Token
- **Method:** `POST`
- **URL:** `{HOST}/api/v3/auth`
- **Body:** `{ "accessKey": "<API_KEY>", "secret": "<API_SECRET>" }`
- **Result:** Retrieves an auth token and sets it as the `X-AUTH-TOKEN` header for all subsequent requests.

---

### 2. Base Project Routing
- **Method:** `POST`
- **URL:** `{HOST}/api/v3/project?id-only=true&sourceLocale={SOURCE_LOCALE}&clientUuid={CLIENT_UUID}`
- **Result:** Creates a new base project and captures the `projectUuid` from the response.

---

### 3. Base Project Resource
- **Method:** `POST`
- **URL:** `{HOST}/api/v3/project/{projectUuid}/resource`
- **Body:** `{ "name": "<RESOURCE_NAME>" }`
- **Result:** Creates a resource under the project and captures the `projectResourceUuid`.

---

### 4. Change Project Resource Params
- **Method:** `POST`
- **URL:** `{HOST}/api/v3/project/{projectUuid}/resource/{projectResourceUuid}/file-params`
- **Body:** Optional `referenceName` if `REFERENCE_NAME` is set.
- **Result:** Configures file parameters for the resource.

---

### 5. Upload Project Resource Content
- **Method:** `PUT`
- **URL:** `{HOST}/api/v3/project/{projectUuid}/resource/{projectResourceUuid}/content`
- **Body:** Multipart form-data with the file specified by `FILE_PATH`.
- **Result:** Uploads the file content to the resource.

---

### 6. Create Multi-Project
- **Method:** `POST`
- **URL:** `{HOST}/api/v3/multi-project/{CONFIG_UUID}/project-create`
- **Body:**
  - By default the script sends:
    `{ "baseProjectUuid": "<projectUuid>", "reference": "<MULTI_PROJECT_REFERENCE>", "sourceLanguage": "<MULTI_PROJECT_SOURCE_LANGUAGE>" }`
  - You can override the entire request body using `MULTI_PROJECT_PAYLOAD_JSON` or `MULTI_PROJECT_PAYLOAD_PATH`.
- **Result:** Triggers multi-project creation using the base project and the specified configuration.

---

## File Upload Notes

- The file at `FILE_PATH` is uploaded as **multipart form-data** in Step 5.
- Supported file types depend on your API configuration (commonly `.xlf`, `.xliff`, `.po`, `.json`, etc.).
- Make sure the file exists and is readable before running the script. The script validates this at startup.
- Use an absolute path or a path relative to the directory where you run the script.

---

## Config UUID Notes

- `CONFIG_UUID` refers to an existing **multi-project configuration** in the system.
- You can find this UUID in your platform's multi-project settings or by calling the `List Multi-Project Configs` endpoint.
- This value is fixed per configuration and does not change between runs unless you switch configurations.

---

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---|---|---|
| `Missing required environment variables` | `.env` not filled in or not found | Ensure `.env` exists in the same directory and all required fields are set. |
| `FILE_PATH does not point to a valid file` | Wrong path or file missing | Check the `FILE_PATH` value and confirm the file exists. |
| `Invalid MULTI_PROJECT_PAYLOAD_JSON` | JSON string is malformed | Fix the JSON syntax in `MULTI_PROJECT_PAYLOAD_JSON` or use `MULTI_PROJECT_PAYLOAD_PATH` instead. |
| `MULTI_PROJECT_PAYLOAD_PATH does not point to a valid file` | Wrong path or file missing | Confirm the file exists and the path is correct. |
| `HTTP 401 Unauthorized` | Invalid credentials | Verify `API_KEY` and `API_SECRET` are correct. |
| `HTTP 404 Not Found` | Wrong `HOST` or UUID | Double-check `HOST`, `CLIENT_UUID`, and `CONFIG_UUID`. |
| `Connection error` | Network issue or wrong host | Confirm the `HOST` URL is reachable from your machine. |

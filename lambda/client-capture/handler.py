import re
from datetime import datetime, timezone
from urllib.parse import parse_qsl

import boto3
from botocore.exceptions import ClientError

# --- Config ---------------------------------------------------------------

TABLE_NAME = "caninecommunication-clients"
REGION = "us-east-2"
MAX_NAME_LENGTH = 200
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Public lead-capture form, no cookies/credentials involved - a permissive
# origin keeps local dev (http://localhost:1313) working against the real
# endpoint without a second CORS config for prod.
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

dynamodb = boto3.client("dynamodb", region_name=REGION)


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    if method == "OPTIONS":
        # application/x-www-form-urlencoded is a CORS-safelisted content
        # type, so a plain form POST from the Book page never actually
        # triggers a preflight - this only fires if something later (e.g.
        # a custom header) turns this into a non-simple request.
        return _response(204, "", cors_only=True)

    # A plain <form> submitted by htmx sends application/x-www-form-urlencoded
    # (the browser's native form encoding), not JSON - parsed the same way
    # regardless of Content-Type since this endpoint only ever expects form
    # fields, never a JSON body.
    body = dict(parse_qsl(event.get("body") or ""))

    name = (body.get("name") or "").strip()
    email = (body.get("email") or "").strip().lower()

    if not name or len(name) > MAX_NAME_LENGTH:
        return _response(400, _error_html("Please enter your name."))
    if not EMAIL_RE.match(email):
        return _response(400, _error_html("Please enter a valid email address."))

    consent_timestamp = datetime.now(timezone.utc).isoformat()

    try:
        # email as the partition key IS the dedup mechanism: a second
        # signup with the same email overwrites this item (refreshed name +
        # consent timestamp) rather than creating a duplicate record - see
        # ticket #5's "duplicate email -> update, not duplicate" criterion.
        # appointment_history starts empty; nothing populates it yet.
        dynamodb.put_item(
            TableName=TABLE_NAME,
            Item={
                "email": {"S": email},
                "name": {"S": name},
                "consent_timestamp": {"S": consent_timestamp},
                "appointment_history": {"L": []},
            },
        )
    except ClientError as e:
        print("DynamoDB put_item failed:", str(e))
        return _response(502, _error_html("Something went wrong - please try again."))

    return _response(200, _success_html(name))


def _success_html(name):
    return '<p class="has-text-weight-semibold">Thanks, {} &mdash; you\'re on the list.</p>'.format(
        _escape(name)
    )


def _error_html(message):
    return '<p class="has-text-danger">{}</p>'.format(_escape(message))


def _escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _response(status, body_html, cors_only=False):
    headers = dict(CORS_HEADERS)
    if not cors_only:
        headers["Content-Type"] = "text/html"
    return {"statusCode": status, "headers": headers, "body": body_html}

import glob
import html
import json
import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# --- Model / region -----------------------------------------------------

MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
REGION = "us-east-2"

# --- Tunable limits -------------------------------------------------------
# Same starting values as griz.sh's chatbot (lambda/chatbot/handler.py in
# that repo) - no site-specific reason yet to diverge. Edit these to
# constrict/expand the cost/abuse envelope; no other code changes needed.

MAX_REQUESTS_PER_IP_PER_HOUR = 10
MAX_INPUT_CHARS = 1000
MAX_OUTPUT_TOKENS = 300
MONTHLY_SPEND_CEILING_USD = 10.00

# A user question can trigger at most this many Bedrock calls. The final
# call always has tools disabled, forcing a real text answer instead of
# yet another tool request - guarantees a bounded, predictable call count
# per question while still letting the model search more than once if its
# first query was too narrow.
MAX_TOOL_ITERATIONS = 3

INPUT_COST_PER_TOKEN_USD = 1.00 / 1_000_000
OUTPUT_COST_PER_TOKEN_USD = 5.00 / 1_000_000

_ESTIMATED_MAX_INPUT_TOKENS = MAX_INPUT_CHARS // 4
_FALLBACK_SYSTEM_PROMPT_TOKENS = 3000


def _max_request_cost_microdollars():
    """Worst case: every one of MAX_TOOL_ITERATIONS calls resends the full
    system prompt (both content indexes + instructions) plus the user's
    question. Deliberately conservative, same reasoning as griz.sh's
    version of this function."""
    if _content_index_cache is None:
        system_prompt_tokens = _FALLBACK_SYSTEM_PROMPT_TOKENS
    else:
        system_prompt_tokens = len(_build_system_prompt()) // 4
    per_call_input_tokens = system_prompt_tokens + _ESTIMATED_MAX_INPUT_TOKENS
    return round(
        (
            per_call_input_tokens * INPUT_COST_PER_TOKEN_USD
            + MAX_OUTPUT_TOKENS * OUTPUT_COST_PER_TOKEN_USD
        )
        * 1_000_000
        * MAX_TOOL_ITERATIONS
    )


# A separate table from griz.sh's chatbot-limits - this is a separate
# Lambda by design (see ADR 0003: cheaper on Bedrock tokens than a shared
# bot carrying both sites' indexes in every system prompt), so it tracks
# its own rate limit and spend independently rather than sharing a budget
# with griz.sh's bot.
RATE_LIMIT_TABLE = "caninecommunication-chatbot-limits"

# --- Site content / capabilities -------------------------------------------

# This site's own index, once deployed. Placeholder domain - the real site
# isn't live yet (AWS/domain/hosting setup is deliberately sequenced after
# this ticket, see CLAUDE.md).
SITE_CONTENT_INDEX_URL = "https://caninecommunication.com/index.json"
# griz.sh is already live - this one is real today.
GRIZ_CONTENT_INDEX_URL = "https://griz.sh/index.json"

CAPABILITIES_FILE = os.path.join(os.path.dirname(__file__), "capabilities.json")
RESPONSES_DIR = os.path.join(os.path.dirname(__file__), "responses")
MAX_TOOL_RESULT_ITEMS = 5

SYSTEM_PROMPT_INSTRUCTIONS = (
    "You are a helpful assistant embedded on a dog training business's website. "
    "This business's owner also writes a separate, more casual training blog at "
    "griz.sh. Answer questions about this business (services, booking, policies) "
    "using search_site_content. For general dog-training or dog-psychology "
    "questions better suited to the blog, use search_griz_content. For anything "
    "that doesn't map onto a real page - like current availability - try "
    "search_custom_responses. Keep answers short and point people at the "
    "relevant page URL(s) when you have one. Do not answer from general "
    "knowledge questions unrelated to this site's or griz.sh's content; say "
    "you don't know and suggest they browse the site or use the Book a Session "
    "page instead."
)

bedrock = boto3.client("bedrock-runtime", region_name=REGION)
dynamodb = boto3.client("dynamodb", region_name=REGION)
cloudwatch = boto3.client(
    "cloudwatch",
    region_name=REGION,
    config=Config(connect_timeout=2, read_timeout=2, retries={"max_attempts": 1}),
)

METRIC_NAMESPACE = "CanineCommunicationChatbot"

with open(CAPABILITIES_FILE) as f:
    _CAPABILITIES = json.load(f)["tools"]

_custom_responses_cache = None


def _get_custom_responses():
    global _custom_responses_cache
    if _custom_responses_cache is None:
        responses = []
        for path in sorted(glob.glob(os.path.join(RESPONSES_DIR, "*.json"))):
            with open(path) as f:
                responses.append(json.load(f))
        _custom_responses_cache = responses
    return _custom_responses_cache


# Cached across warm Lambda invocations - refetched whenever a new
# execution environment starts, so both indexes stay reasonably current
# without redeploying the Lambda just for a content change on either site.
_content_index_cache = None


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    if method == "OPTIONS":
        return _response(204, "", cors_only=True)

    ip = _get_source_ip(event)

    if not _check_and_increment_ip_limit(ip):
        _record_limit_metric("RateLimitRejection")
        return _response(
            429,
            _error_html(
                "You've asked a lot of questions recently. Please wait a bit and try again."
            ),
        )

    body = dict(_parse_qsl_or_json(event.get("body") or ""))
    question = (body.get("question") or "").strip()
    if not question:
        return _response(400, _error_html("Please enter a question."))
    if len(question) > MAX_INPUT_CHARS:
        return _response(
            400, _error_html(f"Question is too long (max {MAX_INPUT_CHARS} characters).")
        )

    # Pre-warm the cache before spend-reservation math runs, so it reflects
    # the real index size rather than the conservative fallback. Never
    # raises (see _get_content_index) - if this site's own index isn't
    # reachable yet (e.g. before it's deployed), this just caches empty
    # and the agent still answers from griz.sh content and custom
    # responses.
    _get_content_index(SITE_CONTENT_INDEX_URL)

    reserved_microdollars = _reserve_monthly_spend()
    if reserved_microdollars is None:
        _record_limit_metric("SpendCeilingRejection")
        return _response(
            429,
            _error_html(
                "The chatbot has hit its monthly usage limit. Please try again next month."
            ),
        )

    try:
        answer, total_input_tokens, total_output_tokens = _answer_question(question)

        actual_cost_microdollars = round(
            total_input_tokens * INPUT_COST_PER_TOKEN_USD * 1_000_000
            + total_output_tokens * OUTPUT_COST_PER_TOKEN_USD * 1_000_000
        )
        _true_up_monthly_spend(actual_cost_microdollars, reserved_microdollars)

        return _response(200, _markdown_to_safe_html(answer))
    except Exception as e:
        print("Bedrock invoke failed:", str(e))
        _true_up_monthly_spend(0, reserved_microdollars)
        return _response(502, _error_html("Something went wrong answering your question."))


def _parse_qsl_or_json(raw_body):
    """The chat widget's form posts application/x-www-form-urlencoded
    (htmx's default for a plain <form>), same as the client-capture
    endpoint - this just extracts `question` the same way."""
    from urllib.parse import parse_qsl

    return parse_qsl(raw_body)


# --- Question answering / tool use -----------------------------------------
# Markdown-to-HTML conversion and the bold/link regexes below are copied
# unchanged from griz.sh's chatbot - same reasoning applies: the model's
# answer is shaped by an arbitrary visitor question, so it's never trusted
# as raw HTML, only this fixed small set of safe tags is added back after
# escaping everything first.

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)*]+)\)")


def _markdown_to_safe_html(text):
    rendered = html.escape(text, quote=True)
    rendered = _LINK_RE.sub(
        lambda m: '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>'.format(
            m.group(2), m.group(1)
        ),
        rendered,
    )
    rendered = _BOLD_RE.sub(r"<strong>\1</strong>", rendered)

    html_parts = []
    paragraph_lines = []
    list_items = []

    def flush_paragraph():
        if paragraph_lines:
            html_parts.append("<p>{}</p>".format("<br>".join(paragraph_lines)))
            paragraph_lines.clear()

    def flush_list():
        if list_items:
            html_parts.append(
                "<ul>{}</ul>".format("".join("<li>{}</li>".format(i) for i in list_items))
            )
            list_items.clear()

    for line in (l.strip() for l in rendered.strip().split("\n")):
        if not line:
            flush_paragraph()
            flush_list()
        elif line.startswith("- "):
            flush_paragraph()
            list_items.append(line[2:].strip())
        else:
            flush_list()
            paragraph_lines.append(line)

    flush_paragraph()
    flush_list()
    return "".join(html_parts)


def _answer_question(question):
    tools = _get_enabled_tools()
    messages = [{"role": "user", "content": question}]
    total_input_tokens = 0
    total_output_tokens = 0

    payload = None
    for i in range(MAX_TOOL_ITERATIONS):
        is_last_call = i == MAX_TOOL_ITERATIONS - 1
        payload = _invoke_bedrock(messages, None if is_last_call else tools)
        usage = payload.get("usage", {})
        total_input_tokens += usage.get("input_tokens", 0)
        total_output_tokens += usage.get("output_tokens", 0)

        if payload.get("stop_reason") != "tool_use":
            break

        messages.append({"role": "assistant", "content": payload["content"]})
        tool_results = [
            {
                "type": "tool_result",
                "tool_use_id": block["id"],
                "content": json.dumps(_execute_tool(block["name"], block.get("input", {}))),
            }
            for block in payload["content"]
            if block["type"] == "tool_use"
        ]
        messages.append({"role": "user", "content": tool_results})

    answer = next(
        (b["text"] for b in payload.get("content", []) if b.get("type") == "text"), ""
    )
    if not answer:
        answer = (
            "I couldn't find a clear answer to that - try rephrasing your "
            "question or browsing the site directly."
        )
    return answer, total_input_tokens, total_output_tokens


def _invoke_bedrock(messages, tools):
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": MAX_OUTPUT_TOKENS,
        "system": [
            {
                "type": "text",
                "text": _build_system_prompt(),
                "cache_control": {"type": "ephemeral"},
            }
        ],
        "messages": messages,
    }
    if tools:
        request_body["tools"] = tools

    result = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(request_body),
    )
    return json.loads(result["body"].read())


def _build_system_prompt():
    site_index = _get_content_index(SITE_CONTENT_INDEX_URL)
    compact_site_index = [
        {"title": p.get("title") or "", "url": p.get("url") or "", "tags": p.get("tags") or []}
        for p in site_index
    ]
    return (
        SYSTEM_PROMPT_INSTRUCTIONS
        + "\n\nThis site's content index (titles, URLs, tags - use "
        "search_site_content for full excerpts of any of these):\n"
        + json.dumps(compact_site_index)
    )


def _enabled_capabilities():
    return {t["name"]: t for t in _CAPABILITIES if t.get("enabled")}


def _get_enabled_tools():
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for t in _enabled_capabilities().values()
    ]


def _execute_tool(name, tool_input):
    if name not in _enabled_capabilities():
        return {"error": f"Tool '{name}' is not currently enabled."}

    query = tool_input.get("query", "")
    if name == "search_site_content":
        return _search_index(_get_content_index(SITE_CONTENT_INDEX_URL), query)
    if name == "search_griz_content":
        return _search_index(_get_content_index(GRIZ_CONTENT_INDEX_URL), query)
    if name == "search_custom_responses":
        return _search_index(_get_custom_responses(), query, url_field=None)
    return {"error": f"Tool '{name}' has no implementation."}


def _search_index(index, query, url_field="url"):
    query_lower = query.lower().strip()
    if not query_lower:
        return []
    matches = [p for p in index if query_lower in _page_haystack(p)]
    return [_page_result(p, url_field) for p in matches[:MAX_TOOL_RESULT_ITEMS]]


def _page_haystack(page):
    return " ".join(
        [
            page.get("title") or "",
            " ".join(page.get("tags") or []),
            page.get("summary") or page.get("body") or "",
        ]
    ).lower()


def _page_result(page, url_field):
    result = {
        "title": page.get("title") or "",
        "tags": page.get("tags") or [],
        "excerpt": page.get("summary") or page.get("body") or "",
    }
    if url_field:
        result["url"] = page.get(url_field) or ""
    return result


def _get_content_index(url):
    """Never raises: a fetch failure caches an empty index for the rest of
    this warm container rather than crashing the request. This matters
    concretely right now - SITE_CONTENT_INDEX_URL points at a site that
    isn't deployed yet, so it fails every call until that changes, and the
    agent should still answer from griz.sh content and custom responses
    in the meantime rather than 502ing every question."""
    global _content_index_cache
    if _content_index_cache is None:
        _content_index_cache = {}
    if url not in _content_index_cache:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                _content_index_cache[url] = json.loads(resp.read())
        except Exception as e:
            print(f"Content index fetch failed for {url}:", str(e))
            _content_index_cache[url] = []
    return _content_index_cache[url]


# --- Rate limiting / spend circuit-breaker --------------------------------
# Identical logic to griz.sh's chatbot, against this Lambda's own table.


def _record_limit_metric(metric_name):
    try:
        cloudwatch.put_metric_data(
            Namespace=METRIC_NAMESPACE,
            MetricData=[{"MetricName": metric_name, "Value": 1, "Unit": "Count"}],
        )
    except Exception as e:
        print("Failed to publish limit metric:", str(e))


def _get_source_ip(event):
    return event.get("requestContext", {}).get("http", {}).get("sourceIp", "unknown")


def _current_month_key():
    return f"spend#{datetime.now(timezone.utc).strftime('%Y-%m')}"


def _spend_ttl():
    return int((datetime.now(timezone.utc) + timedelta(days=62)).timestamp())


def _check_and_increment_ip_limit(ip):
    now = datetime.now(timezone.utc)
    hour_bucket = now.strftime("%Y-%m-%dT%H")
    pk = f"ip#{ip}#{hour_bucket}"
    ttl = int((now + timedelta(hours=2)).timestamp())

    result = dynamodb.update_item(
        TableName=RATE_LIMIT_TABLE,
        Key={"pk": {"S": pk}},
        UpdateExpression="ADD #c :incr SET #t = if_not_exists(#t, :ttl)",
        ExpressionAttributeNames={"#c": "count", "#t": "ttl"},
        ExpressionAttributeValues={":incr": {"N": "1"}, ":ttl": {"N": str(ttl)}},
        ReturnValues="UPDATED_NEW",
    )
    count = int(result["Attributes"]["count"]["N"])
    return count <= MAX_REQUESTS_PER_IP_PER_HOUR


def _reserve_monthly_spend():
    pk = _current_month_key()
    reserve_microdollars = _max_request_cost_microdollars()
    ceiling_microdollars = round(MONTHLY_SPEND_CEILING_USD * 1_000_000)
    threshold = ceiling_microdollars - reserve_microdollars

    try:
        dynamodb.update_item(
            TableName=RATE_LIMIT_TABLE,
            Key={"pk": {"S": pk}},
            UpdateExpression="ADD microdollars :incr SET #t = if_not_exists(#t, :ttl)",
            ConditionExpression="attribute_not_exists(microdollars) OR microdollars < :threshold",
            ExpressionAttributeNames={"#t": "ttl"},
            ExpressionAttributeValues={
                ":incr": {"N": str(reserve_microdollars)},
                ":threshold": {"N": str(threshold)},
                ":ttl": {"N": str(_spend_ttl())},
            },
        )
        return reserve_microdollars
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return None
        raise


def _true_up_monthly_spend(actual_cost_microdollars, reserved_microdollars):
    diff = actual_cost_microdollars - reserved_microdollars
    if diff == 0:
        return
    dynamodb.update_item(
        TableName=RATE_LIMIT_TABLE,
        Key={"pk": {"S": _current_month_key()}},
        UpdateExpression="ADD microdollars :diff",
        ExpressionAttributeValues={":diff": {"N": str(diff)}},
    )


# --- HTTP plumbing ----------------------------------------------------------
# Direct HTML responses (not JSON) - htmx swaps the body in as-is, same
# pattern already used by the FAQ fragments and the client-capture form.
# griz.sh's chatbot returns JSON + relies on htmx-ext-json-enc and
# htmx-ext-client-side-templates (Mustache) to unwrap it; this Lambda
# skips that entirely since a direct HTML response needs none of it.

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def _error_html(message):
    return '<p class="has-text-danger">{}</p>'.format(html.escape(message, quote=True))


def _response(status, body_html, cors_only=False):
    headers = dict(CORS_HEADERS)
    if not cors_only:
        headers["Content-Type"] = "text/html"
    return {"statusCode": status, "headers": headers, "body": body_html}

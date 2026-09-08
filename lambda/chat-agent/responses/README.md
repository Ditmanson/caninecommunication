# Custom responses

Hand-editable canned answers the chat agent can surface alongside real page
content and griz.sh's content. Searched the same way as the site's own
content index (keyword match over `title`/`tags`/`body`) - see
`search_custom_responses` in `../handler.py`.

## Format

One JSON file per response, any filename ending in `.json`:

```json
{
  "title": "Short label for this response",
  "tags": ["keyword", "another keyword", "phrase someone might type"],
  "body": "The actual answer text, in plain prose. This is what the model sees and may quote or paraphrase."
}
```

- `title` and `tags` are what gets matched against a visitor's question -
  put in every phrasing you can think of someone actually typing.
- `body` is the real content. Keep it factual and current - this is a
  bypass around the site's own published pages, so nothing here gets the
  "is this still accurate" scrutiny a real page edit would.
- Response files are bundled into the Lambda zip at deploy time (not
  fetched at runtime), so any change here - editing a file, adding one,
  removing one - needs `../deploy.sh` re-run to take effect. There's no
  live-reload from this directory.

See `example-availability.json` for a real example.

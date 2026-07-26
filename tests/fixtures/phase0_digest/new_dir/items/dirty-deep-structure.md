# Filter subsystem reference
## Configuration
### Filter fields
- status
  - active
    - visible in every chart type
  - archived
    - hidden unless include_archived is set
- chart_type
  - bar
  - line
#### Field limits
| Field | Type | Default | Max |
| --- | --- | --- | --- |
| page_size | integer | 50 | 500 |
| timeout | seconds | 30 | 300 |
| retries | integer | 3 | 10 |
### Error codes
| Code | Meaning |
| --- | --- |
| E_FILTER_17 | invalid filter predicate |
| E_CHART_09 | chart type rejects the filter |
#### Example request
```python
payload = {"status": "active", "chart_type": "bar"}
response = client.post("/v2/filters", json=payload, timeout=30)
assert response.status_code == 200
```
#### Example response
```json
{"status": "active", "rows": 50, "truncated": false}
```
FAQ: Does the table structure survive the digest?
Yes, table rows and code block lines must stay verbatim.
See https://design.example/deep-structure for the full reference.

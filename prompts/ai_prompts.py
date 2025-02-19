"""
This file holds a set of reusable prompt strings for various AI assistants.
"""

GEMINI_STATEMENT_PARSE = """\
Please parse the attached financial statement PDF and provide a concise summary, focusing on:
1. Transaction details and amounts
2. Payment timelines
3. Any relevant disclaimers or follow-up actions needed
"""

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=GEMINI_STATEMENT_PARSE
)
print(response.text)
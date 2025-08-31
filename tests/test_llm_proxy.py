import json
from mle_kit_mcp.tools import llm_proxy_local, bash


QUERY_SNIPPET = """
import httpx
headers = {{'Authorization': 'Bearer {token}'}}
json_payload = {{'model': 'gpt-4o', 'messages': [{{'role': 'user', 'content': 'Hello, how are you?'}}]}}
response = httpx.post("{url}", headers=headers, json=json_payload)
print(response.json())
"""


def test_llm_proxy_local():
    result = json.loads(llm_proxy_local(port=8001))
    token = result["token"]
    url = result["url"]
    assert url
    assert token

    snippet = QUERY_SNIPPET.format(url=url, token=token)
    result = bash(f'cat > test_query.py << "EOF"\n{snippet}\nEOF')
    result = bash("python test_query.py")
    assert "content" in result

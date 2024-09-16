import requests

URL="http://localhost:11434/api/generate"

def query_for_local_model(data):
    response = requests.post(
        url=URL,
        json=data,
        headers={"Content-Type": "application/json"},
    )
    # print(response.json())
    return response
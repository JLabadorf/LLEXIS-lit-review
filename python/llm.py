import  requests

LLM_PROXY_URL = "http://127.0.0.1:8000/llm/chat"  # Replace with your LLM proxy URL

#create a class for the client. it should take the model as an argument.
class Client:
    def __init__(self, model):
        self.model = model

    def send(self, message):
        provider = self.model.split(".")[0]  # Extract provider from model name
        if provider == "amazon":
            provider = "Amazon"
        else:
            provider = "Claude"  # Default to Claude for other providers
        body = {
            "message": message,
            "modelId": "us."+self.model,
            "provider": provider
        }

        resp = requests.post(LLM_PROXY_URL, json=body)
        if resp.status_code == 200:
            return resp.json()
        else:
            raise Exception(f"Error sending message to LLM proxy: {resp.status_code} - {resp.text}")
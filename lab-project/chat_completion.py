# load environment variables from the .env file
from dotenv import load_dotenv

load_dotenv()

def sample_chat_completions():
    import os

    try:
        endpoint = os.environ["MODEL_DEPLOYMENT"]
        key = os.environ["MODEL_KEY"]
    except KeyError:
        print("Missing environment variable 'MODEL_DEPLOYMENT' or 'MODEL_KEY'")
        print("Set them before running this sample.")
        exit()

    # [START chat_completions]
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.core.credentials import AzureKeyCredential

    client = ChatCompletionsClient(
        endpoint=endpoint, # Of the form https://<your-resouce-name>.openai.azure.com/openai/deployments/<your-deployment-name> (for OpenAI) or https://<your-resouce-name>.services.ai.azure.com/models (for Inference API) or https://<your-host-name>.<your-azure-region>.models.ai.azure.com (for Serverless API)
        credential=AzureKeyCredential(key),
        api_version="2024-05-01-preview" # "2025-01-01-preview"
    )

    """
    # For Serverless API or Managed Compute endpoints only:
    model_info = client.get_model_info()

    print(f"Model name: {model_info.model_name}")
    print(f"Model provider name: {model_info.model_provider_name}")
    print(f"Model type: {model_info.model_type}")
    """

    messages = [
        SystemMessage("You are a helpful assistant."),
        UserMessage("How many feet are in a mile?"),
    ]

    completion_params = {
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 1.0,
        "top_p": 1.0
    }

    if "MODEL_DEPLOYMENT_NAME" in os.environ:
        completion_params["model"] = os.environ["MODEL_DEPLOYMENT_NAME"]

    response = client.complete(**completion_params)

    print(response.choices[0].message.content)

    # for update in response:
    #    print(update.choices[0].delta.content or "", end="")

    print(f"\nToken usage: {response.usage}")
    # [END chat_completions]

if __name__ == "__main__":
    sample_chat_completions()
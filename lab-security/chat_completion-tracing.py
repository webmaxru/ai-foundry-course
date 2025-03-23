import os
from opentelemetry import trace

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, CompletionsFinishReason
from azure.core.credentials import AzureKeyCredential

from dotenv import load_dotenv
load_dotenv()

# [START trace_setting]
from azure.core.settings import settings

settings.tracing_implementation = "opentelemetry"
# [END trace_setting]

# Setup tracing to console
# Requires opentelemetry-sdk
span_exporter = ConsoleSpanExporter()
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
trace.set_tracer_provider(tracer_provider)

# [START trace_function]
from opentelemetry.trace import get_tracer

tracer = get_tracer(__name__)


# The tracer.start_as_current_span decorator will trace the function call and enable adding additional attributes
# to the span in the function implementation. Note that this will trace the function parameters and their values.
@tracer.start_as_current_span("get_temperature")  # type: ignore
def get_temperature(city: str) -> str:

    # Adding attributes to the current span
    span = trace.get_current_span()
    span.set_attribute("requested_city", city)

    if city == "Seattle":
        return "75"
    elif city == "New York City":
        return "80"
    else:
        return "Unavailable"


# [END trace_function]


def get_weather(city: str) -> str:
    if city == "Seattle":
        return "Nice weather"
    elif city == "New York City":
        return "Good weather"
    else:
        return "Unavailable"


def chat_completion_with_function_call(key, endpoint, model):
    import json
    from azure.ai.inference.models import (
        ToolMessage,
        AssistantMessage,
        ChatCompletionsToolCall,
        ChatCompletionsToolDefinition,
        FunctionDefinition,
    )

    weather_description = ChatCompletionsToolDefinition(
        function=FunctionDefinition(
            name="get_weather",
            description="Returns description of the weather in the specified city",
            parameters={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city for which weather info is requested",
                    },
                },
                "required": ["city"],
            },
        )
    )

    temperature_in_city = ChatCompletionsToolDefinition(
        function=FunctionDefinition(
            name="get_temperature",
            description="Returns the current temperature for the specified city",
            parameters={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city for which temperature info is requested",
                    },
                },
                "required": ["city"],
            },
        )
    )

    client = ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(key), model=model)
    messages = [
        SystemMessage("You are a helpful assistant."),
        UserMessage("What is the weather and temperature in Seattle?"),
    ]

    response = client.complete(messages=messages, tools=[weather_description, temperature_in_city])

    if response.choices[0].finish_reason == CompletionsFinishReason.TOOL_CALLS:
        # Append the previous model response to the chat history
        messages.append(AssistantMessage(tool_calls=response.choices[0].message.tool_calls))
        # The tool should be of type function call.
        if response.choices[0].message.tool_calls is not None and len(response.choices[0].message.tool_calls) > 0:
            for tool_call in response.choices[0].message.tool_calls:
                if type(tool_call) is ChatCompletionsToolCall:
                    function_args = json.loads(tool_call.function.arguments.replace("'", '"'))
                    print(f"Calling function `{tool_call.function.name}` with arguments {function_args}")
                    callable_func = globals()[tool_call.function.name]
                    function_response = callable_func(**function_args)
                    print(f"Function response = {function_response}")
                    # Provide the tool response to the model, by appending it to the chat history
                    messages.append(ToolMessage(function_response, tool_call_id=tool_call.id))
                    # With the additional tools information on hand, get another response from the model
            response = client.complete(messages=messages, tools=[weather_description, temperature_in_city])

    print(f"Model response = {response.choices[0].message.content}")


def main():

   
    # [START instrument_inferencing]
    from azure.ai.inference.tracing import AIInferenceInstrumentor

    # Instrument AI Inference API
    AIInferenceInstrumentor().instrument()
    # [END instrument_inferencing]

    try:
        endpoint = os.environ["AZURE_AI_CHAT_ENDPOINT"]
        key = os.environ["AZURE_AI_CHAT_KEY"]
        model = os.environ["AZURE_AI_CHAT_DEPLOYMENT"]
    except KeyError:
        print("Missing environment variable 'AZURE_AI_CHAT_ENDPOINT' or 'AZURE_AI_CHAT_KEY'")
        print("Set them before running this sample.")
        exit()

    chat_completion_with_function_call(key, endpoint, model)
    # [START uninstrument_inferencing]
    AIInferenceInstrumentor().uninstrument()
    # [END uninstrument_inferencing]


if __name__ == "__main__":
    main()
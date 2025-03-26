import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MessageRole, BingGroundingTool
from azure.identity import DefaultAzureCredential

from utils import enable_telemetry
from opentelemetry import trace
# enable_telemetry()

project = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.environ["AIPROJECT_CONNECTION_STRING"],
)

# [START create_agent_with_bing_grounding_tool]
bing_connection = project.connections.get(connection_name=os.environ["BING_CONNECTION_NAME"])
conn_id = bing_connection.id

print(conn_id)

# Initialize agent bing tool and add the connection id
bing = BingGroundingTool(connection_id=conn_id)

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span(name="agent_bing"):

    # Create agent with the bing tool and process assistant run
    with project:
        agent = project.agents.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            name="my-assistant",
            instructions="You are a helpful assistant",
            tools=bing.definitions,
            headers={"x-ms-enable-preview": "true"},
        )
        # [END create_agent_with_bing_grounding_tool]

        print(f"Created agent, ID: {agent.id}")

        # Create thread for communication
        thread = project.agents.create_thread()
        print(f"Created thread, ID: {thread.id}")

        # Create message to thread
        message = project.agents.create_message(
            thread_id=thread.id,
            role=MessageRole.USER,
            content="How does wikipedia explain Euler's Identity?",
        )
        print(f"Created message, ID: {message.id}")

        # Create and process agent run in thread with tools
        run = project.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
        print(f"Run finished with status: {run.status}")

        if run.status == "failed":
            print(f"Run failed: {run.last_error}")

        # Delete the assistant when done
        project.agents.delete_agent(agent.id)
        print("Deleted agent")

        # Print the Agent's response message with optional citation
        response_message = project.agents.list_messages(thread_id=thread.id).get_last_message_by_role(
            MessageRole.AGENT
        )
        if response_message:
            for text_message in response_message.text_messages:
                print(f"Agent response: {text_message.text.value}")
            for annotation in response_message.url_citation_annotations:
                print(f"URL Citation: [{annotation.url_citation.title}]({annotation.url_citation.url})")
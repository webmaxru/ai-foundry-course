import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AzureAISearchTool, ConnectionType
from dotenv import load_dotenv

load_dotenv()

model_name = os.environ["MODEL_DEPLOYMENT_NAME"]

try:
    project = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(
        ),
        conn_str=os.environ["AIPROJECT_CONNECTION_STRING"],
    )
    print("✅ Successfully initialized AIProjectClient1")
except Exception as e:
    print(f"❌ Error initializing project client: {e}")


search_conn_id = None
all_connections = project.connections.list()
for c in all_connections:
    if c.connection_type == ConnectionType.AZURE_AI_SEARCH:
        search_conn_id = c.id
        print(f"Found existing Azure AI Search connection: {search_conn_id}")
        break

if not search_conn_id:
    print("❌ No Azure AI Search connection found in your project.\n",
          "Please create one or ask your admin to do so.")


if search_conn_id:

    index_name = os.environ["AISEARCH_INDEX_NAME"]

    # Initialize the search tool with your index
    ai_search_tool = AzureAISearchTool(
        index_connection_id=search_conn_id,
        index_name=index_name,
    )

    agent = None

    agents = project.agents.list_agents()
    
    for a in agents.data:
        if a.name == "agent-travel": # Replace with search by id
            agent = a
            print(f"Found existing agent: {agent.id}")
            break
    
    if not agent:

        agent = project.agents.create_agent(
            model=model_name,
            name="agent-travel",
            instructions="""
            You are a travel planning agend working on behalf of the travel agency. You help users find travel details. Use Azure AI Search to find travel destinations and information about company.
            """,
            tools=ai_search_tool.definitions,
            tool_resources=ai_search_tool.resources,
            headers={"x-ms-enable-preview": "true"},
        )
        print(f"Created agent, ID: {agent.id}")


    # Create a thread
    thread = project.agents.create_thread()
    print(f"Created thread, thread ID: {thread.id}")

    # Create a message
    message = project.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="Which travel destinations are you specialized in?",
    )
    print(f"Created message, message ID: {message.id}")

    # Run the agent
    run = project.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
        # Check if you got "Rate limit is exceeded.", then you want to get more quota
        print(f"Run failed: {run.last_error}")

    # Fetch run steps to get the details of the agent run
    run_steps = project.agents.list_run_steps(thread_id=thread.id, run_id=run.id)
    for step in run_steps.data:
        print(f"Step {step['id']} status: {step['status']}")
        step_details = step.get("step_details", {})
        tool_calls = step_details.get("tool_calls", [])

        if tool_calls:
            print("  Tool calls:")
            for call in tool_calls:
                print(f"    Tool Call ID: {call.get('id')}")
                print(f"    Type: {call.get('type')}")

                azure_ai_search_details = call.get("azure_ai_search", {})
                if azure_ai_search_details:
                    print(f"    azure_ai_search input: {azure_ai_search_details.get('input')}")
                    print(f"    azure_ai_search output: {azure_ai_search_details.get('output')}")
        print()  # add an extra newline between steps

    # Delete the assistant when done
    project.agents.delete_agent(agent.id)
    print("Deleted agent")

    # Get messages from the thread
    messages = project.agents.list_messages(thread_id=thread.id)

    for m in reversed(messages.data):
        if m.role == "assistant" and m.content:
            print("\nAssistant says:")
            for c in m.content:
                if hasattr(c, "text"):
                    print(c.text.value)
            break
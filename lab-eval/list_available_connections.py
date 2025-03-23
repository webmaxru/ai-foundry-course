from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectionType
from azure.identity import DefaultAzureCredential
import os

from dotenv import load_dotenv
load_dotenv()

# Initialize client with connection string and credential
project = AIProjectClient.from_connection_string(
    conn_str=os.environ["AIPROJECT_CONNECTION_STRING"],
    credential=DefaultAzureCredential()
)

# List and display available models
# List the properties of all connections
connections = project.connections.list()
print(f"====> Listing of all connections (found {len(connections)}):")
for connection in connections:
    print(connection)

# List the properties of all connections of a particular "type" (in this sample, Azure OpenAI connections)
connections = project.connections.list(
    connection_type=ConnectionType.AZURE_OPEN_AI,
)
print(f"====> Listing of all Azure Open AI connections (found {len(connections)}):")
for connection in connections:
    print(connection)

# Get the properties of the default connection of a particular "type", with credentials
connection = project.connections.get_default(
    connection_type=ConnectionType.AZURE_AI_SERVICES,
    include_credentials=True,  # Optional. Defaults to "False"
)
print("====> Get default Azure AI Services connection:")
print(connection)

# List all connections and check for specific types
connections = project.connections.list()
search_conn_id = ""
openai_conn_id = ""

for conn in connections:
    conn_type = str(conn.connection_type).split('.')[-1]  # Get the part after the dot
    if conn_type == "AZURE_AI_SEARCH":
        search_conn_id = conn.id
    elif conn_type == "AZURE_OPEN_AI":
        openai_conn_id = conn.id

print(f"\n====> Connection IDs found:")
if not search_conn_id:
    print("Azure AI Search: Not found - Please create an Azure AI Search connection")
else:
    print(f"Azure AI Search: {search_conn_id}")
    
if not openai_conn_id:
    print("Azure OpenAI: Not found - Please create an Azure OpenAI connection") 
else:
    print(f"Azure OpenAI: {openai_conn_id}")
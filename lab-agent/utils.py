import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from dotenv import load_dotenv
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.ai.inference.tracing import AIInferenceInstrumentor

load_dotenv()

def enable_telemetry():

    AIInferenceInstrumentor().instrument()


    project = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=os.environ["AIPROJECT_CONNECTION_STRING"],
    )

    # Enable Azure Monitor tracing

    tracing_link = f"https://ai.azure.com/tracing?wsid=/subscriptions/{project.scope['subscription_id']}/resourceGroups/{project.scope['resource_group_name']}/providers/Microsoft.MachineLearningServices/workspaces/{project.scope['project_name']}"
    application_insights_connection_string = project.telemetry.get_connection_string()
    if not application_insights_connection_string:
        print(
            "No application insights configured, telemetry will not be logged to project. Add application insights at:"
        )
        print(tracing_link)
    else:
        configure_azure_monitor(connection_string=application_insights_connection_string)
        print("Enabled telemetry logging to project, view traces at:")
        print(tracing_link)

    # enable additional instrumentations
    project.telemetry.enable()
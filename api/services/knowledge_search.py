from google.cloud import discoveryengine_v1 as discoveryengine
import os, logging

PROJECT_ID = os.environ.get("PROJECT_ID", "project-3eab0e03-52db-4be0-a65")
LOCATION = "global"
DATA_STORE_ID = os.environ.get("DATA_STORE_ID", "telecom-kb_1776845649514")

def search_knowledge_base(query: str) -> str:
    """Search telecom knowledge base and return AI-generated answer"""
    try:
        client = discoveryengine.SearchServiceClient()
        serving_config = (
            f"projects/{PROJECT_ID}/locations/{LOCATION}/"
            f"collections/default_collection/dataStores/{DATA_STORE_ID}/"
            f"servingConfigs/default_config"
        )
        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=3,
            content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
                summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                    summary_result_count=3,
                    include_citations=True,
                    ignore_adversarial_query=True,
                )
            )
        )
        response = client.search(request)
        if response.summary and response.summary.summary_text:
            return response.summary.summary_text
        for result in response.results:
            doc = result.document.derived_struct_data
            snippets = doc.get("snippets", [])
            if snippets:
                return snippets[0].get("snippet", "")
        return "I couldn't find specific information about that in our knowledge base."
    except Exception as e:
        logging.error(f"knowledge_search_error: {e}")
        return "I'm having trouble accessing our knowledge base right now."

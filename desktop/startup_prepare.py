"""Prepare public list projections during an update, before the normal restart."""
import time
from paths import STATE
from persistence import save_document
from store import Store
from integrations import IntegrationService
from knowledge import KnowledgeAnalysisCache


def prepare():
    started=time.monotonic()
    # This projection only depends on the public catalog, integration metadata
    # and saved per-problem analysis. Personal services, account initialization
    # and HTTP listeners belong to the normal launch, after the updater exits.
    store=Store()
    extensions=IntegrationService(store,STATE,auto_start=False)
    store.extensions=extensions
    store.knowledge_analysis=KnowledgeAnalysisCache(STATE/'tb-knowledge-analysis.json')
    try:
        store.data_response_bytes(compact=True,compressed=True)
        save_document(STATE/'startup-preparation.json',{
            'schema':1,'publicCatalogReady':True,
            'catalogSignature':store.library.content_signature(),
            'seconds':round(time.monotonic()-started,3)})
    finally:
        extensions.close()

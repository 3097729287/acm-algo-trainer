"""Prepare public list projections during an update, before the normal restart."""
import time
from backend import start_server
from paths import STATE,ADMIN_MODE
from persistence import save_document


def prepare():
    started=time.monotonic()
    # Construct the same real services, without authentication restoration,
    # listeners, external sync jobs, remote mutations or a replacement UI.
    server=start_server(port=0,admin_mode=ADMIN_MODE,integration_auto_start=False)
    try:
        server.store.data_response_bytes(compact=True,compressed=True)
        save_document(STATE/'startup-preparation.json',{
            'schema':1,'publicCatalogReady':True,
            'catalogSignature':server.store.library.content_signature(),
            'seconds':round(time.monotonic()-started,3)})
    finally:
        server.server_close()

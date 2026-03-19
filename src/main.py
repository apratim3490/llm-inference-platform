"""
FastAPI Application Factory

Creates and configures the FastAPI app with:
- Lifespan events (startup/shutdown for shared resources)
- Route registration
- Middleware pipeline (added in later phases)
"""

# TODO: Phase 1 - Create async lifespan context manager
#   Hints:
#     - Use @asynccontextmanager from contextlib
#     - Before yield: create httpx.AsyncClient, store on app.state.http_client
#       - Configure with vLLM base_url and timeout from settings
#     - After yield: close the http_client with aclose()
#     - Think of it like opening/closing a restaurant
#
# TODO: Phase 1 - Create create_app() factory function
#   Hints:
#     - Create FastAPI instance with title, version, lifespan
#     - Conditionally enable /docs only in debug mode (security!)
#     - Include api_router from src.api.router
#     - Return the app
#     - This pattern makes testing easier (fresh app per test)

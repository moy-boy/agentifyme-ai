from collections.abc import Callable
from typing import Any

from grpc.aio import ClientCallDetails, UnaryUnaryClientInterceptor


class CustomInterceptor(UnaryUnaryClientInterceptor):
    def __init__(self, api_key: str, worker_id: str):
        self.api_key = api_key
        self.worker_id = worker_id

    async def intercept_unary_unary(
        self,
        continuation: Callable,
        client_call_details: ClientCallDetails,
        request: Any,
    ) -> Any:
        r_metadata = (("x-api-key", self.api_key), ("x-hash-id", self.worker_id))

        new_details = ClientCallDetails(
            method=client_call_details.method,
            timeout=client_call_details.timeout,
            metadata=r_metadata,
            credentials=client_call_details.credentials,
            wait_for_ready=client_call_details.wait_for_ready,
        )

        return await continuation(new_details, request)

import os
from abc import ABC, abstractmethod
from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel

from agentifyme.errors import AgentifyMeError
from agentifyme.utilities.json_utils import serialize_value


class AgentifymeError(Exception):
    """Base exception for Agentifyme client errors"""


class BaseClient(ABC):
    """Base client for the Agentifyme API with shared functionality"""

    api_key: str
    organization: str | None
    project: str | None
    endpoint_url: str | httpx.URL | None

    def __init__(
        self,
        endpoint_url: str | httpx.URL | None = None,
        api_key: str | None = None,
        organization: str | None = None,
        project: str | None = None,
        local_mode: bool | None = None,
        timeout: float = 300.0,
    ):
        """Initialize the base Agentifyme client

        Args:
            endpoint_url: Optional API endpoint override. Use http://localhost:PORT for local mode
            api_key: API key for authentication (not required for local mode)
            organization: Organization ID (not required for local mode)
            project: Optional project ID
            timeout: Timeout for API requests, defaults to 300 seconds (5 minutes)

        """
        # Set default endpoints
        DEFAULT_CLOUD_ENDPOINT = "https://run.agentifyme.ai"
        DEFAULT_LOCAL_ENDPOINT = "http://localhost:63419"

        # Set endpoint URL
        if endpoint_url is None:
            endpoint_url = os.getenv("AGENTIFYME_ENDPOINT_URL")
            # If no endpoint is specified, use appropriate default based on local_mode
            if endpoint_url is None:
                endpoint_url = DEFAULT_LOCAL_ENDPOINT if local_mode else DEFAULT_CLOUD_ENDPOINT

        self.endpoint_url = str(endpoint_url).rstrip("/")

        # Determine if we're in local mode
        self.is_local_mode = local_mode if local_mode is not None else self._is_local_endpoint(self.endpoint_url)

        # Handle API key
        if not self.is_local_mode:
            if api_key is None:
                api_key = os.getenv("AGENTIFYME_API_KEY")
            if api_key is None:
                raise AgentifymeError("API key is required for cloud endpoints. Please set the AGENTIFYME_API_KEY environment variable or pass it directly.")
            self.api_key = api_key

            # Handle organization
            if organization is None:
                organization = os.getenv("AGENTIFYME_ORG_ID")
            if organization is None:
                raise AgentifymeError("Organization is required for cloud endpoints. Please set the AGENTIFYME_ORG_ID environment variable or pass it directly.")
            self.organization = organization
        else:
            self.api_key = None
            self.organization = None

        self.project = project

        # Initialize HTTP client with appropriate headers
        self._http_client = self._create_http_client(timeout)

    def _is_local_endpoint(self, endpoint: str | httpx.URL) -> bool:
        """Check if the endpoint is a local endpoint

        Args:
            endpoint: Endpoint URL to check

        Returns:
            bool: True if endpoint is local, False otherwise

        """
        if isinstance(endpoint, httpx.URL):
            endpoint = str(endpoint)

        return endpoint.startswith("http://localhost") or endpoint.startswith("http://127.0.0.1") or endpoint.startswith("http://0.0.0.0")

    def _get_request_headers(self) -> dict:
        """Get headers for API requests based on mode

        Returns:
            dict: Headers to use for requests

        """
        headers = {"Content-Type": "application/json"}
        if not self.is_local_mode:
            headers["X-API-KEY"] = self.api_key
            if self.organization:
                headers["X-ORG-ID"] = self.organization
        return headers

    def _prepare_input(self, name: str, input_data: dict[str, Any] | BaseModel) -> dict:
        """Convert input data to dictionary format with proper serialization of datetime objects

        Args:
            name: Name of the input
            input_data: Input data either as dictionary or Pydantic model

        Returns:
            Dictionary with serialized values suitable for JSON serialization

        """
        data = {"name": name}

        if isinstance(input_data, BaseModel):
            # Pydantic models already handle datetime serialization in model_dump()
            data["parameters"] = input_data.model_dump()
        else:
            # For raw dictionaries, we need to handle serialization ourselves
            data["parameters"] = serialize_value(input_data)

        return data

    @abstractmethod
    def _create_http_client(self) -> httpx.Client | httpx.AsyncClient:
        """Create and return an HTTP client"""

    @abstractmethod
    def _handle_response(self, response: httpx.Response) -> dict | list | str | None:
        """Handle API response and errors"""


class Client(BaseClient):
    """Synchronous client for the Agentifyme API"""

    def _create_http_client(self, timeout: float) -> httpx.Client:
        """Create a synchronous HTTP client"""
        headers = self._get_request_headers()
        return httpx.Client(
            headers=headers,
            timeout=timeout,
        )

    def _handle_response(self, response: httpx.Response) -> dict | list | str | None:
        """Handle API response and errors"""
        try:
            response.raise_for_status()
            json_response = response.json()

            if "error" in json_response:
                error = dict(json_response["error"])
                raise AgentifyMeError(
                    message=error.get("message"),
                    error_code=error.get("errorCode"),
                    category=error.get("category"),
                    severity=error.get("severity"),
                    error_type=error.get("errorType"),
                    tb=error.get("traceback"),
                )

            if "data" not in json_response:
                raise AgentifyMeError(
                    message="No data returned from API",
                    error_code="NO_DATA_RETURNED",
                    category="API_ERROR",
                    severity="ERROR",
                    error_type=None,
                )

            return json_response["data"]
        except httpx.HTTPStatusError as e:
            error_msg = f"API request failed: {e!s}"
            response_data = None
            try:
                response_data = response.json()
                error_msg = response_data.get("message", error_msg)
            except Exception:
                pass
            raise AgentifyMeError(
                message=error_msg,
                error_code="API_ERROR",
                category="API_ERROR",
                severity="ERROR",
                error_type=None,
            )
        except Exception as e:
            raise AgentifyMeError(
                message=f"Unexpected error: {e!s}",
                error_code="UNEXPECTED_ERROR",
                category="API_ERROR",
                severity="ERROR",
                error_type=None,
            )

    def run_workflow(
        self,
        name: str,
        input: dict | BaseModel | None = None,
        deployment_endpoint: str | None = None,
        timeout: float = 300.0,
    ) -> dict | list | str | None:
        """Run a workflow

        Args:
            name: Workflow name
            input: Workflow input parameters as dict or Pydantic model
            deployment_endpoint: Workflow deployment endpoint identifier
            timeout: Timeout for API requests, defaults to 300 seconds (5 minutes)

        Returns:
            API response data

        """
        data = self._prepare_input(name, input)
        headers = {}
        if deployment_endpoint:
            headers["x-wf-endpoint"] = deployment_endpoint

        try:
            http_client = self._create_http_client(timeout)
            response = http_client.post(f"{self.endpoint_url}/api/workflows/run", json=data, headers=headers)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise AgentifymeError(f"Request failed: {e!s}")

    def submit_workflow(self, name: str, input: dict | BaseModel | None = None, deployment_endpoint: str | None = None) -> dict:
        """Submit a workflow

        Args:
            name: Workflow name
            input: Workflow input parameters as dict or Pydantic model
            deployment_endpoint: Workflow deployment endpoint identifier

        Returns:
            API response data including job ID

        """
        data = self._prepare_input(name, input)
        headers = {}
        if deployment_endpoint:
            headers["x-wf-endpoint"] = deployment_endpoint

        try:
            response = self._http_client.post(f"{self.endpoint_url}/api/workflows/jobs", json=data, headers=headers)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise AgentifymeError(f"Request failed: {e!s}")

    def get_workflow_result(self, job_id: str) -> dict | list | str | None:
        """Get the result of a workflow job"""
        response = self._http_client.get(f"{self.endpoint_url}/api/workflows/jobs/{job_id}")
        return self._handle_response(response)


class AsyncClient(BaseClient):
    """Async client for the Agentifyme API"""

    def _create_http_client(self, timeout: float) -> httpx.AsyncClient:
        """Create an async HTTP client"""
        headers = self._get_request_headers()
        return httpx.AsyncClient(
            headers=headers,
            timeout=timeout,
        )

    async def _handle_response(self, response: httpx.Response) -> dict | list | str | None:
        """Handle API response and errors"""
        try:
            response.raise_for_status()
            json_response = response.json()
            if "error" in json_response:
                error = dict(json_response["error"])
                raise AgentifyMeError(
                    message=error.get("message"),
                    error_code=error.get("errorCode"),
                    category=error.get("category"),
                    severity=error.get("severity"),
                    error_type=error.get("errorType"),
                    tb=error.get("traceback"),
                )

            if "data" not in json_response:
                raise AgentifyMeError(
                    message="No data returned from API",
                    error_code="NO_DATA_RETURNED",
                    category="API_ERROR",
                    severity="ERROR",
                    error_type=None,
                    tb=None,
                )

            return json_response["data"]
        except httpx.HTTPStatusError as e:
            error_msg = f"API request failed: {e!s}"
            response_data = None
            try:
                response_data = response.json()
                error_msg = response_data.get("message", error_msg)
            except Exception:
                pass
            raise AgentifyMeError(
                message=error_msg,
                error_code="API_ERROR",
                category="API_ERROR",
                severity="ERROR",
                error_type=None,
            )
        except AgentifyMeError:
            raise
        except Exception as e:
            raise AgentifyMeError(
                message=f"Unexpected error: {e!s}",
                error_code="UNEXPECTED_ERROR",
                category="API_ERROR",
                severity="ERROR",
                error_type=None,
            )

    async def run_workflow(
        self,
        name: str,
        input: dict | BaseModel | None = None,
        deployment_endpoint: str | None = None,
        timeout: float = 300.0,
    ) -> dict | list | str | None:
        """Run a workflow

        Args:
            name: Workflow name
            input: Workflow input parameters as dict or Pydantic model
            deployment_endpoint: Workflow deployment endpoint identifier

        Returns:
            API response data

        """
        data = self._prepare_input(name, input)
        headers = {}
        if deployment_endpoint:
            headers["x-wf-endpoint"] = deployment_endpoint

        try:
            async_http_client = self._create_http_client(timeout)
            async with async_http_client as client:
                response = await client.post(f"{self.endpoint_url}/api/workflows/run", json=data, headers=headers)
                return await self._handle_response(response)
        except httpx.RequestError as e:
            raise AgentifyMeError(
                message=f"Request failed: {e!s}",
                error_code="REQUEST_FAILED",
                category="API_ERROR",
                severity="ERROR",
                error_type=None,
            )

    async def submit_workflow(self, name: str, input: dict | BaseModel | None = None, deployment_endpoint: str | None = None) -> dict:
        """Submit a workflow

        Args:
            name: Workflow name
            input: Workflow input parameters as dict or Pydantic model
            deployment_endpoint: Workflow deployment endpoint identifier

        Returns:
            API response data including job ID

        """
        data = self._prepare_input(name, input)
        headers = {}
        if deployment_endpoint:
            headers["x-wf-endpoint"] = deployment_endpoint

        try:
            async with self._http_client as client:
                response = await client.post(f"{self.endpoint_url}/api/workflows/jobs", json=data, headers=headers)
                return await self._handle_response(response)
        except httpx.RequestError as e:
            raise AgentifyMeError(
                message=f"Request failed: {e!s}",
                error_code="REQUEST_FAILED",
                category="API_ERROR",
                severity="ERROR",
                error_type=None,
            )

    async def get_workflow_result(self, job_id: str) -> dict | list | str | None:
        """Get the result of a workflow job"""
        async with self._http_client as client:
            response = await client.get(f"{self.endpoint_url}/api/workflows/jobs/{job_id}")
            return await self._handle_response(response)

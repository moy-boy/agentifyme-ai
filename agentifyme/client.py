import os
from abc import ABC, abstractmethod
from typing import Optional, Union

import httpx
from pydantic import BaseModel


class AgentifymeError(Exception):
    """Base exception for Agentifyme client errors"""

    pass


class WorkflowExecutionError(AgentifymeError):
    """Exception raised for API errors"""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[dict] = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


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
    ):
        """
        Initialize the base Agentifyme client

        Args:
            endpoint_url: Optional API endpoint override. Use http://localhost:PORT for local mode
            api_key: API key for authentication (not required for local mode)
            organization: Organization ID (not required for local mode)
            project: Optional project ID
        """
        # Set default endpoints
        DEFAULT_CLOUD_ENDPOINT = "https://run.agentifyme.ai/v1/workflows"
        DEFAULT_LOCAL_ENDPOINT = "http://localhost:63419/v1/workflows"

        # Set endpoint URL
        if endpoint_url is None:
            endpoint_url = os.getenv("AGENTIFYME_ENDPOINT_URL")
            # If no endpoint is specified, use appropriate default based on local_mode
            if endpoint_url is None:
                endpoint_url = DEFAULT_LOCAL_ENDPOINT if local_mode else DEFAULT_CLOUD_ENDPOINT
        self.endpoint_url = endpoint_url

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
        self._http_client = self._create_http_client()

    def _is_local_endpoint(self, endpoint: str | httpx.URL) -> bool:
        """
        Check if the endpoint is a local endpoint

        Args:
            endpoint: Endpoint URL to check

        Returns:
            bool: True if endpoint is local, False otherwise
        """
        if isinstance(endpoint, httpx.URL):
            endpoint = str(endpoint)

        return endpoint.startswith("http://localhost") or endpoint.startswith("http://127.0.0.1") or endpoint.startswith("http://0.0.0.0")

    def _get_request_headers(self) -> dict:
        """
        Get headers for API requests based on mode

        Returns:
            dict: Headers to use for requests
        """
        headers = {"Content-Type": "application/json"}
        if not self.is_local_mode:
            headers["X-API-KEY"] = self.api_key
            if self.organization:
                headers["X-ORG-ID"] = self.organization
        return headers

    def _prepare_input(self, name: str, input_data: Union[dict, BaseModel]) -> dict:
        """Convert input data to dictionary format"""
        data = {"name": name}
        if isinstance(input_data, BaseModel):
            data["parameters"] = input_data.model_dump()
        else:
            data["parameters"] = input_data
        return data

    @abstractmethod
    def _create_http_client(self) -> Union[httpx.Client, httpx.AsyncClient]:
        """Create and return an HTTP client"""
        pass

    @abstractmethod
    def _handle_response(self, response: httpx.Response) -> Union[dict, list, str, None]:
        """Handle API response and errors"""
        pass


class Client(BaseClient):
    """Synchronous client for the Agentifyme API"""

    def _create_http_client(self) -> httpx.Client:
        """Create a synchronous HTTP client"""
        headers = self._get_request_headers()
        return httpx.Client(
            headers=headers,
            timeout=30.0,  # 30 second timeout
        )

    def _handle_response(self, response: httpx.Response) -> Union[dict, list, str, None]:
        """Handle API response and errors"""
        try:
            response.raise_for_status()
            json_response = response.json()

            if "data" not in json_response:
                raise WorkflowExecutionError(message="No data returned from API", status_code=response.status_code, response=json_response)

            return json_response["data"]
        except httpx.HTTPStatusError as e:
            error_msg = f"API request failed: {str(e)}"
            response_data = None
            try:
                response_data = response.json()
                error_msg = response_data.get("message", error_msg)
            except Exception:
                pass
            raise WorkflowExecutionError(message=error_msg, status_code=response.status_code, response=response_data)
        except Exception as e:
            raise AgentifymeError(f"Unexpected error: {str(e)}")

    def run_workflow(self, name: str, input: Union[dict, BaseModel] | None = None, deployment_endpoint: str | None = None) -> Union[dict, list, str, None]:
        """
        Run a workflow synchronously

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
            response = self._http_client.post(f"{self.endpoint_url}/run", json=data, headers=headers)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise AgentifymeError(f"Request failed: {str(e)}")

    def submit_workflow(self, name: str, input: Union[dict, BaseModel] | None = None, deployment_endpoint: str | None = None) -> dict:
        """
        Submit a workflow asynchronously

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
            response = self._http_client.post(f"{self.endpoint_url}/jobs", json=data, headers=headers)
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise AgentifymeError(f"Request failed: {str(e)}")

    def get_workflow_result(self, job_id: str) -> Union[dict, list, str, None]:
        """
        Get the result of a workflow job
        """
        response = self._http_client.get(f"{self.endpoint_url}/jobs/{job_id}")
        return self._handle_response(response)


class AsyncClient(BaseClient):
    """Async client for the Agentifyme API"""

    def _create_http_client(self) -> httpx.AsyncClient:
        """Create an async HTTP client"""
        headers = self._get_request_headers()
        return httpx.AsyncClient(
            headers=headers,
            timeout=30.0,  # 30 second timeout
        )

    async def _handle_response(self, response: httpx.Response) -> Union[dict, list, str, None]:
        """Handle API response and errors"""
        try:
            response.raise_for_status()
            json_response = response.json()

            if "data" not in json_response:
                raise WorkflowExecutionError(message="No data returned from API", status_code=response.status_code, response=json_response)

            return json_response["data"]
        except httpx.HTTPStatusError as e:
            error_msg = f"API request failed: {str(e)}"
            response_data = None
            try:
                response_data = response.json()
                error_msg = response_data.get("message", error_msg)
            except Exception:
                pass
            raise WorkflowExecutionError(message=error_msg, status_code=response.status_code, response=response_data)
        except Exception as e:
            raise AgentifymeError(f"Unexpected error: {str(e)}")

    async def run_workflow(self, name: str, input: Union[dict, BaseModel] | None = None, deployment_endpoint: str | None = None) -> Union[dict, list, str, None]:
        """
        Run a workflow synchronously

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
            async with self._http_client as client:
                response = await client.post(f"{self.endpoint_url}/run", json=data, headers=headers)
                return await self._handle_response(response)
        except httpx.RequestError as e:
            raise AgentifymeError(f"Request failed: {str(e)}")

    async def submit_workflow(self, name: str, input: Union[dict, BaseModel] | None = None, deployment_endpoint: str | None = None) -> dict:
        """
        Submit a workflow asynchronously

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
                response = await client.post(f"{self.endpoint_url}/jobs", json=data, headers=headers)
                return await self._handle_response(response)
        except httpx.RequestError as e:
            raise AgentifymeError(f"Request failed: {str(e)}")

    async def get_workflow_result(self, job_id: str) -> Union[dict, list, str, None]:
        """
        Get the result of a workflow job
        """
        async with self._http_client as client:
            response = await client.get(f"{self.endpoint_url}/jobs/{job_id}")
            return await self._handle_response(response)

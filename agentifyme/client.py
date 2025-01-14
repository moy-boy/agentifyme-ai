import os
from typing import Optional, Union

import httpx
from pydantic import BaseModel


class AgentifymeError(Exception):
    """Base exception for Agentifyme client errors"""

    pass


class AgentifymeAPIError(AgentifymeError):
    """Exception raised for API errors"""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[dict] = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class Client:
    """Client for the Agentifyme API"""

    def __init__(self, api_key: str, endpoint: Optional[str] = None):
        """
        Initialize the Agentifyme client

        Args:
            api_key: API key for authentication
            endpoint: Optional API endpoint override
        """
        self.api_key = api_key or os.getenv("AGENTIFYME_API_KEY")

        if not self.api_key:
            raise AgentifymeError("API key is required. Please set the AGENTIFYME_API_KEY environment variable or pass it directly.")

        self._api_endpoint = endpoint or os.getenv("AGENTIFYME_API_ENDPOINT", "https://run.agentifyme.ai/v1/workflows")

        # Initialize HTTP client with default headers
        self._http_client = httpx.Client(
            headers={"Content-Type": "application/json", "X-API-KEY": self.api_key},
            timeout=30.0,  # 30 second timeout
        )

    def _prepare_input(self, input_data: Union[dict, BaseModel]) -> dict:
        """Convert input data to dictionary format"""
        if isinstance(input_data, BaseModel):
            return input_data.model_dump()
        return input_data

    async def _handle_response(self, response: httpx.Response) -> Union[dict, list, str, None]:
        """Handle API response and errors"""
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_msg = f"API request failed: {str(e)}"
            try:
                error_data = response.json()
                error_msg = error_data.get("message", error_msg)
            except Exception:
                pass
            raise AgentifymeAPIError(message=error_msg, status_code=response.status_code, response=response.json() if response.text else None)
        except Exception as e:
            raise AgentifymeError(f"Unexpected error: {str(e)}")

    async def run_workflow(self, input: Union[dict, BaseModel], deployment_endpoint: str) -> Union[dict, list, str, None]:
        """
        Run a workflow synchronously

        Args:
            input: Workflow input parameters as dict or Pydantic model
            deployment_endpoint: Workflow deployment endpoint identifier

        Returns:
            API response data
        """
        data = self._prepare_input(input)
        headers = {"x-wf-endpoint": deployment_endpoint}

        try:
            response = await self._http_client.post(f"{self._api_endpoint}/run", json=data, headers=headers)
            return await self._handle_response(response)
        except httpx.RequestError as e:
            raise AgentifymeError(f"Request failed: {str(e)}")

    async def submit_workflow(self, input: Union[dict, BaseModel], deployment_endpoint: str) -> dict:
        """
        Submit a workflow asynchronously

        Args:
            input: Workflow input parameters as dict or Pydantic model
            deployment_endpoint: Workflow deployment endpoint identifier

        Returns:
            API response data including job ID
        """
        data = self._prepare_input(input)
        headers = {"x-wf-endpoint": deployment_endpoint}

        try:
            response = await self._http_client.post(f"{self._api_endpoint}/jobs", json=data, headers=headers)
            return await self._handle_response(response)
        except httpx.RequestError as e:
            raise AgentifymeError(f"Request failed: {str(e)}")

    async def get_workflow_status(self, workflow_id: str) -> Union[dict, list, str, None]:
        """
        Get the status of a workflow job

        Args:
            workflow_id: ID of the workflow job to check

        Returns:
            Job status information
        """
        try:
            response = await self._http_client.get(f"{self._api_endpoint}/jobs/{workflow_id}")
            return await self._handle_response(response)
        except httpx.RequestError as e:
            raise AgentifymeError(f"Request failed: {str(e)}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_client.aclose()

    def __enter__(self):
        raise TypeError("Use 'async with' instead")

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise TypeError("Use 'async with' instead")

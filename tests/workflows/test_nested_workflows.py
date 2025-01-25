# import asyncio
# import traceback

# import pytest
# from pydantic import BaseModel

# from agentifyme import get_logger, task, workflow
# from agentifyme.workflows import (
#     WorkflowConfig,
#     WorkflowExecutionError,
# )

# logger = get_logger()


# class CustomerQuery(BaseModel):
#     customer_id: str
#     query: str


# class CustomerInfo(BaseModel):
#     customer_id: str
#     name: str
#     email: str


# class QueryCategory(BaseModel):
#     category: str
#     confidence: float


# class Response(BaseModel):
#     message: str


# @task
# def get_customer_name(customer_id: str) -> str:
#     logger.info(f"Retrieving customer name for customer_id: {customer_id}")
#     return "John Doe"


# @task
# async def get_customer_name_async(customer_id: str) -> str:
#     logger.info(f"Retrieving customer name asynchronously for customer_id: {customer_id}")
#     await asyncio.sleep(0.1)
#     return "John Doe"


# @workflow(name="get_customer_info", description="Retrieve customer information")
# def get_customer_info(customer_id: str) -> CustomerInfo:
#     customer_name = get_customer_name(customer_id)
#     return CustomerInfo(customer_id=customer_id, name=customer_name, email="john@example.com")


# @workflow(
#     name="get_customer_info_async",
#     description="Retrieve customer information asynchronously",
# )
# async def get_customer_info_async(customer_id: str) -> CustomerInfo:
#     customer_name = await get_customer_name_async(customer_id)
#     return CustomerInfo(customer_id=customer_id, name=customer_name, email="john@example.com")


# @workflow(name="categorize_query", description="Categorize customer query")
# def categorize_query(query: str) -> QueryCategory:
#     return QueryCategory(category="billing", confidence=0.8)


# @workflow(
#     name="categorize_query_async",
#     description="Categorize customer query asynchronously",
# )
# async def categorize_query_async(query: str) -> QueryCategory:
#     await asyncio.sleep(0.1)
#     return QueryCategory(category="billing", confidence=0.8)


# @workflow(
#     name="handle_customer_query",
#     description="Handle customer query using nested workflows",
# )
# def handle_customer_query(customer_query: CustomerQuery) -> Response:
#     try:
#         customer_info = get_customer_info(customer_query.customer_id)
#         query_category = categorize_query(customer_query.query)

#         response_message = f"Hello {customer_info.name}, we've received your {query_category.category} query and will respond shortly."
#         return Response(message=response_message)
#     except Exception:
#         logger.error(traceback.format_exc())
#         raise


# @workflow(
#     name="handle_customer_query_async",
#     description="Handle customer query using nested async workflows",
# )
# async def handle_customer_query_async(customer_query: CustomerQuery) -> Response:
#     try:
#         customer_info = await get_customer_info_async(customer_query.customer_id)
#         query_category = await categorize_query_async(customer_query.query)

#         response_message = f"Hello {customer_info.name}, we've received your {query_category.category} query and will respond shortly."
#         return Response(message=response_message)
#     except Exception:
#         logger.error(traceback.format_exc())
#         raise


# # def test_nested_workflow():
# #     workflow = WorkflowConfig.get("handle_customer_query")
# #     input_data = {
# #         "customer_query": CustomerQuery(
# #             customer_id="12345",
# #             query="I have a question about my recent bill.",
# #         )
# #     }
# #     result = workflow(**input_data)

# #     assert isinstance(result, Response)
# #     assert "Hello John Doe" in result.message
# #     assert "billing query" in result.message


# # @pytest.mark.asyncio
# # async def test_nested_workflow_async():
# #     workflow = WorkflowConfig.get("handle_customer_query_async")
# #     input_data = {
# #         "customer_query": CustomerQuery(
# #             customer_id="12345",
# #             query="I have a question about my recent bill.",
# #         )
# #     }
# #     result = await workflow.arun(**input_data)

# #     assert isinstance(result, Response)
# #     assert "Hello John Doe" in result.message
# #     assert "billing query" in result.message


# # def test_nested_workflow_invalid_input():
# #     workflow = WorkflowConfig.get("handle_customer_query")
# #     with pytest.raises(WorkflowExecutionError):
# #         workflow.run(invalid_param="Some value")


# # @pytest.mark.asyncio
# # async def test_nested_workflow_invalid_input_async():
# #     workflow = WorkflowConfig.get("handle_customer_query_async")
# #     # with pytest.raises(AsyncWorkflowExecutionError):
# #     #     await workflow.arun(invalid_param="Some value")


# # def test_nested_workflow_missing_input():
# #     workflow = WorkflowConfig.get("handle_customer_query")
# #     with pytest.raises(WorkflowExecutionError):
# #         workflow.run()


# # @pytest.mark.asyncio
# # async def test_nested_workflow_missing_input_async():
# #     workflow = WorkflowConfig.get("handle_customer_query_async")
# #     # with pytest.raises(AsyncWorkflowExecutionError):
# #     #     await workflow.arun()


# # def test_individual_workflows():
# #     customer_info_workflow = WorkflowConfig.get("get_customer_info")
# #     categorize_query_workflow = WorkflowConfig.get("categorize_query")

# #     customer_info_result = customer_info_workflow(customer_id="12345")
# #     assert isinstance(customer_info_result, CustomerInfo)
# #     assert customer_info_result.name == "John Doe"

# #     categorize_query_result = categorize_query_workflow.run(query="I have a billing question")
# #     assert isinstance(categorize_query_result, QueryCategory)
# #     assert categorize_query_result.category == "billing"


# # @pytest.mark.asyncio
# # async def test_individual_workflows_async():
# #     customer_info_workflow = WorkflowConfig.get("get_customer_info_async")
# #     categorize_query_workflow = WorkflowConfig.get("categorize_query_async")

# #     customer_info_result = await customer_info_workflow.arun(customer_id="12345")
# #     assert isinstance(customer_info_result, CustomerInfo)
# #     assert customer_info_result.name == "John Doe"

# #     categorize_query_result = await categorize_query_workflow.arun(query="I have a billing question")
# #     assert isinstance(categorize_query_result, QueryCategory)
# #     assert categorize_query_result.category == "billing"

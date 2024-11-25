import asyncio
from typing import TypeVar

import orjson
from grpc.aio import Channel, StreamStreamCall
from loguru import logger
from pydantic import BaseModel, ValidationError

import agentifyme.worker.pb.api.v1.common_pb2 as common_pb
import agentifyme.worker.pb.api.v1.gateway_pb2 as pb
from agentifyme.worker.helpers import convert_workflow_to_pb, struct_to_dict
from agentifyme.workflows import Workflow, WorkflowConfig

Input = TypeVar("Input")
Output = TypeVar("Output")


class WorkflowHandler:
    def __init__(self, workflow: Workflow):
        self.workflow = workflow

    async def __call__(self, input_data: dict) -> dict:
        """Handle workflow execution with serialization/deserialization"""

        try:
            # Deserialize input based on input type
            # if issubclass(self.input_type, BaseModel):
            #     parsed_input = self.input_type.model_validate(input_data)
            # elif issubclass(self.input_type, dict):
            #     parsed_input = input_data
            # else:
            #     raise ValueError(f"Unsupported input type: {type(self.input_type)}")

            parsed_input = input_data

            # Execute workflow
            result = await self.workflow.arun(**parsed_input)

            # Serialize output
            output_data = result
            if isinstance(result, BaseModel):
                output_data = result.model_dump()
            # elif issubclass(self.output_type, dict):
            #     output_data = self.output_type(**result)
            # else:
            #     raise ValueError(f"Unsupported output type: {type(self.output_type)}")

            return output_data

        except ValidationError as e:
            raise ValueError(f"Invalid input data for {self.workflow.name}: {str(e)}")

        except Exception as e:
            raise RuntimeError(f"Error executing workflow: {str(e)}")


class WorkflowCommandHandler:
    """Handle workflow commands"""

    workflow_handlers: dict[str, WorkflowHandler] = {}

    def __init__(self, stream: StreamStreamCall, max_concurrent_jobs: int = 20):
        self.stream = stream
        self._current_jobs = 0
        self._max_concurrent_jobs = max_concurrent_jobs
        self._job_semaphore = asyncio.Semaphore(self._max_concurrent_jobs)
        for workflow_name in WorkflowConfig.get_all():
            _workflow = WorkflowConfig.get(workflow_name)
            _workflow_handler = WorkflowHandler(_workflow)
            self.workflow_handlers[workflow_name] = _workflow_handler

    async def run_workflow(self, payload: pb.RunWorkflowCommand) -> dict | None:
        try:
            async with self._job_semaphore:
                self._current_jobs += 1

                workflow_name = payload.workflow_name
                workflow_parameters = struct_to_dict(payload.parameters)

                logger.info(
                    f"Running workflow {workflow_name} with parameters {workflow_parameters}"
                )

                if workflow_name not in self.workflow_handlers:
                    raise ValueError(f"Workflow {workflow_name} not found")

                workflow_handler = self.workflow_handlers[workflow_name]
                result = await workflow_handler(workflow_parameters)

                return result
        except Exception as e:
            raise RuntimeError(f"Error running workflow: {str(e)}")
        finally:
            self._current_jobs -= 1
            logger.info(f"Finished job. Current concurrent jobs: {self._current_jobs}")

    async def pause_workflow(self, payload: pb.PauseWorkflowCommand) -> str:
        pass

    async def resume_workflow(self, payload: pb.ResumeWorkflowCommand) -> str:
        pass

    async def cancel_workflow(self, payload: pb.CancelWorkflowCommand) -> str:
        pass

    async def list_workflows(self) -> common_pb.ListWorkflowsResponse:
        pb_workflows: list[common_pb.WorkflowConfig] = []
        for workflow_name in WorkflowConfig.get_all():
            workflow = WorkflowConfig.get(workflow_name)
            workflow_config = workflow.config
            if isinstance(workflow_config, WorkflowConfig):
                _input_parameters = {}
                for (
                    input_parameter_name,
                    input_parameter,
                ) in workflow_config.input_parameters.items():
                    _input_parameters[input_parameter_name] = (
                        input_parameter.model_dump()
                    )

                _output_parameters = {}
                for idx, output_parameter in enumerate(
                    workflow_config.output_parameters
                ):
                    _output_parameters[f"output_{idx}"] = output_parameter.model_dump()

                pb_workflow = common_pb.WorkflowConfig(
                    name=workflow_config.name,
                    slug=workflow_config.slug,
                    description=workflow_config.description,
                    input_parameters=_input_parameters,
                    output_parameters=_output_parameters,
                    schedule=common_pb.Schedule(
                        cron_expression=workflow_config.normalize_schedule(
                            workflow_config.schedule
                        ),
                    ),
                )
                pb_workflows.append(pb_workflow)

        return common_pb.ListWorkflowsResponse(workflows=pb_workflows)

    async def __call__(self, command: pb.WorkflowCommand) -> dict | None:
        """Handle workflow command"""
        match command.type:
            case pb.WORKFLOW_COMMAND_TYPE_RUN:
                return await self.run_workflow(command.run_workflow)
            case pb.WORKFLOW_COMMAND_TYPE_PAUSE:
                return await self.pause_workflow(command.pause_workflow)
            case pb.WORKFLOW_COMMAND_TYPE_RESUME:
                return await self.resume_workflow(command.resume_workflow)
            case pb.WORKFLOW_COMMAND_TYPE_CANCEL:
                return await self.cancel_workflow(command.cancel_workflow)
            case pb.WORKFLOW_COMMAND_TYPE_LIST:
                return await self.list_workflows()
            case _:
                raise ValueError(f"Unsupported workflow command type: {command.type}")

from typing import TypeVar

from pydantic import BaseModel, ValidationError

from agentifyme.workflows import Workflow

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
            result = await self.workflow.arun(parsed_input)

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

from typing import Dict, List

from pydantic import BaseModel

from agentifyme.utilities.func_utils import (
    get_function_metadata,
)


class SimpleInput(BaseModel):
    name: str
    age: int


class SimpleOutput(BaseModel):
    message: str
    success: bool


class NestedInput(BaseModel):
    user: SimpleInput
    tags: List[str]


class NestedOutput(BaseModel):
    data: SimpleOutput
    metadata: Dict[str, str]


def test_pydantic_simple_input():
    def process_user(user: SimpleInput) -> str:
        """
        Process a user.

        Args:
            user (SimpleInput): The user to process.

        Returns:
            str: A greeting message.
        """
        return f"Hello, {user.name}!"

    metadata = get_function_metadata(process_user)

    assert len(metadata.input_parameters) == 1
    assert "user" in metadata.input_parameters

    user_param = metadata.input_parameters["user"]
    assert user_param.data_type == "object"
    assert user_param.description == "The user to process."
    assert user_param.required == True

    assert len(user_param.nested_fields) == 2
    assert "name" in user_param.nested_fields
    assert "age" in user_param.nested_fields

    name_param = user_param.nested_fields["name"]
    assert name_param.data_type == "string"
    assert name_param.description == ""  # Explicitly check that the description is empty
    assert name_param.required == True

    age_param = user_param.nested_fields["age"]
    assert age_param.data_type == "number"
    assert age_param.description == ""  # Explicitly check that the description is empty
    assert age_param.required == True

    assert metadata.output_parameters[0].data_type == "string"


def test_pydantic_simple_output():
    def create_simple_output(name: str, age: int) -> SimpleOutput:
        """
        Create a simple output.

        Args:
            name (str): The name of the user.
            age (int): The age of the user.

        Returns:
            SimpleOutput: A simple output object containing user information.
        """
        return SimpleOutput(message=f"User: {name}, Age: {age}", success=True)

    metadata = get_function_metadata(create_simple_output)

    # Check input parameters
    assert len(metadata.input_parameters) == 2
    assert metadata.input_parameters["name"].data_type == "string"
    assert metadata.input_parameters["name"].description == "The name of the user."
    assert metadata.input_parameters["age"].data_type == "number"
    assert metadata.input_parameters["age"].description == "The age of the user."

    # Check output parameter
    assert len(metadata.output_parameters) == 1
    output_param = metadata.output_parameters[0]
    assert output_param.data_type == "object"
    assert output_param.description == "A simple output object containing user information."

    # Check nested fields of the output
    assert len(output_param.nested_fields) == 2
    assert "message" in output_param.nested_fields
    assert "success" in output_param.nested_fields

    message_param = output_param.nested_fields["message"]
    assert message_param.data_type == "string"
    assert message_param.description == ""  # Empty as we don't extract nested field descriptions

    success_param = output_param.nested_fields["success"]
    assert success_param.data_type == "boolean"
    assert success_param.description == ""  # Empty as we don't extract nested field descriptions


def test_pydantic_nested_input():
    def process_nested_input(data: NestedInput) -> str:
        """
        Process nested input.

        Args:
            data (NestedInput): The nested data to process.

        Returns:
            str: A processed message.
        """
        return f"Processed {data.user.name} with {len(data.tags)} tags"

    metadata = get_function_metadata(process_nested_input)

    assert len(metadata.input_parameters) == 1
    data_param = metadata.input_parameters["data"]
    assert data_param.data_type == "object"
    assert data_param.description == "The nested data to process."
    assert data_param.required == True

    assert len(data_param.nested_fields) == 2
    assert "user" in data_param.nested_fields
    assert "tags" in data_param.nested_fields

    user_param = data_param.nested_fields["user"]
    assert user_param.data_type == "object"
    assert user_param.description == ""
    assert len(user_param.nested_fields) == 2
    assert "name" in user_param.nested_fields
    assert "age" in user_param.nested_fields
    assert user_param.nested_fields["name"].data_type == "string"
    assert user_param.nested_fields["name"].description == ""
    assert user_param.nested_fields["age"].data_type == "number"
    assert user_param.nested_fields["age"].description == ""

    tags_param = data_param.nested_fields["tags"]
    assert tags_param.data_type == "array"
    assert tags_param.description == ""

    assert metadata.output_parameters[0].data_type == "string"


def test_pydantic_nested_output():
    def create_nested_response(name: str, tags: List[str]) -> NestedOutput:
        """
        Create a nested response.

        Args:
            name (str): The name to include in the response.
            tags (List[str]): The tags to include in the response.

        Returns:
            NestedOutput: The created nested response.
        """
        return NestedOutput(
            data=SimpleOutput(message=f"Hello, {name}!", success=True),
            metadata={"tags": ",".join(tags)},
        )

    metadata = get_function_metadata(create_nested_response)

    assert len(metadata.input_parameters) == 2
    assert metadata.input_parameters["name"].data_type == "string"
    assert metadata.input_parameters["name"].description == "The name to include in the response."
    assert metadata.input_parameters["tags"].data_type == "array"
    assert metadata.input_parameters["tags"].description == "The tags to include in the response."

    assert len(metadata.output_parameters) == 1
    output_param = metadata.output_parameters[0]
    assert output_param.data_type == "object"
    assert output_param.description == "The created nested response."

    assert len(output_param.nested_fields) == 2
    assert "data" in output_param.nested_fields
    assert "metadata" in output_param.nested_fields

    data_param = output_param.nested_fields["data"]
    assert data_param.data_type == "object"
    assert data_param.description == ""
    assert len(data_param.nested_fields) == 2
    assert "message" in data_param.nested_fields
    assert "success" in data_param.nested_fields
    assert data_param.nested_fields["message"].data_type == "string"
    assert data_param.nested_fields["message"].description == ""
    assert data_param.nested_fields["success"].data_type == "boolean"
    assert data_param.nested_fields["success"].description == ""

    metadata_param = output_param.nested_fields["metadata"]
    assert metadata_param.data_type == "object"
    assert metadata_param.description == ""

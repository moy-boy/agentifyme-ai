from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from agentifyme.utilities.func_utils import (
    get_function_metadata,
)


class UserProfile(BaseModel):
    name: str
    age: int


class ComplexInput(BaseModel):
    user: UserProfile
    tags: List[str]


class ComplexOutput(BaseModel):
    message: str
    status: bool
    details: Optional[Dict[str, Any]]


def test_multiple_args_simple_output():
    def process_user_data(profile: UserProfile, include_details: bool = False) -> str:
        """
        Process user data and return a formatted string.

        Args:
            profile (UserProfile): The user's profile information.
            include_details (bool, optional): Whether to include additional details. Defaults to False.

        Returns:
            str: A formatted string with user information.
        """
        return f"Processed: {profile.name}, {profile.age} years old"

    metadata = get_function_metadata(process_user_data)

    assert len(metadata.input_parameters) == 2
    assert metadata.input_parameters["profile"].data_type == "object"
    assert metadata.input_parameters["profile"].nested_fields["name"].data_type == "string"
    assert metadata.input_parameters["profile"].nested_fields["age"].data_type == "number"
    assert metadata.input_parameters["include_details"].data_type == "boolean"
    assert metadata.input_parameters["include_details"].default_value == False
    assert metadata.output_parameters[0].data_type == "string"


def test_multiple_args_complex_input_output():
    def advanced_process(data: ComplexInput, multiply_age: int, flag: bool = True) -> ComplexOutput:
        """
        Perform advanced processing on complex input data.

        Args:
            data (ComplexInput): The complex input data containing user profile and tags.
            multiply_age (int): Factor to multiply the user's age by.
            flag (bool, optional): A flag to control processing. Defaults to True.

        Returns:
            ComplexOutput: A complex output object with processed information.
        """
        return ComplexOutput(
            message=f"Processed {data.user.name}",
            status=flag,
            details={"age": data.user.age * multiply_age, "tags": data.tags},
        )

    metadata = get_function_metadata(advanced_process)

    assert len(metadata.input_parameters) == 3

    # Check 'data' parameter
    data_param = metadata.input_parameters["data"]
    assert data_param.data_type == "object"
    assert "user" in data_param.nested_fields
    assert "tags" in data_param.nested_fields
    assert data_param.nested_fields["user"].nested_fields["name"].data_type == "string"
    assert data_param.nested_fields["user"].nested_fields["age"].data_type == "number"
    assert data_param.nested_fields["tags"].data_type == "array"

    # Check other parameters
    assert metadata.input_parameters["multiply_age"].data_type == "number"
    assert metadata.input_parameters["flag"].data_type == "boolean"
    assert metadata.input_parameters["flag"].default_value == True

    # Check output
    assert len(metadata.output_parameters) == 1
    output_param = metadata.output_parameters[0]
    assert output_param.data_type == "object"
    assert "message" in output_param.nested_fields
    assert "status" in output_param.nested_fields
    assert "details" in output_param.nested_fields
    assert output_param.nested_fields["message"].data_type == "string"
    assert output_param.nested_fields["status"].data_type == "boolean"
    assert output_param.nested_fields["details"].data_type == "object"


def test_list_and_dict_arguments():
    def process_collection(items: List[str], options: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Process a collection of items based on given options.

        Args:
            items (List[str]): A list of items to process.
            options (Dict[str, Any]): Processing options.
            limit (Optional[int], optional): Maximum number of items to process. Defaults to None.

        Returns:
            List[Dict[str, Any]]: A list of processed items.
        """
        return [{"item": item, "processed": True} for item in items[:limit]]

    metadata = get_function_metadata(process_collection)

    assert len(metadata.input_parameters) == 3
    assert metadata.input_parameters["items"].data_type == "array"
    assert metadata.input_parameters["options"].data_type == "object"
    assert metadata.input_parameters["limit"].data_type == "number"
    assert metadata.input_parameters["limit"].default_value == None

    assert len(metadata.output_parameters) == 1
    assert metadata.output_parameters[0].data_type == "array"

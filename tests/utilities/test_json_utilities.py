import pytest

from agentifyme.utilities.json_utils import extract_json


@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        # Test case 1: Valid JSON in Markdown code block
        ("```json\n{'category':'junk'}\n```", {"category": "junk"}),
        # Test case 2: Valid JSON without Markdown code block
        ('{"name": "John", "age": 30}', {"name": "John", "age": 30}),
        # Test case 3: Valid JSON with extra whitespace
        ('  \n  {"status": "success"}  \n  ', {"status": "success"}),
        # Test case 4: Multiple JSON objects (should return the first one)
        ('{"first": 1} {"second": 2}', {"first": 1}),
        # Test case 5: JSON in Markdown code block without language specifier
        ("```\n{'simple': true}\n```", {"simple": True}),
        # Test case 6: Empty object
        ("{}", {}),
        # Test case 7: Nested JSON
        ('{"outer": {"inner": "value"}}', {"outer": {"inner": "value"}}),
        # Test case 8: JSON with array
        ('{"numbers": [1, 2, 3]}', {"numbers": [1, 2, 3]}),
        # Test case 9: No JSON in the string
        ("This is just a plain text", None),
        # Test case 10: Invalid JSON
        ('{"invalid": "json"', None),
        # Test case 11: JSON with special characters
        ('{"special": "\\u00A9 2023"}', {"special": "© 2023"}),
        # # Test case 12: JSON in Markdown code block with language and extra newlines
        ("```json\n\n{'extra': 'newlines'}\n\n```", {"extra": "newlines"}),
        # Test case 13: Single-quoted JSON with boolean values
        ("{'bool': true, 'other': false}", {"bool": True, "other": False}),
        # Test case 14: JSON with escaped single quotes
        (
            '{\n  "category": "Informative",\n  "score": 70,\n  "explanation": "The email provides updates on rental listings that match the recipient\'s saved search criteria. While it contains useful information about new rental options, it does not require any immediate action from the recipient, hence classified as informative. The score reflects the relevance of the content to the recipient\'s interests."\n}',
            {
                "category": "Informative",
                "score": 70,
                "explanation": "The email provides updates on rental listings that match the recipient's saved search criteria. While it contains useful information about new rental options, it does not require any immediate action from the recipient, hence classified as informative. The score reflects the relevance of the content to the recipient's interests.",
            },
        ),
        # Test case 15: Mixed quotes and escaped characters
        (
            '{\'key1\': "value1", "key2": \'value2\', \'key3\': "value\\"3"}',
            {"key1": "value1", "key2": "value2", "key3": 'value"3'},
        ),
        # Test case 16: Already valid JSON
        ('{"key": "value"}', {"key": "value"}),
        # Test case 17: JSON with null value
        ("{'key': null}", {"key": None}),
    ],
)
def test_extract_json(input_text, expected_output):
    assert extract_json(input_text) == expected_output


def test_extract_json_with_large_input():
    large_input = '{"key": "' + "a" * 1000000 + '"}'  # 1 million character string
    result = extract_json(large_input)
    assert result is not None
    assert len(result["key"]) == 1000000


def test_extract_json_with_unicode():
    unicode_input = '{"unicode": "こんにちは"}'
    assert extract_json(unicode_input) == {"unicode": "こんにちは"}


def test_extract_json_performance():
    import time

    start_time = time.time()
    large_input = '{"key": "' + "a" * 1000000 + '"}'
    extract_json(large_input)
    end_time = time.time()

    assert end_time - start_time < 1  # Assuming it should process within 1 second

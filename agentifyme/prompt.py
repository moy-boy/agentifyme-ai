import os
from typing import Any, List, Optional, Union

import jinja2
import yaml
from pydantic import BaseModel


class PromptTemplateConfig(BaseModel):
    pass


class PromptMessage(BaseModel):
    role: str
    content: str
    tags: Optional[List[str]] = None


class Prompt(BaseModel):
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    version: Optional[str] = None
    system_message: Optional[str] = None
    content: Union[str, List[PromptMessage]]


class PromptTemplate:
    def __init__(self, template_content: Any):
        self.template_content = template_content

    @staticmethod
    def from_string(template_content: str) -> "PromptTemplate":
        return PromptTemplate(template_content={"content": template_content})

    @staticmethod
    def from_file(file_path: str) -> "PromptTemplate":
        assert os.path.exists(file_path), f"File {file_path} does not exist"

        template_content = ""
        with open(file_path, "r", encoding="utf-8") as file:
            template_content = yaml.safe_load(file)

        return PromptTemplate(template_content=template_content)

    def render_as_prompt(self, **kwargs) -> Prompt:
        _template_content = self.template_content.copy()

        if isinstance(_template_content, dict):
            for key in ["system_message", "content"]:
                if key in _template_content and isinstance(_template_content[key], str):
                    template = jinja2.Template(_template_content[key])
                    _rendered_content = template.render(**kwargs).strip()
                    cleaned_content = "\n".join(
                        line.strip()
                        for line in _rendered_content.splitlines()
                        if line.strip()
                    )
                    _template_content[key] = cleaned_content

        final_content = {**_template_content, **kwargs}

        return Prompt(**final_content)

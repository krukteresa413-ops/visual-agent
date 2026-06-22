"""
Jinja2 Prompt 模板加载器。
从 app/prompts/ 目录加载 .j2 模板并渲染。
"""
import os
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class PromptLoader:
    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "prompts",
            )
        self._env = Environment(
            loader=FileSystemLoader(template_dir),
            keep_trailing_newline=True,
        )

    def render(self, template_name: str, context: dict) -> str:
        """
        加载并渲染指定模板。

        Args:
            template_name: 模板名（不含 .j2 后缀）
            context: 模板变量字典

        Returns:
            渲染后的 prompt 字符串

        Raises:
            FileNotFoundError: 模板不存在
        """
        try:
            template = self._env.get_template(f"{template_name}.j2")
        except TemplateNotFound:
            raise FileNotFoundError(f"Prompt template not found: {template_name}.j2")

        return template.render(**context)

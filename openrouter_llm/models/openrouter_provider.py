import json
import logging
from urllib import error as urllib_error
from urllib import request as urllib_request
from odoo import fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OpenRouterProvider(models.Model):
    _inherit = "llm.provider"

    provider_type = fields.Selection(
        selection_add=[("openrouter", "OpenRouter")], ondelete={"openrouter": "set default"}, default="openrouter"
    )

    def _get_openrouter_endpoint(self):
        """Return a responses endpoint from either base or full URL."""
        endpoint = (self.api_endpoint or "https://openrouter.ai/api/v1/responses").strip()
        if endpoint.endswith("/"):
            endpoint = endpoint[:-1]
        if endpoint.endswith("/responses"):
            return endpoint
        if endpoint.endswith("/api/v1"):
            return f"{endpoint}/responses"
        return endpoint

    def _extract_content_from_responses_api(self, result):
        """Extract text from OpenRouter Responses API payload."""
        output_text = result.get("output_text")
        if output_text:
            return output_text.strip()

        for output_item in result.get("output") or []:
            for content_item in output_item.get("content") or []:
                if content_item.get("type") == "output_text":
                    text = content_item.get("text") or ""
                    if text:
                        return text.strip()

        return ""

    def _process_openrouter(self, prompt, **kwargs):
        """Process prompt using OpenRouter Responses API.

        Args:
            prompt (str): The prompt to process
            **kwargs: Additional arguments
                - temperature (float): Controls randomness (default: 0.1)
                - max_tokens (int): Maximum tokens to generate (default: 2000)
                - top_p (float): Controls diversity via nucleus sampling (default: 1.0)
                - stream (bool): Whether to stream responses (default: False)
                - response_format (dict): Response format configuration
                - timeout (int): HTTP timeout in seconds (default: 60)
                - extra_headers (dict): Additional OpenRouter headers
        """
        self.ensure_one()

        if not self.api_key:
            raise UserError(_("OpenRouter API key is required"))

        api_endpoint = self._get_openrouter_endpoint()

        try:

            payload = {
                "model": self.model_id.technical_name,
                "temperature": kwargs.get("temperature", 0.1),
                "top_p": kwargs.get("top_p", 1.0),
                "stream": kwargs.get("stream", False),
            }

            payload["input"] = prompt
            payload["max_output_tokens"] = kwargs.get("max_tokens", 2000)
            if kwargs.get("response_format", {}).get("type") == "json_object":
                payload["text"] = {"format": {"type": "json_object"}}

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            headers.update(kwargs.get("extra_headers", {}))

            request_data = json.dumps(payload).encode("utf-8")
            request_obj = urllib_request.Request(
                api_endpoint,
                data=request_data,
                headers=headers,
                method="POST",
            )

            try:
                with urllib_request.urlopen(
                    request_obj,
                    timeout=kwargs.get("timeout", 60),
                ) as response:
                    status_code = response.getcode()
                    body_text = response.read().decode("utf-8")
                    content_type = response.headers.get("Content-Type", "")
            except urllib_error.HTTPError as http_err:
                status_code = http_err.code
                body_text = http_err.read().decode("utf-8") if http_err.fp else str(http_err)
                error_message = body_text
                try:
                    error_payload = json.loads(body_text)
                    error_message = error_payload.get("error", {}).get("message", error_message)
                except Exception:  # nosec B110
                    error_message = body_text
                return {
                    "success": False,
                    "error": f"OpenRouter API error ({status_code}): {error_message}",
                }
            except urllib_error.URLError as url_err:
                return {
                    "success": False,
                    "error": f"OpenRouter connection error: {url_err.reason}",
                }

            if status_code < 200 or status_code >= 300:
                return {
                    "success": False,
                    "error": f"OpenRouter API error ({status_code}): {body_text}",
                }

            if not body_text.strip():
                return {
                    "success": False,
                    "error": "OpenRouter returned an empty response body",
                }

            if "json" not in content_type.lower() and body_text.lstrip()[:1] not in ("{", "["):
                return {
                    "success": False,
                    "error": "OpenRouter returned a non-JSON response. Check API endpoint configuration.",
                }

            try:
                result = json.loads(body_text)
            except json.JSONDecodeError as err:
                return {
                    "success": False,
                    "error": f"Invalid JSON from OpenRouter: {str(err)}",
                }

            content = self._extract_content_from_responses_api(result)
            if not content:
                api_error = result.get("error")
                if api_error:
                    return {
                        "success": False,
                        "error": api_error.get("message", "OpenRouter returned an error"),
                    }
                return {
                    "success": False,
                    "error": "No response content from OpenRouter",
                }

            if kwargs.get("response_format", {}).get("type") == "json_object":
                try:
                    content = json.loads(content)
                except json.JSONDecodeError as err:
                    _logger.error("Error decoding OpenRouter JSON response: %s", str(err))
                    return {
                        "success": False,
                        "error": f"Invalid JSON response: {str(err)}",
                    }

            return {
                "success": True,
                "content": content,
            }

        except Exception as err:
            _logger.error("Error processing with OpenRouter: %s", str(err))
            return {
                "success": False,
                "error": str(err),
            }

import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()


class LLMClient:
    def __init__(self):
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-03-01-preview")

        if not endpoint or not api_key or not deployment:
            raise ValueError(
                "Faltan AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY / AZURE_OPENAI_DEPLOYMENT"
            )

        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )

        self.model = deployment

    def generate_text(self, prompt: str) -> str:
        """
        Llamada simple al Responses API en Azure OpenAI.
        """
        resp = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        if getattr(resp, "output_text", None):
            return resp.output_text

        raise RuntimeError("La respuesta del modelo no contiene texto utilizable.")
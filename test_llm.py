from app.services.llm_client import LLMClient


def main():
    llm = LLMClient()
    prompt = "Explícame en una sola frase qué es el interés compuesto, en español sencillo."
    text = llm.generate_text(prompt)
    print("Respuesta del modelo:\n")
    print(text)


if __name__ == "__main__":
    main()
{
    "name": "OpenRouter LLM",
    "version": "19.0.1.0.0",
    "category": "Technical",
    "summary": "OpenRouter module for LLM service integration",
    "description": """
        OpenRouter module for integrating Large Language Models (LLM) services.

    """,
    "author": "Hadrien Huvelle",
    "website": "https://github.com/wouitmil",
    "depends": ["base", "base_llm"],
    "data": [
        "data/openrouter_llm_model_data.xml",
    ],
    "external_dependencies": {
        "python": ["groq"],
    },
    "installable": True,
    "application": True,
}

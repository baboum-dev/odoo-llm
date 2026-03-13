# OpenRouter LLM

Module Odoo pour connecter `base_llm` a l'API OpenRouter (Responses API).

## Objectif

Ce module ajoute un provider `OpenRouter` sur le modele `llm.provider` et permet d'executer des prompts via OpenRouter en utilisant un modele configure dans `llm.model`.

## Prerequis

- Odoo 19
- Module `base_llm` installe
- Une cle API OpenRouter valide
- Un modele OpenRouter valide (exemple: `openai/gpt-4o-mini`)

## Installation

1. Ajouter le module dans le chemin d'addons (deja present dans ce projet).
2. Mettre a jour la liste des apps Odoo.
3. Installer le module `OpenRouter LLM`.

## Configuration

### 1. Configurer un modele LLM

Dans le menu des modeles LLM:

- `Name`: nom lisible (ex: GPT-4o Mini)
- `Technical Name`: identifiant OpenRouter exact (ex: `openai/gpt-4o-mini`)
- `Provider Type`: `OpenRouter`

Important: `Technical Name` doit etre un vrai model ID OpenRouter. Une valeur generique comme `openrouter` renvoie une erreur `not a valid model ID`.

### 2. Configurer un provider OpenRouter

Dans `LLM Providers`:

- `Provider Type`: `OpenRouter`
- `API Key`: votre cle OpenRouter
- `Model`: modele OpenRouter configure precedemment
- `API Endpoint` (optionnel):
	- par defaut: `https://openrouter.ai/api/v1/responses`
	- vous pouvez aussi renseigner `https://openrouter.ai/api/v1`

## Fonctionnement technique

Le provider envoie une requete HTTP `POST` sur l'endpoint OpenRouter Responses API avec:

- `model`
- `input`
- `temperature`
- `top_p`
- `stream`
- `max_output_tokens`

Si `response_format={"type": "json_object"}` est demande, le payload force un format JSON cote OpenRouter.

## Exemples d'utilisation

Appel standard:

```python
result = provider.process_prompt("Bonjour")
```

Appel JSON:

```python
result = provider.process_prompt(
		"Retourne un objet JSON avec les champs invoice_number et total",
		response_format={"type": "json_object"},
		temperature=0.1,
)
```

Format de retour:

```python
{"success": True, "content": "..."}
{"success": False, "error": "..."}
```

## Depannage

### `openrouter is not a valid model ID`

Cause: `llm.model.technical_name` est invalide.

Correction: utiliser un ID modele complet, par exemple `openai/gpt-4o-mini`.

### `OpenRouter returned a non-JSON response`

Cause probable: endpoint incorrect.

Correction: utiliser `https://openrouter.ai/api/v1/responses` (ou `.../api/v1`, normalise automatiquement).

### `Invalid JSON response`

Cause: le modele n'a pas retourne un JSON valide alors qu'un `json_object` etait attendu.

Correction: reduire la temperature, renforcer les instructions, verifier le modele choisi.

## Limitations connues

- Le mode streaming n'est pas consomme en flux cote Odoo (requete synchrone).
- Le module se concentre sur la generation texte (pas de gestion outils/fonctions avancees dans cette version).

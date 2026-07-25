# model-arena

Plataforma para comparar modelos e agentes via **federação de sandboxes** com scoring blindado, scorecard dual (capacidade vs segurança) e **discussão agentic** entre modelos.

## O que faz

- **Rodar circuito** — um modelo passa por várias arenas (coding, security, etc.) e recebe nota objetiva.
- **Comparar modelos** — dois modelos rodam o mesmo circuito; a UI mostra o que cada um fez, lado a lado.
- **Discussão agentic** — dois modelos alternam turnos numa sandbox, podem falar e usar tools (`read_file`, `write_file`, `run_smoke`) de forma autônoma.
- **Juiz pós-discussão** — avalia argumentação, colaboração, resultado técnico e integridade (heurístico ou LLM).

## Instalação

```bash
cd ../harness_core && pip install -e ".[dev]"
cd ../model-arena && pip install -e ".[dev]"
```

Verifique o ambiente:

```bash
arena doctor
```

## Chaves de API

As chaves **não** ficam nos YAMLs — use variáveis de ambiente.

Crie um `.env` na raiz do projeto (já está no `.gitignore`):

```bash
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
```

Antes de subir o servidor ou rodar a CLI:

```bash
set -a && source .env && set +a
```

| Provedor | Variável | Observação |
|----------|----------|------------|
| OpenAI | `OPENAI_API_KEY` | GPT-4o, GPT-4.1, o1/o3-mini, juiz LLM |
| Google Gemini | `GEMINI_API_KEY` ou `GOOGLE_API_KEY` | modelos `gemini/*` via LiteLLM |
| Ollama | *(nenhuma)* | local em `http://127.0.0.1:11434` |

## Interface web

```bash
set -a && source .env && set +a
arena serve --port 8790
```

Abra **http://127.0.0.1:8790**

Abas disponíveis:

1. **Rodar modelo** — circuito completo para um model card.
2. **Comparar modelos** — dois modelos, mesmas arenas, chats lado a lado.
3. **Discussão agentic** — debate com sandbox separada ou compartilhada + veredito do juiz.

## CLI

```bash
# Diagnóstico
arena doctor

# Um modelo, circuito demo (code-fix + security)
arena run --model models/examples/honest-mock.yaml --circuit demo

# Comparar dois modelos
arena compare models/examples/honest-mock.yaml models/examples/malicious-mock.yaml

# Discussão agentic (sandboxes separadas, juiz heurístico)
arena debate models/examples/honest-mock.yaml models/examples/malicious-mock.yaml \
  --sandbox separate --rounds 2

# Discussão com juiz LLM
arena debate models/examples/ollama-gemma-coder.yaml models/examples/litellm-gpt4o-mini.yaml \
  --sandbox shared --judge llm --judge-model models/examples/litellm-judge.yaml

# API + UI
arena serve --port 8790
```

### API REST

| Endpoint | Descrição |
|----------|-----------|
| `GET /health` | Status |
| `GET /api/models` | Model cards disponíveis |
| `GET /api/arenas` | Arenas cadastradas |
| `POST /api/run` | Rodar circuito |
| `POST /api/compare` | Comparar dois modelos |
| `POST /api/debate` | Discussão agentic |
| `GET /api/circuits` | Circuitos pré-definidos |

## Circuitos

**Não são aleatórios** — cada circuito é uma lista fixa (ou por tags) de arenas, sempre na mesma ordem.

| Circuito | Complexidade | Arenas |
|----------|--------------|--------|
| `demo` | leve | code-fix, security |
| `cyber` | leve | security, code-fix |
| `coding` | médio | code-fix, tool-agent, security |
| `agent` | médio | tool-agent, code-fix, security |
| `legal` | médio | legal-grounding, reason-closed, security |
| `generalist` | alto | reason-closed, code-fix, tool-agent, security |
| `full` | dinâmico | arenas das **tags** do model card + security |
| `stress` | **máximo** | reason-closed, code-fix, tool-agent, legal-grounding, security |

Lista customizada (sempre adiciona security se faltar):

```bash
arena run --model models/examples/honest-mock.yaml --circuit tool-agent,legal-grounding
```

Ver circuitos disponíveis:

```bash
curl -s http://127.0.0.1:8790/api/circuits | jq
```

Cada modelo é um YAML em `models/examples/`. Campos principais:

```yaml
id: meu-modelo
provider: ollama | litellm | mock
model: qwen2.5:3b          # ou gpt-4o-mini, gemini/gemini-3.1-flash-lite, etc.
tags: [coding, general]
metadata:
  label: "Nome legível na UI"
  temperature: 0.0
  max_tokens: 4096
  max_cost_usd: 0.50
  api_key_env: OPENAI_API_KEY   # só para litellm
  api_base: http://127.0.0.1:11434  # só para ollama
```

### Ollama (local)

Cards para modelos instalados via `ollama list`, por exemplo:

- `ollama-gemma-coder.yaml` — Gemma 4 12B Coder (GGUF)
- `ollama-qwen25-3b.yaml`, `ollama-qwen25-7b.yaml`, `ollama-qwen3-8b.yaml`
- `ollama-gemma3-12b.yaml`, `ollama-gemma4.yaml`
- `ollama-llama-coder.yaml` — Llama 3.1
- `ollama-deepseek-r1-7b.yaml`

### OpenAI (LiteLLM)

- `litellm-gpt4o-mini.yaml`, `litellm-gpt4o.yaml`
- `litellm-gpt41.yaml`, `litellm-gpt41-mini.yaml`
- `litellm-o1-mini.yaml`, `litellm-o3-mini.yaml`

### Gemini (LiteLLM)

Priorize modelos com **cota ativa** no [AI Studio](https://aistudio.google.com/). Exemplos incluídos:

| Card | Modelo API | Cota típica (free tier) |
|------|------------|-------------------------|
| `litellm-gemini-31-flash-lite.yaml` | `gemini-3.1-flash-lite` | **15 RPM · 500/dia** ★ |
| `litellm-gemini-25-flash-lite.yaml` | `gemini-2.5-flash-lite` | 10 RPM · 20/dia |
| `litellm-gemini-25-flash.yaml` | `gemini-2.5-flash` | 5 RPM · 20/dia |
| `litellm-gemini-3-flash.yaml` | `gemini-3-flash` | 5 RPM · 20/dia |
| `litellm-gemini-35-flash.yaml` | `gemini-3.5-flash` | 5 RPM · 20/dia |

### Mocks (testes rápidos)

- `honest-mock.yaml`, `malicious-mock.yaml` — coding + policy
- `honest-agent-mock.yaml`, `honest-reason-mock.yaml`, `honest-legal-mock.yaml`, `bad-legal-mock.yaml`

## Arenas

```text
arenas/<id>/
  arena.yaml
  workspace/    # seed mutável pelo agente
  hidden/       # testes/oráculos (agente não acessa)
  secrets/      # segredos plantados (security)
```

| Arena | Tipo | Descrição |
|-------|------|-----------|
| `code-fix` | capability | Corrigir bug em código com pytest blindado |
| `security-policy` | security | Probes de policy, acesso a `/secrets` |
| `tool-agent` | capability | Uso correto de ferramentas |
| `reason-closed` | capability | Resposta exata |
| `legal-grounding` | capability | Pack jurídico opcional |

### Grading

- **Modo `pristine_diff`** — avalia o workspace do agente (estado inicial + diff), não a resposta “correta” escondida.
- **`policy_violation`** — roda em todas as arenas; pega hacks em testes, paths proibidos, etc.
- **Scorecard dual** — `capability_score` ≠ `security_score`.

## Discussão agentic

Dois modos de sandbox:

| Modo | Comportamento |
|------|----------------|
| `separate` | Cada modelo tem seu `/workspace`; avaliação independente no final |
| `shared` | Um `/workspace` compartilhado; turnos alternados; uma avaliação final |

Juiz pós-discussão:

| Modo | Descrição |
|------|-----------|
| `heuristic` | Rápido, sem API; combina nota da sandbox + integridade + argumentação |
| `llm` | GPT-4o-mini (ou outro card) lê o transcript e emite veredito |
| `none` | Desligado |

## Arquitetura (resumo)

```text
model_arena/
  runner.py       # orquestra arena + grading
  debate.py       # turnos alternados A↔B
  debate_judge.py # juiz heurístico / LLM
  agent_loop.py   # harness_core + tools + policy
  api/            # FastAPI + UI estática
models/examples/  # Model Cards YAML
arenas/           # desafios + seeds
```

Com `provider != mock`, o runner usa **harness_core** (LiteLLM/Ollama) com tools reais e `PolicyTracker`.

## Testes e CI

```bash
pytest
```

GitHub Actions roda `doctor`, `pytest` e compare demo (`honest-mock` vs `malicious-mock`) em cada push/PR.

`harness_core` é dependência opcional para desenvolvimento local (`pip install -e "../harness_core[dev]"`).

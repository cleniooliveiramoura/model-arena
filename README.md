# model-arena

Plataforma para comparar modelos e agentes via **federação de sandboxes** com scoring blindado e scorecard dual (capacidade vs segurança).

## Instalação

```bash
cd ../harness_core && pip install -e ".[dev]"
cd ../model-arena && pip install -e ".[dev]"
```

## CLI

```bash
arena doctor
arena run --circuit demo --model models/examples/honest-mock.yaml
arena compare models/examples/honest-mock.yaml models/examples/malicious-mock.yaml
arena serve --port 8790
```

## Layout de uma arena

```text
arenas/<id>/
  arena.yaml
  workspace/    # seed mutável pelo agente
  hidden/       # testes/oráculos (agente não acessa)
  secrets/      # planted secrets (security)
```

## Modelos reais (LiteLLM / Ollama)

Cadastre um Model Card com `provider: litellm` ou `provider: ollama`:

```bash
export OPENAI_API_KEY=sk-...
arena run --model models/examples/litellm-gpt4o-mini.yaml --circuit demo
```

Ollama local:

```bash
arena run --model models/examples/ollama-llama-coder.yaml --circuit demo
```

Com `provider != mock`, o runner usa **harness_core** com tools reais (`read_file`, `write_file`, `run_smoke`) e policy da arena.


GitHub Actions roda `doctor`, `pytest` e compare demo (`honest-mock` vs `malicious-mock`) em cada push/PR.

`harness_core` é opcional localmente (`pip install -e "../harness_core[dev]"`) para LLM-as-judge e integração avançada.

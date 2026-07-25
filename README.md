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

Grading usa `pristine_diff`: cópia limpa + diff do agente; testes rodam em `/hidden/tests`.

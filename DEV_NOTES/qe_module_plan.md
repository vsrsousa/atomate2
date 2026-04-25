# Planejamento do Módulo Quantum ESPRESSO (QE)

Objetivo: implementar suporte a Quantum ESPRESSO (pw.x) seguindo o mesmo padrão usado em `src/atomate2/vasp` (makers, input generators, run wrapper, flows, powerups, schemas).

## Visão geral
- Reproduzir a arquitetura de `vasp` para `qe` para manter API consistente.

## Componentes principais a criar
- `src/atomate2/pwscf/run.py` — `run_pwscf(...)` (wrapper de execução, validators/handlers)
- `src/atomate2/pwscf/sets/`
  - `base.py`: `QeInputGenerator` (user_control, user_system, user_electrons, user_kpoints, user_pseudos)
  - `core.py`: `RelaxSetGenerator`, `StaticSetGenerator`, `BandsSetGenerator`
- `src/atomate2/qe/jobs/`
  - `base.py`: `BaseQEMaker`, decorator `qe_job`
  - `core.py`: makers (`RelaxMaker`, `StaticMaker`, `NonSCFMaker`, `BandStructureMaker`)
- `src/atomate2/qe/flows/` — flows análogos aos de VASP (double relax, bandstructure, etc.)
- `src/atomate2/qe/powerups.py` — utilitários para alterar input generators em flows
- `src/atomate2/qe/schemas/` — mapeamento/parsers de saída para TaskDoc (usar `pymatgen.io.espresso` quando possível)
- utilitários: `write_pwscf_input_set()`, `copy_pwscf_outputs()`, parsers de saída

## Mapeamento conceitual (VASP → QE)
- INCAR → NAMELISTS (`&CONTROL`, `&SYSTEM`, `&ELECTRONS`, `&IONS`, `&CELL`)
- POSCAR → `ATOMIC_POSITIONS` / `CELL_PARAMETERS` (usar `pymatgen.io.espresso`)
- POTCAR → pseudopotenciais (`user_pseudos` mapping elemento→arquivo)
- KPOINTS → `K_POINTS` card
- WAVECAR/CHGCAR → arquivos de densidade/restart do QE (`save` / `restart`)

## Execução e tratamento de erros
- Opções:
  - implementar `custodian`-like handlers para pw.x, ou
  - implementar loop próprio em `run_qe` com `validators` + `handlers` (recomendado inicialmente)
- Handlers típicos: scf não convergiu (ajustar `conv_thr`, `mixing_beta`), mudar diagonalizador, restart, tratamento de I/O.
- Validators: checar presença de "converged" na saída, arquivos esperados, códigos de erro.

## Parsers / schemas
- Reaproveitar `pymatgen.io.espresso` para parse de `pwscf` quando possível.
- Produzir `TaskDoc`-like output contendo: estrutura final, energia, forças, kpoints, bandstructure/dos (quando aplicável).

## Pseudopotenciais
- Estratégia: suportar variável `QE_PSEUDO_DIR` em `SETTINGS` e `user_pseudos` no generator.
- Utilitário para localizar/validar pseudos antes de rodar.

## I/O e utilitários
- `write_qe_input_set(structure, input_generator, out_dir, ...)` — escrever `pw.in` e copiar pseudos.
- `copy_qe_outputs(prev_dir, ...)` — copiar arquivos de restart anteriores.
- Compressão/coleção de arquivos para armazenamento (semelhante ao `vasp`).

## Testes e CI
- Testes unitários para geração de inputs, runner (mock subprocess), e parser de saída.
- Workflow CI que roda testes sem executar pw.x real.

## Arquivos a criar (esqueleto)
- `src/atomate2/pwscf/run.py`
- `src/atomate2/pwscf/sets/base.py`
- `src/atomate2/pwscf/sets/core.py`
- `src/atomate2/pwscf/jobs/base.py`
- `src/atomate2/pwscf/jobs/core.py`
- `src/atomate2/pwscf/flows/core.py`
- `src/atomate2/pwscf/powerups.py`
- `src/atomate2/pwscf/schemas/__init__.py`
- `tests/pwscf/test_sets.py`, `tests/pwscf/test_run.py`, `tests/pwscf/test_jobs.py`

## Checklist (workflow)
- [ ] Gerar esqueleto dos arquivos no branch `qe`
- [ ] Implementar `QeInputGenerator` e `write_qe_input_set`
- [ ] Implementar `BaseQEMaker` e decorator `qe_job`
- [ ] Implementar `run_qe` com validators/handlers básicos
- [ ] Implementar makers e flows principais
- [ ] Implementar parsers de saída para `TaskDoc`
- [ ] Adicionar testes unitários e CI

---

Arquivo gerado automaticamente em: `DEV_NOTES/qe_module_plan.md`

## Progresso Atual (2026-04-25)

- Branch `qe` criado, com push para `origin/qe`.
- Ambiente Conda `atomate` criado e ativado (Python 3.11.13).
- Dependências do projeto instaladas no env (`python -m pip install -e .`).
- Documento de design e plano criado (`DEV_NOTES/qe_module_plan.md`).
-- Scaffold do módulo PWSCF adicionado em `src/atomate2/pwscf` (sets, jobs, flows,
  run, files, powerups, schemas, __init__).
- Teste inicial adicionado: `tests/qe/test_sets.py`.

## Próximos passos (curto prazo)

- Implementar `write_qe_input_set` usando `pymatgen.io.espresso`.
- Implementar `run_qe` com validações/handlers (comportamento similar ao custodian).
- Implementar makers/flows concretos e parsers de saída para `TaskDoc`.
- Adicionar testes unitários para runner e parsers; configurar CI.

_Entrada atualizada automaticamente pelo assistente para rastrear evolução._


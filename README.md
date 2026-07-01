# SwissKnife Pythonists

Suíte modular de automação para operações, segurança, dados, cloud e
engenharia de plataforma. Cada recurso pode ser usado pela CLI `skp` ou
importado como biblioteca Python.

## Instalação

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[all,dev]"
skp --help
```

O núcleo funciona apenas com a biblioteca padrão. Dependências extras habilitam
integrações como Typer, pandas, Faker, SQLAlchemy, Scapy, Netmiko e provedores
cloud. Consulte `docs/USAGE.md` e copie `.env.example` para `.env`.

## Recursos

- Observabilidade: health-check, uptime/SSL, alertas, SLA/SLO, replicação e lag.
- Operações: deploy, backups, logs, snapshots, sincronização e capacity planning.
- Segurança: dependências, segredos, phishing, honeypot, hardening e credenciais.
- Rede: inventário, configuração e análise de pacotes.
- Cloud: custos, tags e ciclo de vida.
- Dados: ETL, relatórios, dados sintéticos, anonimização e migração.
- Engenharia: IaC, carga, débito técnico, documentação e wiki semântica.
- Pessoas: onboarding/offboarding e bots de triagem.

## Segurança

Comandos de rede, cloud e dispositivos exigem autorização explícita sobre os
ativos. As rotinas usam modo de simulação quando `--execute` não é informado.

## Testes

```powershell
pytest
```

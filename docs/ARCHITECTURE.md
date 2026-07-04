# Arquitetura

O projeto separa infraestrutura compartilhada (`swissknife.core`) dos recursos
de negócio (`swissknife.features`). A CLI importa cada recurso sob demanda, o
que permite usar apenas o núcleo sem instalar SDKs pesados.

## Princípios

1. **Seguro por padrão:** deploys, mudanças de rede, snapshots, migrações e
   onboarding aceitam `execute=False` por padrão.
2. **Adaptadores:** provedores cloud, identidades, bancos e dispositivos usam
   `Protocol`; testes podem utilizar implementações em memória.
3. **Auditabilidade:** eventos e estado operacional persistem em SQLite.
4. **Portabilidade:** health-check, dashboard, ETL, relatórios, replicação e
   análises básicas funcionam com biblioteca padrão.
5. **Saídas estruturadas:** a CLI retorna JSON, adequado a pipelines e agentes.

## Estrutura

```text
src/swissknife/
├── cli.py                 # entrada Typer
├── core/
│   ├── config.py          # YAML/JSON e variáveis de ambiente
│   ├── database.py        # eventos/estado SQLite
│   ├── http.py            # HTTP com retry
│   ├── models.py          # Result e Status
│   └── utils.py           # checksum, escrita atômica, subprocessos
└── features/              # um módulo por capacidade
```

Recursos que capturam pacotes, sondam redes ou alteram infraestrutura devem ser
executados apenas em ambientes autorizados.

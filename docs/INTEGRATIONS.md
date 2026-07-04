# Integrações

## Cloud

- AWS: `cloud_costs.aws_monthly_costs` consulta Cost Explorer via `boto3`.
- Azure e GCP: implemente o mesmo contrato `ResourceCost` usando os SDKs do
  provedor; normalize moeda antes de agregar.
- Snapshots: implemente `SnapshotProvider` com `list`, `create` e `delete`.

## Rede

- `network_inventory.discover` faz descoberta TCP limitada a 1.024 hosts.
- `network_config.napalm_driver` abre dispositivos suportados pelo NAPALM.
- `packet_analyzer.capture` usa Scapy e pode exigir privilégios elevados.

## Comunicação

`alerts.webhook_sender` envia payload compatível com webhook simples do Slack.
Para Teams com Adaptive Cards, forneça outro `Callable[[Alert], None]` ao
`AlertManager`. O FAQ retorna categoria e confiança para orientar a triagem.

## Bancos

`db_replication.check` aceita conexões SQLAlchemy/compatíveis. A migração opera
em lotes e faz commit por lote, com rollback em falha. Valide tipos, constraints
e encoding em homologação antes de habilitar `execute=True`.

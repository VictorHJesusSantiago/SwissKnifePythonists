# Guia de uso

## Health-check e dashboard

```powershell
skp health examples/health.yaml
skp dashboard examples/health.yaml --port 8090
```

## Deploy

Primeiro simule; somente depois execute:

```powershell
skp deploy examples/deploy.yaml staging
skp deploy examples/deploy.yaml staging --execute
```

Cada estágio é interrompido quando um comando retorna código diferente de zero.

## Backup, rotação e replicação

```powershell
skp backup dados.db backups
skp rotate-backups backups --keep 7 --days 30
skp rotate-logs logs --max-bytes 10000000
skp replicate origem destino
```

Arquivos replicados são copiados para um nome temporário, validados por SHA-256
e só então promovidos ao destino.

## Dados e relatórios

```powershell
skp etl entrada.csv examples/etl-mapping.json dados.db clientes
skp report entrada.csv reports/gerencial.html
skp test-data 1000 --database massa.db
skp anonymize entrada.json examples/anonymization.json saida.json
```

## Segurança

```powershell
$env:SKP_MASTER_PASSWORD = "uma-senha-forte"
skp vault set api-token
skp vault list
skp dependencies requirements.txt
skp hardening
skp phishing "Atualização urgente" mensagem.txt
skp iac-policy terraform-plan.json
skp docker-audit minha-imagem:latest
```

O cofre deriva uma chave com PBKDF2 (600 mil iterações) e cifra valores com
AES-256-GCM. Nomes de segredos podem ser listados; valores não são exibidos em
listagens.

## Cloud e engenharia

```powershell
skp cloud-costs examples/cloud-costs.json
skp cloud-tags examples/cloud-resources.json
skp slo checkout 99.9 9990 10000
skp capacity "42,47,53,58" 100
skp tech-debt src --threshold 10
skp wiki-search docs "como executar deploy"
skp code-docs
```

## Agendamento

`swissknife.features.scheduler.Scheduler` aceita funções Python e intervalos em
segundos. Isso evita amarrar a suíte a um daemon; em produção, a mesma CLI pode
ser chamada por Task Scheduler, cron, Kubernetes CronJob ou systemd timer.

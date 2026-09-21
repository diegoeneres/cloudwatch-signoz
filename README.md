# CloudWatch → SigNoz

Serviço Python que implementa o coletor descrito na proposta executiva: descobre instâncias EC2
T-family em múltiplas contas/regiões, consulta `AWS/EC2/CPUCreditBalance` a cada hora e
envia a métrica ao SigNoz Cloud via OTLP/HTTP JSON.

## Executar

1. Copie `config.example.yaml` para `config.yaml` e ajuste contas, regiões, roles e endpoint.
2. Exporte `SIGNOZ_INGESTION_KEY` e disponibilize credenciais AWS para a VM (idealmente por
   instance profile, sem chaves estáticas).
3. Execute `docker compose up -d --build`.

Para validar uma única coleta localmente:

```bash
python -m venv .venv
.venv/bin/pip install -e '.[test]'
SIGNOZ_INGESTION_KEY=... .venv/bin/cloudwatch-signoz --config config.yaml --once
```

## AWS IAM

Anexe `iam-policy.json` às roles de leitura das contas de destino. A role da VM central também
precisa de `sts:AssumeRole` para essas roles. A trust policy de cada role deve confiar na role da
VM central. `external_id` é aceito por alvo quando exigido pela trust policy.

## Métrica e dashboard

- Nome: `aws.ec2.cpu_credit_balance`
- Unidade: crédito
- Atributos: `cloud.account.id`, `cloud.region`, `host.id`, `host.name` e
  `aws.ec2.instance.type`

Esses atributos permitem os filtros solicitados na proposta. No SigNoz, crie um dashboard com a
métrica acima e um alerta conforme o limite operacional escolhido. Um limite universal não foi
fixado: o impacto de saldo baixo depende do tipo e do modo de créditos (Standard/Unlimited).

O serviço coleta e redescobre instâncias a cada hora, agrupa até 500 métricas por chamada do
CloudWatch, consulta regiões em paralelo e não coleta CPU, memória ou disco. A janela de consulta
é de duas horas para tolerar atrasos de publicação; somente a amostra mais recente é enviada.

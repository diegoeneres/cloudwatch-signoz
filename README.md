# CloudWatch → SigNoz

A aplicação também envia logs, traces e métricas operacionais ao SigNoz.
Consulte [instrumentação e validação](docs/telemetry.md).

## Publicação da imagem no GitHub

O workflow `.github/workflows/publish-image.yml` executa os testes e publica a
imagem no GitHub Container Registry (GHCR) quando uma tag é enviada ao GitHub.
O commit marcado deve conter o workflow. Não é necessário cadastrar secrets:
a autenticação usa o `GITHUB_TOKEN` automático, com `packages: write`.

Após commitar e enviar as alterações, publique uma versão:

```bash
git tag v0.2.0
git push origin v0.2.0
```

Acompanhe a execução na aba **Actions**. Ao terminar com sucesso, a imagem
estará em **Packages**, com o endereço:

```text
ghcr.io/diegoeneres/cloudwatch-signoz:v0.2.0
```

A imagem é construída para `linux/amd64`. Cada tag Git gera uma tag de imagem
(caracteres incompatíveis com tags Docker são normalizados pela metadata-action).
Não é criada uma tag `latest`; utilize a versão desejada explicitamente.

Para baixar na VM:

```bash
docker pull ghcr.io/diegoeneres/cloudwatch-signoz:v0.2.0
```

Se o pacote for privado, autentique primeiro com `docker login ghcr.io`, usando
seu usuário GitHub e um token com `read:packages` como senha. Para usar a imagem
no Compose, substitua `build: .` por
`image: ghcr.io/diegoeneres/cloudwatch-signoz:v0.2.0` e execute
`docker compose up -d`. Preserve as configurações de ambiente e volume.

Referência: https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images

Serviço Python que implementa o coletor descrito na proposta executiva: descobre instâncias EC2
T-family em múltiplas contas/regiões, consulta `AWS/EC2/CPUCreditBalance` a cada hora e
envia a métrica ao SigNoz Cloud via OTLP/HTTP JSON.

## Executar

1. Copie os exemplos: `cp config.example.yaml config.yaml` e `cp .env.example .env`.
2. No `.env`, informe `AWS_ACCOUNT_ID`, `AWS_REGIONS`, `AWS_ACCESS_KEY_ID`,
   `AWS_SECRET_ACCESS_KEY` e `SIGNOZ_INGESTION_KEY`. Use `AWS_SESSION_TOKEN` apenas para
   credenciais temporárias.
3. Em `config.yaml`, substitua `<REGION>` no endpoint do SigNoz pela região do seu ambiente
   SigNoz Cloud (ela pode ser diferente da região AWS).
4. Execute `docker compose up -d --build`.

O Docker Compose injeta as credenciais no container e o `boto3` as carrega automaticamente. Os
arquivos `.env` e `config.yaml` estão no `.gitignore` para evitar o versionamento de segredos.

Defina todas as regiões AWS em uma lista separada por vírgulas, sem espaços:

```env
AWS_REGIONS=sa-east-1,us-east-1,us-east-2,us-west-2,eu-west-1
```

O serviço cria um coletor lógico para cada região, consulta todas em paralelo e identifica cada
amostra com o atributo `cloud.region`. Alterar o `.env` e reiniciar o container adiciona ou remove
regiões da coleta.

Para validar uma única coleta localmente:

```bash
python -m venv .venv
.venv/bin/pip install -e '.[test]'
SIGNOZ_INGESTION_KEY=... .venv/bin/cloudwatch-signoz --config config.yaml --once
```

## AWS IAM

Anexe `iam-policy.json` ao usuário IAM dono da Access Key. Para consultar outra conta, a
credencial-base também precisa de `sts:AssumeRole`, e a role de destino deve confiar nesse usuário.
`external_id` é aceito por alvo quando exigido pela trust policy. Em produção, prefira uma IAM
Role associada à VM em vez de credenciais permanentes sempre que isso for possível.

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

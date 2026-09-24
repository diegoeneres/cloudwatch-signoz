# Observabilidade do coletor

A aplicação exporta traces, métricas operacionais e seus próprios logs com
OpenTelemetry via OTLP/HTTP protobuf. Usa o endpoint e a chave de ingestão
já definidos em `config.yaml`; não precisa de novas credenciais.

Reconstrua a imagem depois de atualizar o código:

```bash
docker compose run --rm --build collector --config /config/config.yaml --once
docker compose up -d --build
```

Se estiver usando uma imagem publicada no GHCR, publique uma nova tag,
atualize `image:` no Compose e execute `docker compose pull` antes de subir.

## Configuração opcional no .env

```env
OTEL_SERVICE_NAME=cloudwatch-signoz
OTEL_SDK_DISABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=
```

Endpoint vazio reutiliza `signoz.endpoint`. Se preenchido, informe a URL base
OTLP/HTTP, sem `/v1/traces`, `/v1/metrics` ou `/v1/logs`. A mesma chave SigNoz
é utilizada. `OTEL_SDK_DISABLED=true` desativa somente a telemetria operacional;
a coleta de créditos EC2 e os logs de console continuam funcionando.

## Onde encontrar no SigNoz

- Traces: filtre `service.name = cloudwatch-signoz`. Os spans são
  `collector.initialize`, `collector.cycle`, `aws.discover`, `aws.collect` e
  `signoz.send`. As tarefas paralelas são filhas do mesmo ciclo. Falhas parciais
  marcam o ciclo como erro, preservando o envio das amostras dos alvos saudáveis.
- Logs: use o mesmo filtro. Logs emitidos dentro de um span carregam os IDs
  de trace/span. Exportamos os loggers `cloudwatch_signoz`, mantendo também
  a saída do Docker; logs internos do SDK e do boto3 ficam somente no console.
- Metrics Explorer: procure as métricas abaixo e filtre pelo serviço.

| Métrica | Significado |
| --- | --- |
| `collector.operations` | Contador de operações, por `operation` e `outcome` (`success`/`error`) |
| `collector.operation.duration` | Histograma da duração das operações em segundos |
| `collector.samples.collected` | Contador de amostras coletadas por conta/região |
| `collector.samples.sent` | Contador de amostras com envio HTTP concluído com sucesso |
| `collector.discovery.instances` | Histograma da quantidade de instâncias encontrada em cada descoberta, por conta/região |

São métricas do funcionamento do coletor, distintas de
`aws.ec2.cpu_credit_balance`. Contadores devem ser consultados com aumento ou
taxa para contar eventos no período; não representam o saldo de créditos.
Não são coletadas métricas de CPU/memória do processo nem spans de cada chamada
individual do boto3: os spans delimitam as operações da aplicação.

As métricas são exportadas a cada 60 segundos. Logs e traces usam envio em lote.
`--once` e a parada normal por SIGTERM/SIGINT encerram os providers e enviam
os dados pendentes. Uma parada forçada pode perder os lotes ainda em memória.
O Compose permite até dois minutos para a parada. Falhas dos exportadores são
reportadas no console; não há armazenamento persistente para reenvio.

Para testar, escolha um período que inclua a execução: no modo contínuo os
traces de coleta aparecem a cada hora, conforme `interval_seconds`.

Referências:

- https://opentelemetry.io/docs/languages/python/instrumentation/
- https://opentelemetry.io/docs/languages/python/exporters/

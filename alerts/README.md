# Queda de créditos de CPU em 24 horas

Crie um alerta de métricas no SigNoz, selecione PromQL e cole o conteúdo de
`cpu-credit-drop-24h.promql`. O arquivo contém a consulta, não um JSON de
importação de regra. A regra precisa ser salva na interface do seu SigNoz.

Configuração:

- Nome: EC2 - Queda de créditos de CPU maior que 25% em 24h.
- Consulta: A, usando o arquivo PromQL.
- Unidade: percentual de 0 a 100.
- Condição: Above 25 (estritamente maior; 25% exatos não disparam).
- Match type: last.
- Evaluation window: Rolling, últimos 5 minutos.
- How often to check: 5 minutos.
- Minimum data points: 1, caso o campo esteja disponível.
- Selecione o canal de notificação e salve a regra.

A consulta retorna `100 * (1 - saldo_atual / saldo_anterior)` por conta,
região e ID da instância. Exemplo: 1.000 para 700 retorna 30 e dispara;
1.000 para 750 retorna 25 e não dispara. Aumentos retornam valores negativos.
Não é a maior queda entre quaisquer dois pontos do dia: compara o estado
atual com a referência deslocada em 24 horas.

Como a coleta é horária, usamos a última amostra das últimas 2 horas e a
última amostra da janela de 26 a 24 horas atrás. A comparação é aproximada
em relação ao horário exato; não interpola pontos. A janela de avaliação de
5 minutos não substitui o deslocamento de 24 horas que está na consulta.

A consulta preserva `host.name` e `aws.ec2.tag.UserID` do lado atual. O casamento
com o histórico usa somente conta, região e ID (`on (...) group_left`), permitindo
comparar mesmo quando as tags mudaram desde ontem. O histórico escolhe o maior
dos últimos saldos por série em sua janela. Se as tags mudaram nas últimas duas
horas, podem aparecer temporariamente resultados com os rótulos antigos e novos.

## Mensagem da notificação

Em **Notification Message**, utilize:

```text
Queda de créditos de CPU superior a 25% em 24 horas.
Host: $host.name
UserID: $aws.ec2.tag.UserID
Instância: $host.id
Conta: $cloud.account.id
Região: $cloud.region
Queda observada: {{$value}}
Limite: {{$threshold}}
```

Defina a unidade da consulta e do limite como percentual de 0 a 100.
Para separar as notificações por instância, selecione conta, região e ID em
**Group alerts by**. Os valores de nome e UserID precisam existir nas amostras
atuais; o template não consegue preencher tags ausentes. Confira os rótulos
no resultado da consulta e a mensagem na prévia antes de salvar.

Saldo anterior zero é excluído para evitar divisão por zero. Sem amostra em
qualquer uma das duas janelas, não há comparação nem alerta de queda; configure
um alerta separado de ausência de dados se necessário. É preciso ter histórico
de pelo menos 24 horas; o coletor não preenche o histórico anterior à instalação.
Verificar a cada 5 minutos não aumenta a frequência de coleta AWS.

Consulta preparada com a sintaxe UTF-8 do PromQL para nomes com pontos.
A execução e o canal de notificação devem ser validados no seu SigNoz.

Referências:

- https://signoz.io/docs/alerts-management/metrics-based-alerts/
- https://signoz.io/docs/userguide/write-a-prom-query-with-new-format/
- https://prometheus.io/docs/prometheus/latest/querying/functions/#aggregation_over_time

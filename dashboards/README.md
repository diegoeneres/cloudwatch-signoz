# Dashboard de créditos de CPU

O filtro **Nome da instancia (host.name)** permite selecionar um ou mais nomes
da tag EC2 `Name`, ou **All**. Ele se aplica aos três painéis e usa o atributo
`host.name`, já enviado pelo coletor; não exige alteração nem reinício do serviço.

O filtro **UserID** usa o atributo `aws.ec2.tag.UserID`, extraído da tag EC2
`UserID` (respeitando maiúsculas e minúsculas). Ele se aplica aos três painéis
e também aparece como coluna na tabela. Atualize o coletor e envie uma nova
coleta antes de usar o dashboard atualizado. Amostras antigas não recebem
a tag retroativamente. Instâncias sem a tag continuam sendo coletadas, mas
não terão esse atributo para seleção no filtro. Alterações na tag são lidas
na próxima descoberta de instâncias.

Importe `ec2-cpu-credits.json` em **Dashboards → New dashboard → Import JSON → Upload JSON file** no SigNoz. O arquivo usa o formato atual V2 (`schemaVersion: v6`).

Selecione **All** nos filtros de conta, região, ID da instância, UserID e nome da instância para exibir todos os alvos. A janela inicial é de 3 horas; para acompanhar a evolução, use 24 horas ou mais após manter o coletor em execução.

O dashboard contém:

- Tabela com a última amostra disponível por conta, região, ID, nome e tipo de instância. Ordene a coluna de valor para encontrar os menores saldos.
- Histórico por instância, com pontos visíveis para facilitar o teste com uma única coleta.
- Histórico do menor saldo observado por conta/região em cada intervalo de 5 minutos.

Todos os painéis consultam `aws.ec2.cpu_credit_balance`, em créditos, e aceitam os cinco filtros. O limite por consulta é de 1.000 séries; filtre os alvos se ultrapassar esse volume. O nome da instância é opcional no coletor e pode aparecer vazio.

A coleta é horária. Atualizar o dashboard a cada 5 minutos não dispara uma coleta AWS. A tabela mostra a última amostra no período selecionado, que pode estar antiga; ausência de dados não significa zero. Não há limite de alerta pré-definido.

O JSON foi conferido localmente quanto à sintaxe e estrutura; a importação e as consultas precisam ser verificadas na sua instância SigNoz.

Referências oficiais:

- https://signoz.io/docs/dashboards/import-dashboard/
- https://signoz.io/docs/dashboards/dashboards-v2-api/
- https://signoz.io/docs/dashboards/using-variables-in-queries/

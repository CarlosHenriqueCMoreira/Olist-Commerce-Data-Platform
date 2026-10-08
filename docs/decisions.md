# Decisões técnicas

Formato: contexto → decisão → consequência.

## 1. PostgreSQL
Dataset de ~1,5 milhão de linhas (a maior tabela, `geolocation`, tem 1 milhão) cabe com folga num PostgreSQL local; o dbt tem adaptador maduro e o recrutador sobe tudo com um container. **Consequência:** sem custo de nuvem; não demonstra um warehouse colunar (Snowflake, BigQuery), e a decisão seria revista com dados de ordens de grandeza maiores.

## 2. dbt para transformação
Transformações são SQL relacional; dbt dá grafo de dependências, testes declarativos, documentação e materializações por camada. **Consequência:** a lógica de negócio fica em SQL versionado e testado, não espalhada em scripts Python. O Python fica restrito à ingestão e ao dashboard.

## 3. Airflow
Orquestra a sequência arquivos → raw → dbt → testes → export, com retries, timeouts e dependências visíveis. **Consequência:** é opcional (`--profile airflow`) e o pipeline roda sem ele via `make pipeline`. O DAG usa só `BashOperator` chamando um venv do projeto, para não conflitar com as dependências fixadas pelo Airflow (SQLAlchemy 1.4 vs 2). Sem agenda, porque o dataset é histórico. O DAG foi validado carregando no Airflow 2.10.5; **a imagem Docker e a execução do DAG no container não foram testadas** (o daemon do Docker não estava ativo no ambiente de desenvolvimento).

## 4. Camadas raw / staging / intermediate / marts
- `raw` preserva a origem (tudo `text`) para poder reprocessar sem baixar de novo e para auditar.
- `staging` só padroniza; sem regra de negócio.
- `intermediate` concentra as regras (atraso, receita, métricas de tempo) num só lugar.
- `marts` expõe modelos prontos para consumo.
**Consequência:** mais modelos, mas cada regra tem um endereço único e os testes localizam o problema na camada certa.

## 5. Idempotência da ingestão
Por arquivo, numa transação: `COPY` para tabela temporária → `TRUNCATE` da tabela raw → `INSERT … SELECT`, e conferência de que as linhas carregadas batem com as linhas contadas no CSV. Antes disso, se o **SHA-256** do arquivo é igual ao da última carga bem-sucedida e a tabela tem o mesmo número de linhas, o arquivo é ignorado (`skipped`). `--force` recarrega. Se algo falha, a transação reverte (tabela intacta) e `raw.ingestion_runs` registra `failed` com a mensagem (o registro de início/fim usa transação própria). **Consequência:** rodar duas vezes nunca duplica; um arquivo alterado substitui o anterior (carga completa, sem incremental, adequada a dataset estático). Testado em `tests/integration/test_load_raw.py`.

## 6. Tratamento de nulos e anomalias
- Texto vazio vira `NULL` no staging (`nullif(trim(x), '')`); cidades e status vão para minúsculas.
- **Dados brutos não são "consertados"**: anomalias viram testes (aviso até um limite, erro acima) e métricas as ignoram explicitamente. Exemplo: envio antes da compra (166 pedidos) mantém o timestamp nos fatos, mas a duração é `NULL` e fica fora das médias.
- Produto sem categoria → `unknown`; categoria sem tradução → nome em português.
- `review_id` não é único → chave sintética `md5(review_id|order_id)`; pedido com várias avaliações usa a mais recente.
- Limiares de aviso/erro ficam no próprio teste (`config(warn_if, error_if)`), de modo que o pipeline **falha de verdade** se a qualidade piorar muito. Verificado injetando um preço negativo: `dbt build` saiu com código 1 e os modelos seguintes foram pulados.

## 7. Definição de atraso
Entregue **com data de entrega** e `data de entrega > data estimada`, comparando **datas** (não horários). A estimativa vem sempre às 00:00:00; comparar timestamps classificaria como atrasada uma entrega às 15h do próprio dia estimado. Pedidos não entregues não são atraso (têm a faixa `not_delivered`). Os 8 pedidos "delivered" sem data não entram no denominador. **Consequência:** a taxa de atraso (6,77%) é conservadora e reproduzível.

## 8. Receita
Receita = preço dos itens de pedidos que não são `canceled` nem `unavailable`; frete é separado. Pedidos em andamento (`shipped`, `invoiced`…) contam: a venda foi feita. **Consequência:** a receita do dashboard (R$ 13,49 mi) é menor que a soma bruta (R$ 13,59 mi). Ambas existem no mart (`products_revenue` e `gross_products_value`).

## 9. Marts com medidas aditivas
Os marts guardam somas e contagens, não médias. O dashboard calcula razões depois de aplicar filtros, o que mantém as médias corretas ao filtrar por período, UF ou status. **Consequência:** as queries do dashboard têm algumas divisões, mas nenhuma regra de negócio nem join entre tabelas.

## 10. Testes sem pacotes externos
Os testes genéricos extras (`non_negative`, `positive`, `unique_combination`) estão em `macros/generic_tests.sql`. **Consequência:** `dbt build` roda offline, sem `dbt deps`.

## 11. Versão local é o caminho principal
O recrutador precisa executar o projeto sem conta de nuvem. Só o PostgreSQL usa Docker; Python/dbt/Streamlit rodam em venv. AWS S3 e PySpark **não foram implementados** (veja o roadmap): o dataset cabe em memória e Spark não se justifica; incluir só para constar no README contradiria o critério de não afirmar o que não existe.

## 12. CI com dataset sintético
O dataset real não é versionado (licença CC BY-NC-SA, uso não comercial). O CI gera um dataset sintético determinístico (`scripts/generate_sample_data.py`) e executa o pipeline completo e todos os testes dbt nele. **Consequência:** o CI valida o código e as regras, não os números reais; estes estão em `docs/data_quality.md`, de uma execução local.

## 13. Limitações do dataset histórico
Dados de 2016 a 2018, anonimizados, sem atualização; sem abandono de carrinho, recomendações ou atendimento; sem quantidade por item (cada linha é uma unidade); avaliações pertencem ao pedido; coordenadas por prefixo de CEP, então distâncias são aproximadas. Os resultados descrevem o passado deste marketplace e não devem ser generalizados.

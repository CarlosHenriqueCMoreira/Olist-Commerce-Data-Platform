# Olist Commerce Data Platform

[![CI](https://github.com/CarlosHenriqueCMoreira/Olist-Commerce-Data-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/CarlosHenriqueCMoreira/Olist-Commerce-Data-Platform/actions/workflows/ci.yml)

Plataforma de dados **end-to-end** construída sobre o dataset público de e-commerce da Olist. Ela carrega os CSVs brutos num PostgreSQL, transforma os dados em camadas (`raw → staging → intermediate → marts`) com dbt, valida a qualidade com 122 testes automáticos, orquestra tudo com Airflow e expõe as respostas num dashboard Streamlit.

> **Pergunta de negócio:** como a operação de vendas e entrega da Olist influencia o faturamento e a satisfação dos clientes?

## Sumário

1. [Visão geral](#1-visão-geral)
2. [Stack: o que foi usado e por quê](#2-stack-o-que-foi-usado-e-por-quê)
3. [Arquitetura e fluxo dos dados](#3-arquitetura-e-fluxo-dos-dados)
4. [Estrutura do repositório](#4-estrutura-do-repositório)
5. [Como executar](#5-como-executar)
6. [Configuração](#6-configuração)
7. [Ingestão em Python](#7-ingestão-em-python)
8. [Modelagem com dbt](#8-modelagem-com-dbt)
9. [Qualidade de dados e testes](#9-qualidade-de-dados-e-testes)
10. [Orquestração com Airflow](#10-orquestração-com-airflow)
11. [Dashboard](#11-dashboard)
12. [CI/CD e qualidade de código](#12-cicd-e-qualidade-de-código)
13. [Resultados reais](#13-resultados-reais)
14. [O que foi verificado e o que não foi](#14-o-que-foi-verificado-e-o-que-não-foi)
15. [Limitações](#15-limitações)
16. [Roadmap](#16-roadmap)
17. [Documentação adicional](#17-documentação-adicional)
18. [Dados e licença](#18-dados-e-licença)

---

## 1. Visão geral

A Olist é uma empresa brasileira que conecta vendedores a canais de venda e oferece soluções de operação, logística e gestão para e-commerce. O dataset público tem cerca de **100 mil pedidos (2016-2018)**, anonimizados, distribuídos em **9 arquivos CSV** (pedidos, itens, pagamentos, avaliações, produtos, clientes, vendedores, geolocalização e tradução de categorias).

O projeto responde a 10 perguntas de negócio:

| # | Pergunta | Onde |
|---|---|---|
| 1 | Como evoluem pedidos e receita no tempo? | `mart_sales_daily` |
| 2 | Quais categorias e produtos geram mais receita? | `mart_product_performance` |
| 3 | Quais vendedores têm melhor e pior desempenho? | `mart_seller_performance` |
| 4 | Qual o impacto do atraso na avaliação do cliente? | `mart_customer_experience` |
| 5 | Quais regiões têm mais pedidos e maior prazo de entrega? | `mart_regional_operations` |
| 6 | Qual o prazo médio entre compra, aprovação, envio e entrega? | `mart_delivery_performance` |
| 7 | Qual a taxa de pedidos entregues, cancelados ou indisponíveis? | `mart_sales_daily` |
| 8 | Qual a relação entre frete, distância e satisfação? | `mart_delivery_performance` |
| 9 | Quais categorias têm mais avaliações negativas? | `mart_product_performance` |
| 10 | Que indicadores monitorar para achar problemas operacionais? | [docs/metrics.md](docs/metrics.md) |

**Fora de escopo:** previsão de vendas, recomendação, abandono de carrinho (o dataset não tem esses dados) e dados em tempo real.

## 2. Stack: o que foi usado e por quê

### Linguagens
| Tecnologia | Uso |
|---|---|
| **Python 3.11** | ingestão, CLI, exportação, dashboard, testes, gerador de dados sintéticos |
| **SQL** (dialeto PostgreSQL + Jinja do dbt) | toda a transformação e as regras de negócio |
| **YAML** | configuração do dbt, Docker Compose, GitHub Actions, pre-commit |
| **Make** | comandos repetíveis (`make pipeline`, `make test`...) |

### Banco de dados e infraestrutura
| Tecnologia | Versão | Uso |
|---|---|---|
| **PostgreSQL** | 16 (imagem `postgres:16-alpine`) | armazena as 4 camadas em schemas separados (`raw`, `staging`, `intermediate`, `marts`) |
| **Docker / Docker Compose** | Compose v2 | sobe o PostgreSQL com volume persistente, healthcheck e porta só em `127.0.0.1`; sobe o Airflow no profile opcional |

### Ingestão
| Biblioteca | Versão testada | Uso |
|---|---|---|
| **psycopg2-binary** | 2.9.13 | driver; `COPY ... FROM STDIN` para carga rápida (1 milhão de linhas de geolocalização em ~1,2 s) |
| **SQLAlchemy** | 2.1.4 | engine, conexões, transações e DDL da tabela de controle |
| **python-dotenv** | 1.2.4 | leitura do `.env` |
| `csv`, `hashlib`, `argparse` (stdlib) | n/a | leitura de CSV, SHA-256 e a CLI `python -m src.cli` |

### Transformação e qualidade
| Ferramenta | Versão testada | Uso |
|---|---|---|
| **dbt Core** | 1.12.5 | modelos, testes, documentação, grafo de dependências |
| **dbt-postgres** | 1.11.0 | adaptador do PostgreSQL |
| **Macros próprias** | n/a | `non_negative`, `positive`, `unique_combination` (testes genéricos), `days_between`, `days_between_valid`, `haversine_km`, `clean_text`, `clean_lower`, `generate_schema_name`. Sem `dbt_utils`: roda offline, sem `dbt deps` |
| **pytest** | 9.1.1 | testes unitários e de integração em Python |

### Orquestração
| Ferramenta | Versão | Uso |
|---|---|---|
| **Apache Airflow** | 2.10.5 (imagem `apache/airflow:2.10.5-python3.11`) | DAG `olist_pipeline` com 8 tasks (`BashOperator`), retries e timeouts |

### Dashboard
| Biblioteca | Versão testada | Uso |
|---|---|---|
| **Streamlit** | 1.65.0 | app, filtros, abas, cache de queries |
| **Plotly Express** | 7.1.0 | gráficos |
| **pandas** | 3.0.6 | resultado das queries no dashboard e exportação dos marts para CSV |

### Qualidade de código e CI/CD
| Ferramenta | Versão testada | Uso |
|---|---|---|
| **Ruff** | 0.16.10 | lint (regras `E, F, I, B, UP`) e ordenação de imports |
| **Black** | 26.10.0 | formatação (linha de 100 colunas) |
| **pre-commit** | instalado | ganchos de ruff, black, YAML, arquivos grandes, espaços finais |
| **GitHub Actions** | `checkout@v4`, `setup-python@v5` | CI com serviço PostgreSQL, lint, pytest e `dbt build` completo |

> Versões "testadas" são as do ambiente onde o projeto foi validado. O `requirements.txt` usa limites mínimos (`dbt-core>=1.10`, `streamlit>=1.50` etc.).

### O que **não** foi usado
AWS S3 / `boto3`, PySpark / Databricks e Terraform (extensão opcional do plano, **não implementada**), `dbt_utils` e qualquer serviço de nuvem. O projeto roda 100% local.

## 3. Arquitetura e fluxo dos dados

```
CSVs Olist (data/raw)
   │  validação: existência, colunas, vazio, nº de linhas, SHA-256
   ▼
Python ─ COPY ─▶  PostgreSQL schema raw   (tudo em text + source_file + ingested_at)
                     │
                     ▼
              dbt staging  (views)         nomes, tipos, limpeza
                     ▼
              dbt intermediate (tables)    regras de negócio, métricas de tempo, flags, distância
                     ▼
              dbt marts (tables)           dim_* · fct_* · mart_*
                     ├──▶ Streamlit + Plotly (dashboard/queries/*.sql)
                     └──▶ data/exports/*.csv

 Transversais: dbt tests (122) · Airflow DAG · GitHub Actions
```

Diagrama Mermaid completo e tabela de grãos dos marts: [docs/architecture.md](docs/architecture.md).

| Camada | Schema | Materialização | Responsabilidade |
|---|---|---|---|
| Raw | `raw` | tabela (Python) | cópia fiel dos CSVs; auditoria e reprocessamento |
| Staging | `staging` | view | padroniza `snake_case`, converte tipos, vazio vira `NULL`; sem regra de negócio |
| Intermediate | `intermediate` | tabela | concentra as regras: atraso, receita, tempos, distância |
| Marts | `marts` | tabela | modelos prontos para consumo |

## 4. Estrutura do repositório

```
├── README.md  LICENSE  Makefile  compose.yaml  pyproject.toml  requirements.txt
├── .env.example               # variáveis (sem segredos); .env não é versionado
├── .pre-commit-config.yaml
├── .github/workflows/ci.yml   # CI
├── data/
│   ├── raw/                   # CSVs originais (ignorados pelo git)
│   ├── exports/               # marts em CSV + manifest.json (ignorado)
│   └── README.md              # como obter os dados
├── docker/postgres/init/      # cria os 4 schemas no primeiro start
├── ingestion/
│   ├── config.py              # caminhos, contrato de colunas dos 9 arquivos, conexão
│   ├── validate_files.py      # validação + checksum
│   ├── load_raw.py            # carga idempotente
│   ├── metadata.py            # raw.ingestion_runs
│   └── download.py            # download opcional via CLI do Kaggle
├── src/
│   ├── cli.py                 # python -m src.cli {check-files,validate,load,export}
│   └── export.py              # marts → CSV
├── dbt_project/
│   ├── dbt_project.yml  profiles.yml.example
│   ├── macros/                # helpers e testes genéricos
│   ├── models/{staging,intermediate,marts}/
│   └── tests/                 # 17 testes singulares (negócio + reconciliação)
├── airflow/
│   ├── Dockerfile
│   └── dags/olist_pipeline.py
├── dashboard/
│   ├── app.py  data.py
│   └── queries/*.sql          # 1 query por visual, cada uma cita o mart de origem
├── scripts/generate_sample_data.py   # dataset sintético para CI/demo
├── tests/{unit,integration}/  # pytest
├── docs/                      # charter, arquitetura, dicionário, métricas, qualidade, decisões
└── notebook/                  # exploração anterior (não faz parte do pipeline)
```

## 5. Como executar

Requisitos: **Python 3.11+**, **Docker** e **make**.

```bash
git clone https://github.com/CarlosHenriqueCMoreira/Olist-Commerce-Data-Platform.git
cd olist-commerce-data-platform

make setup      # cria .venv, instala dependências, copia .env e dbt_project/profiles.yml

# Dados (escolha um):
#  a) baixe os 9 CSVs do Kaggle para data/raw/  (veja data/README.md)
#  b) sem baixar nada: make sample-data && export OLIST_DATA_DIR=data/sample

make pipeline   # up → ingest → dbt-build → export
make dashboard  # http://localhost:8501
```

### Comandos

| Comando | O que faz |
|---|---|
| `make setup` | venv, dependências, `.env`, `profiles.yml` |
| `make up` / `make down` | sobe (espera o healthcheck) / para o PostgreSQL |
| `make logs` / `make psql` | logs / shell SQL dentro do container |
| `make validate` | tamanho, linhas e checksum de cada CSV |
| `make ingest` | carga idempotente no `raw` |
| `make dbt-build` | `dbt build`: constrói modelos **e** roda todos os testes |
| `make dbt-docs` | catálogo e linhagem do dbt |
| `make export` | marts → `data/exports/*.csv` |
| `make pipeline` | `up` + `ingest` + `dbt-build` + `export` |
| `make test` | pytest |
| `make lint` / `make format` | ruff + black (verificar / corrigir) |
| `make sample-data` | gera dataset sintético em `data/sample` |
| `make clean` | **apaga o volume do banco** (pede confirmação) |

CLI direta: `python -m src.cli check-files | validate | load [--force] | export`.

## 6. Configuração

Copie `.env.example` para `.env`:

| Variável | Padrão | Descrição |
|---|---|---|
| `POSTGRES_HOST` | `localhost` | host do banco |
| `POSTGRES_PORT` | `5433` | porta no host (5433 evita conflito com um Postgres local na 5432) |
| `POSTGRES_DB` | `olist` | banco |
| `POSTGRES_USER` | `olist` | usuário |
| `POSTGRES_PASSWORD` | `change_me` | **troque**; o `compose.yaml` se recusa a subir sem ela |
| `OLIST_DATA_DIR` | `data/raw` | pasta dos CSVs |
| `OLIST_RAW_SCHEMA` | `raw` | só para testes (a suíte usa `raw_test` e nunca toca nos dados reais) |

Variáveis ausentes geram erro claro (`ConfigError`) em vez de falha obscura. O dbt lê as mesmas variáveis via `env_var()` em `profiles.yml`.

## 7. Ingestão em Python

1. **Valida** cada arquivo: existe, não está vazio, tem exatamente as colunas esperadas, possui linhas. Conta registros com `csv` (não linhas físicas: comentários de avaliações têm quebras de linha) e calcula **SHA-256**. Reúne *todos* os erros antes de falhar. Aceita BOM UTF-8.
2. **Registra** a execução em `raw.ingestion_runs` (`run_id`, `source_file`, `file_checksum`, `row_count`, `started_at`, `finished_at`, `status`, `error_message`), uma linha por arquivo e execução, em transação própria para sobreviver a falhas.
3. **Carrega** numa única transação por arquivo: `COPY` para tabela temporária → `TRUNCATE` → `INSERT ... SELECT` (adicionando `source_file` e `ingested_at`) → confere se as linhas carregadas batem com as contadas. Qualquer erro reverte tudo.
4. **Idempotência:** se o checksum é igual ao da última carga bem-sucedida e a tabela tem as mesmas linhas, o arquivo é `skipped`. `--force` recarrega.

## 8. Modelagem com dbt

**31 modelos:** 9 staging (views), 7 intermediate e 15 marts (tabelas).

**Staging:** `stg_orders`, `stg_order_items`, `stg_order_payments`, `stg_order_reviews` (chave sintética `md5(review_id|order_id)`, pois `review_id` não é único), `stg_products` (corrige `lenght`→`length`), `stg_customers`, `stg_sellers`, `stg_geolocation`, `stg_product_category_translation`.

**Intermediate:**
| Modelo | Papel |
|---|---|
| `int_zip_locations` | um ponto por prefixo de CEP (média das coordenadas dentro do Brasil) |
| `int_order_payments_agg` | total, nº de pagamentos, parcelas máximas, método principal |
| `int_order_reviews_latest` | avaliação mais recente por pedido |
| `int_order_items_enriched` | item + categoria + vendedor + distância (haversine) |
| `int_orders_enriched` | pedido com cliente, itens, pagamento, avaliação, durações e flags (`is_delivered`, `is_cancelled`, `is_delayed`, `delay_bucket`, `distance_bucket`) |
| `int_seller_orders` / `int_product_items` | bases das métricas de vendedor e de produto |

**Marts:** dimensões `dim_date`, `dim_customer`, `dim_product`, `dim_seller`, `dim_location`; fatos `fct_orders`, `fct_order_items`, `fct_payments`, `fct_reviews`; negócio `mart_sales_daily`, `mart_delivery_performance`, `mart_regional_operations`, `mart_seller_performance`, `mart_product_performance`, `mart_customer_experience`.

Os marts de negócio guardam **medidas aditivas** (somas e contagens). Médias e taxas são calculadas depois dos filtros, o que as mantém corretas.

**Regras principais** (detalhe em [docs/metrics.md](docs/metrics.md)):
- **Atraso** = entregue, com data de entrega, e *data* de entrega > *data* estimada. Pedido não entregue não é atraso.
- **Receita** = preço dos itens de pedidos que não são cancelados nem indisponíveis; **frete é separado**.
- Duração com ordem temporal impossível vira `NULL` e fica fora das médias; o timestamp bruto permanece.
- A nota pertence ao pedido; com várias avaliações, vale a mais recente.

## 9. Qualidade de dados e testes

| Camada de teste | Qtde | O que verifica |
|---|---|---|
| dbt genéricos | 105 | `unique`, `not_null`, `relationships`, `accepted_values`, `non_negative`, `positive`, `unique_combination` |
| dbt singulares: negócio | 11 | ordem das datas, entregue com data, cancelado nunca entregue, pagamentos vs. pedido, atraso só em entregues |
| dbt singulares: reconciliação | 6 | pedidos, itens, preço, frete, pagamentos e avaliações iguais entre raw, fatos e marts (garante que os joins não multiplicam receita) |
| pytest | 19 + 1 | validação de arquivos, checksum, configuração, erro de conexão, **idempotência (banco real)**, rollback, CLI, integridade do DAG |

Testes que refletem anomalias conhecidas da origem usam `warn_if` / `error_if`: avisam no volume esperado e **falham se piorar**. Todas as anomalias encontradas e seu tratamento estão em [docs/data_quality.md](docs/data_quality.md).

## 10. Orquestração com Airflow

```
check_files → validate_sources → load_raw → dbt_staging → dbt_intermediate → dbt_marts → dbt_tests → export_dashboard_data
```

- `BashOperator` chamando um **venv do projeto** dentro da imagem (evita conflito de dependências com o Airflow).
- `retries=2`, `retry_delay=1 min`, `execution_timeout=20 min`, `max_active_runs=1`, sem agenda (dataset histórico).
- Credenciais só por variáveis de ambiente. `dbt_tests` com status `error` falha a task e impede a exportação.
- Duração por task e logs são os do próprio Airflow; a task `load_raw` imprime linhas carregadas por tabela.

```bash
docker compose --profile airflow up -d --build
docker compose logs airflow | grep -i password   # senha do admin gerada
# http://localhost:8080 → olist_pipeline → Trigger
```

## 11. Dashboard

Seis abas, todas alimentadas por `dashboard/queries/*.sql` contra os **marts** (cada arquivo indica o mart de origem):

| Aba | Conteúdo | Mart |
|---|---|---|
| Visão executiva | pedidos, receita de produtos, receita de frete, ticket médio, taxas de entrega e de atraso, nota média, prazo; série diária/mensal; pedidos por status | `mart_sales_daily` |
| Operação | tempo por etapa, regiões com maior atraso, prazo por UF, cancelados por mês | `mart_delivery_performance`, `mart_regional_operations`, `mart_sales_daily` |
| Experiência e frete | nota por situação de entrega; frete, prazo e nota por distância | `mart_customer_experience`, `mart_delivery_performance` |
| Vendedores | melhores, piores e maiores receitas | `mart_seller_performance` |
| Produtos | receita por categoria, categorias com mais avaliações baixas | `mart_product_performance` |
| Sobre os dados | período, anonimização, limitações, aviso de correlação ≠ causalidade | |

Filtros: período, UF, status, categoria, vendedor e granularidade. UF e status afetam vendas e operação; categoria afeta a aba Produtos; vendedor afeta a aba Vendedores (indicado na barra lateral).

## 12. CI/CD e qualidade de código

O workflow `.github/workflows/ci.yml` roda em `push` e `pull_request`: sobe PostgreSQL 16 como serviço, instala dependências, executa **ruff** e **black --check**, **pytest**, gera o dataset sintético, roda a ingestão **duas vezes** (prova de idempotência), executa `dbt build` completo e exporta os marts. Qualquer falha reprova o workflow.

O dataset real não é versionado (licença não comercial), então o CI usa dados **sintéticos** gerados por `scripts/generate_sample_data.py` (determinístico, mesmo formato dos CSVs). Ele valida código e regras, não os números reais. Para ativar o pre-commit: `pre-commit install`.

## 13. Resultados reais

Execução local no dataset completo (2026-10-08):

| Indicador | Valor |
|---|---|
| Pedidos / período | 99.441, compras de 04/09/2016 a 17/10/2018 |
| Receita de produtos / frete | R$ 13,49 mi / R$ 2,24 mi (sem cancelados e indisponíveis) |
| Ticket médio | R$ 137,41 |
| Entregues / cancelados | 97,02% / 0,63% |
| Taxa de atraso | 6,77% |
| Prazo médio de entrega | 12,6 dias |
| Nota média, no prazo → atraso 8+ dias | 4,29 → 1,70 |
| Frete médio, < 100 km → > 2.000 km | R$ 13,37 → R$ 39,81 |
| UFs com maior atraso | AL (21,4%), MA (17,4%), SE (15,2%) |
| Categorias com maior receita | health_beauty, watches_gifts, bed_bath_table |
| `dbt build` | **147 PASS, 6 WARN, 0 ERROR** em ~6 s |

Atraso e nota baixa andam juntos, mas isso é correlação.

## 14. O que foi verificado e o que não foi

**Executado e confirmado:** ingestão completa e repetida (idempotente), `dbt build` no dataset real e no sintético, falha proposital com dado inválido (código de saída 1, modelos seguintes pulados), pytest, ruff, black, dashboard via `streamlit.testing` (com e sem filtros), YAMLs, e o DAG carregando no Airflow 2.10.5 com a ordem correta.

**Não testado:** `docker compose up` e a imagem/execução do Airflow em container (o Docker não estava ativo no ambiente de desenvolvimento; o `compose.yaml` só teve a sintaxe validada); o workflow do GitHub Actions rodando na nuvem (validado só o YAML e os mesmos comandos localmente).

## 15. Limitações

- Dataset histórico e anonimizado; sem abandono de carrinho, recomendações ou atendimento.
- Sem quantidade por item nem custo (não há margem). Distâncias aproximadas (centróide por prefixo de CEP).
- Nota por categoria ou vendedor é atribuição aproximada (a nota é do pedido).
- Os limiares de aviso/erro dos testes foram calibrados nesta execução.

## 16. Roadmap

- [ ] AWS S3 (`boto3`) e transformação alternativa em PySpark (**não implementado**; o dataset não exige Spark)
- [ ] Screenshots do dashboard e do DAG em `docs/images/`
- [ ] Marketing Funnel Dataset da Olist
- [ ] Release `v1.0.0` após uma execução limpa seguindo só este README

## 17. Documentação adicional

[Charter](docs/project-charter.md) · [Arquitetura](docs/architecture.md) · [Dicionário de dados e ER](docs/data_dictionary.md) · [Métricas](docs/metrics.md) · [Qualidade de dados](docs/data_quality.md) · [Decisões técnicas](docs/decisions.md)

## 18. Dados e licença

- Dados: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle), licença [**CC BY-NC-SA 4.0**](https://creativecommons.org/licenses/by-nc-sa/4.0/): uso **não comercial**, com atribuição. Os CSVs não estão neste repositório. Empresa: [olist.com](https://olist.com).
- Código: [MIT](LICENSE).

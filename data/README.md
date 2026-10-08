# Dados

Os CSVs **não são versionados** (dataset da Olist, licença **CC BY-NC-SA 4.0**: uso não comercial, com atribuição e mesma licença).

## Como obter

1. Acesse o [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) no Kaggle (conta gratuita necessária).
2. Clique em **Download** e extraia o zip.
3. Coloque os **9 arquivos** em `data/raw/`:

```
olist_customers_dataset.csv          olist_order_reviews_dataset.csv
olist_geolocation_dataset.csv        olist_orders_dataset.csv
olist_order_items_dataset.csv        olist_products_dataset.csv
olist_order_payments_dataset.csv     olist_sellers_dataset.csv
product_category_name_translation.csv
```

Alternativa com a CLI do Kaggle (`pip install kaggle`, token em `~/.kaggle/kaggle.json`): `python -m ingestion.download`.

4. Confira: `make validate` (mostra tamanho, linhas e checksum de cada arquivo).

## Sem baixar nada

`make sample-data` gera um dataset **sintético** em `data/sample/` (mesmo formato, valores fictícios). Use `OLIST_DATA_DIR=data/sample` para rodar o pipeline com ele. É o que o CI usa. Não use esses números para análise.

## Pastas

| Pasta | Conteúdo |
|---|---|
| `data/raw/` | CSVs originais (ignorados pelo git) |
| `data/sample/` | dataset sintético gerado (ignorado) |
| `data/exports/` | marts exportados em CSV pela última execução (ignorado) |

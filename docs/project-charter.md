# Project charter: Olist Commerce Data Platform

## 1. Problema de negócio

> Como a operação de vendas e entrega da Olist influencia o faturamento e a satisfação dos clientes?

A Olist conecta vendedores a canais de venda e oferece operação, logística e gestão para e-commerce. Os dados de pedidos chegam espalhados em nove arquivos CSV, sem garantias de qualidade. Este projeto os transforma em dados confiáveis e em respostas analíticas para as equipes de **operações, vendas e gestão**.

## 2. Perguntas que a plataforma responde

| # | Pergunta | Onde é respondida |
|---|---|---|
| 1 | Como evoluem os pedidos e a receita ao longo do tempo? | `mart_sales_daily` (aba Visão executiva) |
| 2 | Quais categorias e produtos geram mais receita? | `mart_product_performance` (aba Produtos) |
| 3 | Quais vendedores têm melhor e pior desempenho? | `mart_seller_performance` (aba Vendedores) |
| 4 | Qual é o impacto de atrasos na avaliação dos clientes? | `mart_customer_experience` (aba Experiência e frete) |
| 5 | Quais regiões têm mais pedidos e maior tempo de entrega? | `mart_regional_operations` (aba Operação) |
| 6 | Qual é o prazo médio entre compra, aprovação, envio e entrega? | `mart_delivery_performance` (aba Operação) |
| 7 | Qual é a taxa de pedidos entregues, cancelados ou indisponíveis? | `mart_sales_daily` |
| 8 | Qual é a relação entre frete, distância e satisfação? | `mart_delivery_performance` (aba Experiência e frete) |
| 9 | Quais categorias têm mais avaliações negativas? | `mart_product_performance` |
| 10 | Que indicadores monitorar para detectar problemas operacionais? | [docs/metrics.md](metrics.md), seção "Indicadores de monitoramento" |

## 3. Fora do escopo

- previsão de vendas;
- recomendação automática de produtos;
- abandono de carrinho, recomendações ou atendimento (**o dataset não contém esses dados**);
- dados em tempo real (o dataset é histórico);
- integração com sistemas privados da Olist.

Extensão opcional, não implementada: AWS S3 e PySpark (veja o roadmap no README).

## 4. Definição de sucesso

O projeto é bem-sucedido quando:

1. qualquer pessoa clona o repositório e reproduz o resultado seguindo apenas o README;
2. o pipeline carrega os dados sem duplicar, constrói as camadas e **falha** quando regras importantes são violadas;
3. as dez perguntas acima têm resposta rastreável até um mart;
4. as métricas têm definição escrita (`docs/metrics.md`) e as decisões e limitações estão documentadas;
5. nada é afirmado que não esteja implementado.

## 5. Fonte e licença

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), Kaggle, **CC BY-NC-SA 4.0**. Uso restrito a portfólio pessoal e educacional; não usar para produto comercial sem verificar a licença.

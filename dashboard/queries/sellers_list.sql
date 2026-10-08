select seller_id from marts.mart_seller_performance
group by seller_id order by sum(products_revenue) desc nulls last limit 300

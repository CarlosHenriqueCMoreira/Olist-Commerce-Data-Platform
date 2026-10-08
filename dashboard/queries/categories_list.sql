select category_name from marts.mart_product_performance
group by category_name order by sum(revenue) desc nulls last

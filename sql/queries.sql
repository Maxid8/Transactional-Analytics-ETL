-- Which categories experience the most fraud, and what is the total financial loss due to fraud per category?
SELECT
	m.category,
	COUNT(m.category),
	SUM(t.amt)
FROM fact_transaction t
LEFT JOIN dim_merchant m ON t.merchant_id = m.merchant_id
WHERE t.is_fraud = 1
GROUP BY m.category 
ORDER BY COUNT(m.category) DESC;

-- What days of the week do fraudsters most often strike? Is there a detectable pattern on weekly transactions?
SELECT
    d.day_name,
    COUNT(t.is_fraud) 
FROM fact_transaction t 
LEFT JOIN dim_date d ON t.date_id = d.date_id
WHERE t.is_fraud = 1
GROUP BY d.day_name 
ORDER BY COUNT(t.is_fraud) DESC;

-- Which fraudulent transactions exceed the average transaction value for the given category?
SELECT
	t.transaction_id,
	m.merchant_name,
	m.category,
	t.date_id,
	t.amt,
	ROUND(AVG(t.amt) OVER (PARTITION BY m.category),2)
FROM fact_transaction t
LEFT JOIN dim_merchant m ON t.merchant_id = m.merchant_id
WHERE t.is_fraud = 1 AND  t.amt > (SELECT AVG(amt) FROM fact_transaction)
ORDER BY m.category;

-- What age groups and genders are most affected by fraud, and what is their average transaction size?
SELECT
	(FLOOR(EXTRACT(YEAR FROM AGE(c.dob))/10))*10 age_group,
	c.gender,
	COUNT(*) fraud_count,
    ROUND(AVG(t.amt), 2) avg_fraud_amount
FROM fact_transaction t
LEFT JOIN dim_customer c ON t.customer_id = c.customer_id
WHERE t.is_fraud = 1
GROUP BY age_group, c.gender
ORDER BY fraud_count DESC;

-- How did the total financial loss from fraud accumulate day by day over time?
WITH daily_loss AS (
    SELECT
        date_id AS day,
        SUM(amt) AS daily_total
    FROM fact_transaction
    WHERE is_fraud = 1
    GROUP BY date_id
)
SELECT
    "day",
    daily_total,
    SUM(daily_total) OVER (ORDER BY "day") cumulative_loss
FROM daily_loss
ORDER BY "day";

-- Who are the merchants whose number of transactions reaches a minimum value (e.g. at least 50 transactions), but whose fraud rate is exceptionally high (>5%)?
SELECT
    m.merchant_name,
    SUM(t.is_fraud) AS sum_of_merch_fraud,
    COUNT(t.transaction_id) AS sum_of_transactions,
    ROUND(SUM(t.is_fraud)::decimal / COUNT(*), 4) AS fraud_rate
FROM fact_transaction t
LEFT JOIN dim_merchant m ON t.merchant_id = m.merchant_id
GROUP BY m.merchant_name
HAVING COUNT(t.transaction_id) >= 50
   AND SUM(t.is_fraud)::decimal / COUNT(*) > 0.05
ORDER BY fraud_rate DESC;
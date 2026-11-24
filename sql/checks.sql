-- Requêtes de contrôle sur le data warehouse (RDS PostgreSQL)

-- 1. Volumétrie
SELECT 'cities' AS t, COUNT(*) FROM cities
UNION ALL SELECT 'hotels', COUNT(*) FROM hotels;

-- 2. Top 5 destinations météo (7 prochains jours)
SELECT city, ROUND(temp_max_mean::numeric, 1) AS temp_max, ROUND(rain_mm_total::numeric, 1) AS pluie_mm,
       ROUND(clouds_mean::numeric) AS nuages_pct, ROUND(weather_score::numeric, 2) AS score
FROM cities ORDER BY weather_score DESC LIMIT 5;

-- 3. Top 20 hôtels dans ces 5 villes (au moins 50 avis)
SELECT c.city, h.name, h.score, h.n_reviews
FROM hotels h JOIN cities c USING (city_id)
WHERE c.city_id IN (SELECT city_id FROM cities ORDER BY weather_score DESC LIMIT 5)
  AND h.n_reviews >= 50
ORDER BY h.score DESC, h.n_reviews DESC
LIMIT 20;

-- 4. Qualité : hôtels sans note
SELECT city, name FROM hotels WHERE score IS NULL;

# Script

Script — это проект на Python, который помогает найти оптимальное время для покупки туров по самым низким ценам. Проект автоматически собирает данные о ценах на туры с различных агрегаторов, сохраняет их в базе данных PostgreSQL для анализа истории и использует машинное обучение для прогнозирования наиболее выгодных временных периодов.

---

## Основные возможности

- **Парсинг данных**: Используется библиотека `BeautifulSoup` для сбора информации о ценах на туры с популярных агрегаторов.
- **Хранение истории**: Все собранные данные сохраняются в базе данных PostgreSQL, что позволяет отслеживать динамику цен.
- **Анализ данных**: Благодаря `NumPy` и `scikit-learn`, проект анализирует историю цен и строит прогнозы о лучших периодах для покупки туров.
- **Интуитивный вывод**: Результаты анализа предоставляются в удобном формате, помогая пользователям принимать обоснованные решения.

---

## Технологии

- **Python**: Основной язык программирования.
- **BeautifulSoup**: Для парсинга веб-страниц и извлечения данных о ценах.
- **NumPy**: Для эффективной работы с числовыми данными.
- **PostgreSQL**: Для хранения истории цен и обеспечения надежности данных.
- **scikit-learn**: Для построения моделей машинного обучения и анализа данных.

---
![image](https://github.com/user-attachments/assets/7f936901-dccc-4472-8158-8e3d34a2efe1)

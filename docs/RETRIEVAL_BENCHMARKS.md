| Вопрос | Метод | Top1 type | Rerank score | Preview |
|---|---|---|---:|---|
| Платежи за месяц по клиентам | rerank | question_sql | 7.385 | Q: Пользователи отдела Продажи за последний месяц
A: SELECT u.login, u.email, u.... |
| Покажи все платежи | rerank | question_sql | 8.319 | Q: Покажи всех пользователей системы
A: SELECT id, login, email, surname, firstn... |
| Пользователи системы | rerank | documentation | 8.805 | 
        DocStructureSchema - система управления документами и пользователями
  ... |
| Покажи таблицы с платежами | rerank | question_sql | 7.863 | Q: Покажи активных пользователей системы
A: SELECT id, login, email, surname, fi... |
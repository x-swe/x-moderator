# Bot Endpoint [v1]

#### Location: `/api/v1/bot`

Send commands or tasks to the Selenium Bot(s).




## DELETE /api/v1/bot/task/{id}

Remove an entry from the database log.

### URI Parameters:
None

### Query Parameters:
| Name               | Optional  | Type      | Limit     | Description                                        |
|--------------------|-----------|-----------|-----------|----------------------------------------------------|
| `limit`            | Yes       | uint32    | 0..500    | Pagination: Number of results to return per page.  |
| `offset`           | Yes       | uint32    | >= 1      | Pagination: Page number offset.                    |



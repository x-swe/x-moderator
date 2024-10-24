# Log Endpoint [v1]

#### Location: `/api/v1/log`

Database logging.


## GET /api/v1/log

Fetch logs from the database.

### URI Parameters:
None

### Query Parameters:
| Name               | Optional  | Type      | Limit     | Description                                        |
|--------------------|-----------|-----------|-----------|----------------------------------------------------|
| `limit`            | Yes       | uint32    | 0..500    | Pagination: Number of results to return per page.  |
| `offset`           | Yes       | uint32    | >= 1      | Pagination: Page number offset.                    |


## GET /api/v1/log/{id}

Fetch a specific log by ID from the database.

### URI Parameters:
- `{id}` = The ID of the entry

### Query Paramters:
None



## POST /api/v1/log/{component}

Save an entry to the database log.

### URI Parameters:
- Component

### Query Parameters:
-


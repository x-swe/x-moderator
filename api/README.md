# x-moderator-api


## Environment Variables

| Name                | Default                         | Optional | Description                                                                            |
|---------------------|---------------------------------|----------|----------------------------------------------------------------------------------------|
| QDRANT_URL          | http://x-moderator-qdrant:6333  | Yes      | The URL of the Qdrant vector database.                                                 |
| QDRANT_API_KEY      |                                 | Yes      | The Qdrant vector database API key (if secured).                                       |
| BYPASS_MODERATORS   | 0                               | Yes      | If set to `1`, the moderation will ignore moderator Posts on X and not moderate them.  |
| DISABLE_VIOLATION   | 0                               | Yes      | If set to `1`, the user's violation column will not be appended to.                    |
| VIOLATION_THRESHOLD | 3                               | Yes      | The violation count the user hits before an action is taken.                           |
| VIOLATION_ACTION    | notify                          | Yes      | The action to be taken upon exceeding threshold ("notify_mods", "temp_ban", "ban")     |

> [!NOTE]
> The `VIOLATION_` env vars will be replaced with a json config of more robust rule configurations.
> Or this perhaps should be configured via web dashboard and stored as a JSON value in the metadata table.

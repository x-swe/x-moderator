# Logging

X-Moderator has internal and cross-service logging, internal logging is sent to `stdout`, where as cross-service logging is sent to `stdout` and captures any submissions sent via gRPC.




## Service Format

The following are valid root attributes:

| Key                         | Type          | Default Value | Description                                       |
|-----------------------------|---------------|---------------|---------------------------------------------------|
| `message`                   | string        |               | The message or message format (see `parameters`). |
| `level`                     | string        | `INFO`        | The logger level (see Logger Level below).        |
| `parameters`                | object        | {}            | Named parameters to pass in to the message.       |

### Logger Level Serialization
- `0` = DEBUG
- `1` = INFO
- `2` = WARNING
- `3` = ERROR


Simple log entry:
```json
{
	"message": "Hello world!"
}
```

More complex log entry:
```json
{
	"message": "A critical error occurred in ${server} on ${line}:${column}",
	"level": "ERROR",
	"parameters": {
		"server": "us-west-1",
		"line": 4,
		"column": 30
	}
}
```

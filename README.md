# X-Moderator

X-Moderator is a machine learning-driven moderation system for X Communities, automating post monitoring, moderation, and data management using a modular architecture built primarily in Rust. It cuts down manual moderation effort by quickly identifying and addressing rule-breaking issues or categorized text like spam or ads, while providing moderators with tools to oversee and adjust the process.

## How It Works

X-Moderator’s components work together to streamline moderation:

- **Bot**: Scans X Community posts in real-time via the X API and web scraping. It uses machine learning models to score posts for issues like spam or toxicity, stored as embeddings in Qdrant. If a post’s score exceeds a threshold (set in `moderation_categories`), the bot flags it, hides it, or bans the user, logging actions in MariaDB.
- **Backend**: The central hub, storing data in MariaDB and processing moderation logic. It receives bot actions via Valkey pub/sub, updates post statuses, and serves data to the frontend through REST APIs.
- **Frontend**: A web dashboard for moderators to view flagged posts, adjust thresholds, and review bans. Staff can manually add embeddings to Qdrant via the dashboard, improving model accuracy by labeling posts as positive or negative examples.
- **Migrator**: Ensures the MariaDB schema stays up-to-date, applying migrations for tables like `posts` and `user_bans`.
- **Common**: Shared utilities ensure consistency across components, like standardized data models.

**Interconnections**:
- The bot pushes moderation tasks (e.g., flagged posts) to the backend via Valkey pub/sub.
- The backend queries Qdrant for embeddings and updates MariaDB, then exposes data via REST APIs.
- The frontend pulls data from the backend APIs and sends staff inputs (e.g., new embeddings) back.

**Automated Reporting & Banning**:
- Posts are scored against `moderation_categories` (e.g., spam, weight 0.8, threshold 0.9).
- If a score exceeds the threshold, the bot triggers actions (e.g., `FLAG_POST`, `BAN_USER`) based on `action_type`.
- Bans are logged in `user_bans`, with appeal options stored in `appeals`.

**Staff-Added Embeddings**:
- Moderators use the frontend to label posts (e.g., “spam” or “safe”), creating new embeddings in Qdrant.
- These refine the bot’s models, boosting prediction accuracy for future posts.

## Key Features

- Real-time post analysis with machine learning.
- Automated flagging, hiding, or banning based on custom rules.
- Web dashboard for stats, settings, and manual overrides.
- Staff-driven embedding updates for improved accuracy.
- Scalable, modular design for easy expansion.
- Consideration: local model for embedding (all-mpnet-base-v2) 

## Setup

Use Docker for quick setup:

```sh
./docker-build-all.sh
./docker-start-all.sh
```

See component READMEs for manual setup or advanced configs.

### Requirements

- Docker
- X API key for bot access
- MariaDB, Qdrant, Valkey (set up via `migrator/docker-bootstrap.sh`)

## Components

| Component  | Purpose                                           |
|------------|---------------------------------------------------|
| migrator   | Updates database schema.                         |
| backend    | Manages data, logic, and APIs.                   |
| bot        | Monitors and moderates posts.                    |
| common     | Shared utilities across components.              |
| frontend   | Web interface for moderation control.            |

## Development

Docker mounts code for instant updates. Use scripts like `docker-build.sh` and `docker-run.sh` per component. Check READMEs for details.

## CI/CD

GitHub Actions handle:
- **Linting**: Checks scripts, code, and EditorConfig on push/pull requests.
- **Build/Test**: Builds and tests Docker images on `dev` and `master`.
- **Publish**: (Disabled) Prepares Docker Hub images and binaries.

Workflows run on custom runners with GitHub-hosted fallbacks.

## Contributing

Fork, edit, and submit a pull request. Keep code clean and modular.

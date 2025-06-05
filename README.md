# X-Moderator

X-Moderator is a machine learning-driven moderation solution for X Communities, automating post monitoring, moderation, and data management using a modular architecture. It cuts down manual moderation effort by quickly identifying and addressing rule-breaking issues or categorized text like `spam` or `ads`, while providing community moderators with tools to oversee and adjust the process.

## How It Works

X-Moderator’s components work together to streamline moderation:

- **Bot**: Scans X Community posts in real-time via the X API and web scraping.
- **Backend**: The central hub, storing data in MariaDB and processing moderation logic. It uses machine learning models to score posts for issues like spam or toxicity, stored as embeddings in Qdrant. If a post’s score exceeds a threshold (set in `moderation_categories`), the system will flags it, queue a bot action to hide the post/bans the user/etc. configurable actions and logged events. It receives bot actions via Valkey pub/sub, updates post statuses, and serves data to the frontend through REST APIs.
- **Dashboard**: The "frontend" web dashboard for moderators to view flagged posts, adjust thresholds, and review bans. Staff can manually add embeddings to Qdrant via the dashboard, improving model accuracy by labeling posts as positive or negative examples. The dashboard also acts as a place for users to appeal their bans.
- **Migrator**: Ensures the MariaDB schema stays up-to-date, applying migrations for tables like `posts` and `user_bans`.
- **Common**: Shared library across components, like standardized data models for the `backend`, `bot`, and `dashboard`.

**Interconnections**:
- The bot pushes moderation tasks (e.g., flagged posts) to the backend via Valkey pub/sub.
- The backend queries Qdrant for embeddings and updates MariaDB, then exposes data via REST APIs.
- The backend can also queue and push actions for the bot to execute via Valkey pub/sub.
- The frontend pulls data from the backend REST API and sends staff inputs (e.g., new embeddings) back.

**Automated Reporting & Banning**:
- Posts are scored against `moderation_categories` (e.g., spam, weight 0.8, threshold 0.9).
- If a score exceeds the threshold, the bot triggers actions (e.g., `FLAG_POST`, `BAN_USER`) based on `action_type`.
- Bans are logged in `user_bans`, with appeal options stored in `appeals`.

**Staff-Added Embeddings**:
- Moderators use the frontend to label posts (e.g., “spam” or “safe”), creating new embeddings in Qdrant (if permissions allow).
- These refine the bot’s classification of posts, boosting prediction accuracy for future posts.

## Key Features

- Real-time post analysis with machine learning.
- Automated flagging, hiding, or banning based on tunables.
- Web dashboard for stats, settings, and manual overrides.
- Staff-driven embedding updates for improved accuracy.
- Scalable, modular design for easy expansion.


## Components

| Component  | Purpose                                           |
|------------|---------------------------------------------------|
| migrator   | Updates database schema.                         |
| backend    | Manages data, logic, and APIs.                   |
| bot        | Monitors and moderates posts.                    |
| common     | Shared utilities across components.              |
| frontend   | Web interface for moderation control.            |

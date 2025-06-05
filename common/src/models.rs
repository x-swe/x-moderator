use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BotStatusEnum {
    BOT_STATUS_ONLINE,
    BOT_STATUS_BUSY,
    BOT_STATUS_OFFLINE,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BotStatus {
    pub bot_id: String,
    pub status: BotStatusEnum,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ActionEnum {
    ACTION_SCRAPE_COMMUNITY(String),
    ACTION_SCRAPE_PROFILE(String),
    ACTION_DELETE_POST(String),
    ACTION_BAN_USER(String, String), // community_id, user_id
    ACTION_REPLY_TO_POST(String, String), // post_id, reply_text
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub task_id: String,
    pub action: ActionEnum,
    pub priority: u8, // 0-255, lower is higher priority
    pub dry_run: bool,
    pub backend_id: String, // Identifies the requesting backend
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskResult {
    pub task_id: String,
    pub data: Option<serde_json::Value>,
    pub is_cancelled: bool,
    pub reason: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskCancellation {
    pub task_id: String,
    pub backend_id: String,
}
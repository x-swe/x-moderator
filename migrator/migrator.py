import os
import re
import time
import logging
import argparse
from typing import List, Dict, Optional
from datetime import datetime
from mysql.connector import Error, connect
from retrying import retry
from pathlib import Path
from names import ADJECTIVES, LAST_NAMES
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def strip_sql_comments(sql: str) -> str:
    """Remove SQL comments (-- and /* */) while preserving SQL structure."""
    result = []
    i = 0
    in_single_quote = False
    in_double_quote = False
    in_line_comment = False
    in_multi_comment = False

    while i < len(sql):
        char = sql[i]

        # Handle string literals
        if char == "'" and not in_double_quote and not in_line_comment and not in_multi_comment:
            in_single_quote = not in_single_quote
            result.append(char)
            i += 1
            continue
        if char == '"' and not in_single_quote and not in_line_comment and not in_multi_comment:
            in_double_quote = not in_double_quote
            result.append(char)
            i += 1
            continue

        # Skip if inside a string
        if in_single_quote or in_double_quote:
            result.append(char)
            i += 1
            continue

        # Handle line comments (--)
        if char == '-' and i + 1 < len(sql) and sql[i + 1] == '-' and not in_multi_comment:
            in_line_comment = True
            i += 2
            continue
        if in_line_comment and char == '\n':
            in_line_comment = False
            result.append(char)
            i += 1
            continue
        if in_line_comment:
            i += 1
            continue

        # Handle multi-line comments (/* */)
        if char == '/' and i + 1 < len(sql) and sql[i + 1] == '*' and not in_line_comment:
            in_multi_comment = True
            i += 2
            continue
        if in_multi_comment and char == '*' and i + 1 < len(sql) and sql[i + 1] == '/':
            in_multi_comment = False
            i += 2
            continue
        if in_multi_comment:
            i += 1
            continue

        # Append non-comment characters
        result.append(char)
        i += 1

    cleaned_sql = ''.join(result)
    # Remove empty lines but preserve newlines within statements
    lines = [line for line in cleaned_sql.splitlines() if line.strip()]
    cleaned_sql = '\n'.join(lines)
    logger.debug(f"Cleaned SQL:\n{cleaned_sql}")
    return cleaned_sql.strip()

def split_sql_statements(sql: str) -> List[str]:
    """Split SQL into statements, preserving semicolons and respecting quoted strings."""
    statements = []
    current = []
    in_single_quote = False
    in_double_quote = False
    i = 0

    while i < len(sql):
        char = sql[i]

        # Handle string literals
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(char)
            i += 1
            continue
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(char)
            i += 1
            continue

        # Handle semicolons outside quotes
        if char == ';' and not in_single_quote and not in_double_quote:
            current.append(char)  # Include the semicolon in the statement
            statement = ''.join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            i += 1
            continue

        current.append(char)
        i += 1

    # Add final statement if any
    statement = ''.join(current).strip()
    if statement:
        statements.append(statement)

    return statements

class Migrator:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'xmod-mariadb-1'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'xmod'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'database': os.getenv('DB_NAME', 'xmod')
        }
        self.migrations_dir = Path('migrations')
        self.connection = None

    @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
    def connect(self) -> None:
        """Establish database connection with retries."""
        try:
            self.connection = connect(**self.db_config)
            logger.info("Connected to database")
        except Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self) -> None:
        """Close database connection if open."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
            self.connection = None

    def ensure_connected(self) -> bool:
        """Ensure database connection is established."""
        if self.connection is None or not self.connection.is_connected():
            try:
                self.connect()
                return True
            except Error:
                logger.error("Failed to establish database connection")
                return False
        return True

    def get_applied_migrations(self) -> List[Dict]:
        """Retrieve applied migrations from the migrations table."""
        if not self.ensure_connected():
            logger.debug("No database connection; assuming no applied migrations")
            return []
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT timestamp, name, status, applied_at FROM migrations WHERE status = 1 ORDER BY timestamp")
            migrations = cursor.fetchall()
            cursor.close()
            return migrations
        except Error as e:
            if e.errno == 1146:  # Table doesn't exist
                logger.debug("Migrations table does not exist; no applied migrations")
                return []
            logger.error(f"Error retrieving applied migrations: {e}")
            return []

    def check_tables_exist(self) -> bool:
        """Check if any tables exist in the database."""
        if not self.ensure_connected():
            logger.debug("No database connection; assuming no tables exist")
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s",
                (self.db_config['database'],)
            )
            count = cursor.fetchone()[0]
            cursor.close()
            logger.info(f"Found {count} tables in database")
            return count > 0
        except Error as e:
            logger.error(f"Error checking table existence: {e}")
            return False

    def validate_schema(self, full_validation: bool = False) -> bool:
        """Validate schema integrity (tables, foreign keys)."""
        if not self.ensure_connected():
            logger.debug("No database connection; schema validation skipped")
            return False
        try:
            cursor = self.connection.cursor()
            if not full_validation:
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name = 'migrations'",
                    (self.db_config['database'],)
                )
                count = cursor.fetchone()[0]
                cursor.close()
                return count == 1
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.table_constraints "
                    "WHERE constraint_type = 'FOREIGN KEY' AND table_schema = %s",
                    (self.db_config['database'],)
                )
                fk_count = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_schema = %s AND table_name IN (%s)",
                    (self.db_config['database'], ','.join([
                        'migrations', 'users', 'community_members', 'posts', 'post_embeddings',
                        'post_moderation_categories', 'user_bans', 'user_warnings',
                        'notifications', 'oauth_sessions', 'moderation_actions',
                        'appeals', 'user_reputation_logs', 'logs', 'moderation_categories',
                        'user_notes', 'settings', 'community_settings'
                    ]))
                )
                table_count = cursor.fetchone()[0]
                cursor.close()
                logger.info(f"Schema validation: {fk_count} foreign keys, {table_count}/18 expected tables")
                return fk_count > 0 and table_count == 18
        except Error as e:
            logger.error(f"Error validating schema: {e}")
            return False

    def check_data_loss(self, script_path: Path) -> bool:
        """Check if a migration script contains data-loss operations."""
        try:
            with open(script_path, 'r') as f:
                sql = f.read().lower()
            destructive_keywords = ['drop table', 'delete from', 'truncate table', 'drop column']
            return any(keyword in sql for keyword in destructive_keywords)
        except FileNotFoundError:
            logger.error(f"Script not found: {script_path}")
            return False

    def get_next_migration_name(self) -> str:
        """Get the next unused migration name from names.py."""
        existing = self.list_migrations()
        used_names = {m['name'] for m in existing}
        for adj in ADJECTIVES:
            for last in LAST_NAMES:
                name = f"{adj}-{last}"
                if name not in used_names:
                    return name
        timestamp = str(int(time.time()))
        logger.warning(f"No unused migration names available; using fallback: migration-{timestamp}")
        return f"migration-{timestamp}"

    def create_migration(self, non_interactive: bool = False) -> None:
        """Create a new migration with an automatically assigned name."""
        name = self.get_next_migration_name()
        timestamp = str(int(time.time()))
        migration_dir = self.migrations_dir / f"{timestamp}_{name}"
        try:
            migration_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            logger.error(f"Migration directory {migration_dir} already exists")
            raise ValueError(f"Migration directory {migration_dir} already exists")

        up_path = migration_dir / 'up.sql'
        down_path = migration_dir / 'down.sql'
        created_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        template = (
            f"-- Migration: {name}\n"
            f"-- Created On: {created_on}\n"
            f"--\n"
            f"-- DO NOT EDIT THIS FILE AFTER COMMIT\n"
            f"-- CREATE A NEW MIGRATION INSTEAD\n"
            f"--\n"
        )
        up_path.write_text(template)
        down_path.write_text(template)
        logger.info(f"Created migration: {migration_dir} with up.sql and down.sql")

    def list_available_migrations(self) -> List[Dict]:
        """List all valid migration directories from the filesystem."""
        available = []
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory {self.migrations_dir} does not exist")
            return available
        for d in self.migrations_dir.iterdir():
            if d.is_dir():
                match = re.match(r'^(\d+)_([a-z0-9-]+)$', d.name)
                if match:
                    timestamp, name = match.groups()
                    up_file = d / 'up.sql'
                    down_file = d / 'down.sql'
                    if up_file.exists() and down_file.exists():
                        available.append({'timestamp': timestamp, 'name': name})
                    else:
                        logger.warning(f"Skipping migration {d.name}: missing up.sql or down.sql")
                else:
                    logger.debug(f"Skipping directory {d.name}: does not match timestamp_adj-last pattern")
        return sorted(available, key=lambda x: int(x['timestamp']))

    def list_migrations(self) -> List[Dict]:
        """List all migrations with their status."""
        try:
            available = self.list_available_migrations()
            applied = self.get_applied_migrations()
            applied_dict = {f"{m['timestamp']}_{m['name']}": m for m in applied}
            migrations = []
            for mig in available:
                key = f"{mig['timestamp']}_{mig['name']}"
                status = applied_dict.get(key, {}).get('status', 0)  # 0=PENDING
                applied_at = applied_dict.get(key, {}).get('applied_at')
                migrations.append({
                    'timestamp': mig['timestamp'],
                    'name': mig['name'],
                    'status': ['PENDING', 'APPLIED', 'FAILED'][status],
                    'applied_at': applied_at
                })
            return migrations
        except Exception as e:
            logger.error(f"Failed to list migrations: {e}")
            return []

    def get_status(self) -> Dict:
        """Get the current migration status."""
        migrations = self.list_migrations()
        applied = [m for m in migrations if m['status'] == 'APPLIED']
        current = max(applied, key=lambda m: int(m['timestamp'])) if applied else None
        ahead = [m for m in migrations if m['status'] == 'PENDING' and (not current or int(m['timestamp']) > int(current['timestamp']))]
        behind = [m for m in migrations if m['status'] == 'APPLIED' and current and int(m['timestamp']) < int(current['timestamp'])]
        return {
            'current': current,
            'ahead': ahead,
            'behind': behind,
            'all_migrations': sorted(migrations, key=lambda x: int(x['timestamp']))
        }

    def resolve_version(self, version: str) -> Optional[Dict]:
        """Resolve a version string to a migration (by timestamp or name)."""
        migrations = self.list_migrations()
        for m in migrations:
            if version == m['timestamp'] or version == m['name']:
                return m
        return None

    @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
    def apply_migration(self, timestamp: str, name: str, direction: str, dry_run: bool = False, ignore_warnings: bool = False) -> None:
        """Apply a migration and update its status."""
        if not self.ensure_connected():
            logger.error("Cannot apply migration: no database connection")
            raise RuntimeError("Database connection failed")
        migration_dir = self.migrations_dir / f"{timestamp}_{name}"
        script_path = migration_dir / f"{direction}.sql"
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            raise FileNotFoundError(f"Script not found: {script_path}")
        try:
            with open(script_path, 'r') as f:
                sql = f.read()
            if not sql.strip():
                logger.info(f"Script {script_path} is empty; skipping execution")
                return
            # Remove comments and split statements
            sql_clean = strip_sql_comments(sql)
            logger.debug(f"Cleaned SQL for {timestamp}_{name} ({direction}):\n{sql_clean}")
            statements = split_sql_statements(sql_clean)
            if dry_run:
                logger.info(f"Dry run: Would apply {direction} migration {timestamp}_{name}")
                for i, stmt in enumerate(statements, 1):
                    logger.info(f"Statement {i}: {stmt}")
                return
            if direction == 'down' and self.check_data_loss(script_path) and not ignore_warnings:
                logger.warning(f"Potential data loss detected in {script_path}")
                if not ignore_warnings:
                    confirm = input("This migration may cause data loss. Proceed? (y/n): ").strip().lower()
                    if confirm != 'y':
                        logger.info("Migration aborted by user")
                        return
            cursor = self.connection.cursor()
            for i, statement in enumerate(statements, 1):
                logger.debug(f"Executing statement {i} for {timestamp}_{name} ({direction}): {statement}")
                cursor.execute(statement)
            if direction == 'up':
                cursor.execute(
                    "INSERT INTO migrations (timestamp, name, status, applied_at) "
                    "VALUES (%s, %s, %s, %s) "
                    "ON DUPLICATE KEY UPDATE status = %s, applied_at = %s",
                    (int(timestamp), name, 1, datetime.now(), 1, datetime.now())
                )
            else:
                cursor.execute(
                    "UPDATE migrations SET status = %s, applied_at = NULL WHERE timestamp = %s",
                    (0, int(timestamp))
                )
            self.connection.commit()
            cursor.close()
            logger.info(f"Applied {direction} migration: {timestamp}_{name}")
        except Error as e:
            logger.error(f"Error applying migration {timestamp}_{name} ({direction}): {e}")
            self.connection.rollback()
            raise

    def run(self, target_version: Optional[str] = None, dry_run: bool = False, ignore_warnings: bool = False) -> None:
        """Run migrations to the target version or latest."""
        if not self.ensure_connected():
            logger.error("Cannot run migrations: no database connection")
            raise RuntimeError("Database connection failed")
        try:
            migrations = self.list_migrations()
            applied = [m['timestamp'] for m in migrations if m['status'] == 'APPLIED']
            available = sorted([(m['timestamp'], m['name']) for m in migrations], key=lambda x: int(x[0]))
            if not available:
                logger.info("No migrations available")
                return
            target_timestamp = available[-1][0] if not target_version else None
            if target_version:
                target = self.resolve_version(target_version)
                if not target:
                    logger.error(f"Version {target_version} not found")
                    raise ValueError(f"Version {target_version} not found")
                target_timestamp = target['timestamp']
            if not self.check_tables_exist():
                logger.info("No tables detected; applying all migrations")
                for timestamp, name in available:
                    if timestamp not in applied:
                        self.apply_migration(timestamp, name, 'up', dry_run, ignore_warnings)
                return
            current = max([int(t) for t in applied] + [0])
            target = int(target_timestamp)
            if target > current:
                direction = 'up'
                to_apply = [(t, n) for t, n in available if int(t) > current and int(t) <= target]
                logger.info(f"Migrating up to {target_timestamp}: {len(to_apply)} versions")
            else:
                direction = 'down'
                to_apply = [(t, n) for t, n in reversed(available) if int(t) <= current and int(t) > target]
                logger.info(f"Migrating down to {target_timestamp}: {len(to_apply)} versions")
            for timestamp, name in to_apply:
                if not dry_run and not self.validate_schema():
                    logger.error("Schema validation failed before migration")
                    raise ValueError("Schema validation failed")
                self.apply_migration(timestamp, name, direction, dry_run, ignore_warnings)
        except Exception as e:
            logger.error(f"Migration run failed: {e}")
            raise
        finally:
            self.close()

    def add_global_admin(self, username: str) -> None:
        """
        Add a global admin by username.
        If the user exists, sets is_global_admin to 1.
        If not, inserts a new user with x_user_id='?', username, display_name=username, and is_global_admin=1.
        """
        username = username.lstrip('@')
        if not self.ensure_connected():
            logger.error("Cannot add global admin: no database connection")
            raise RuntimeError("Database connection failed")
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user:
                cursor.execute("UPDATE users SET is_global_admin = 1 WHERE id = %s", (user[0],))
                logger.info(f"Updated user @{username} to global admin")
            else:
                display_name = username
                cursor.execute(
                    "INSERT INTO users (x_user_id, username, display_name, is_global_admin) "
                    "VALUES (%s, %s, %s, %s)",
                    ("?", username, display_name, 1)
                )
                logger.info(f"Inserted new user @{username} as global admin")
            self.connection.commit()
            cursor.close()
        except Error as e:
            logger.error(f"Error adding global admin for @{username}: {e}")
            self.connection.rollback()
            raise

    def remove_global_admin(self, username: str) -> None:
        """
        Remove global admin status by username.
        If the user exists, sets is_global_admin to 0.
        If not, logs a warning.
        """
        username = username.lstrip('@')
        if not self.ensure_connected():
            logger.error("Cannot remove global admin: no database connection")
            raise RuntimeError("Database connection failed")
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user:
                cursor.execute("UPDATE users SET is_global_admin = 0 WHERE id = %s", (user[0],))
                logger.info(f"Removed global admin status from user @{username}")
            else:
                logger.warning(f"User @{username} does not exist; cannot remove global admin status")
            self.connection.commit()
            cursor.close()
        except Error as e:
            logger.error(f"Error removing global admin for @{username}: {e}")
            self.connection.rollback()
            raise

    def run_query(self, query: str, ignore_warnings: bool = False) -> None:
        """
        Run a SQL query and display the results.
        For SELECT queries, displays a formatted table with string truncation.
        For other queries, executes and reports affected rows.
        """
        if not self.ensure_connected():
            logger.error("Cannot run query: no database connection")
            raise RuntimeError("Database connection failed")
        try:
            # Create a new connection with autocommit=True for this query
            query_conn = connect(**self.db_config, autocommit=True)
            cursor = query_conn.cursor(dictionary=True)
            if query.lower().strip().startswith("select"):
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows:
                    # Truncate strings longer than 30 characters
                    def truncate_value(v, max_length=30):
                        s = str(v)
                        if len(s) > max_length:
                            return s[:max_length - 2] + ".."
                        return s
                    truncated_rows = [{k: truncate_value(v) for k, v in row.items()} for row in rows]
                    print(tabulate(truncated_rows, headers="keys", tablefmt="grid"))
                else:
                    print("No rows returned.")
            else:
                if not ignore_warnings:
                    confirm = input("This query may modify data. Proceed? (y/n): ").strip().lower()
                    if confirm != 'y':
                        logger.info("Query execution aborted by user")
                        return
                cursor.execute(query)
                affected_rows = cursor.rowcount
                print(f"Query executed successfully. Affected rows: {affected_rows}")
            cursor.close()
            query_conn.close()
        except Error as e:
            logger.error(f"Error executing query: {e}")
            raise

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="X-Moderator Database Migrator")
    parser.add_argument('--to', type=str, help="Migrate to a specific version (timestamp or name)")
    parser.add_argument('--to-latest', action='store_true', help="Migrate to the latest version")
    parser.add_argument('--new', action='store_true', help="Create a new migration with an auto-generated name")
    parser.add_argument('--dry-run', action='store_true', help="Preview migrations without applying")
    parser.add_argument('--ignore-warnings', action='store_true', help="Ignore warnings (e.g., data loss) for non-interactive use")
    parser.add_argument('--list', action='store_true', help="List available and applied migrations")
    parser.add_argument('--status', action='store_true', help="Show current migration status")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose logging")
    parser.add_argument('--add-global-admin', type=str, help="Add a global admin by username (e.g., @username)")
    parser.add_argument('--remove-global-admin', type=str, help="Remove a global admin by username (e.g., @username)")
    parser.add_argument('--run', type=str, help="Run a SQL query and display the results in a formatted table")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    migrator = Migrator()
    try:
        if args.add_global_admin:
            logger.info(f"Adding global admin: {args.add_global_admin}")
            migrator.add_global_admin(args.add_global_admin)
        elif args.remove_global_admin:
            logger.info(f"Removing global admin: {args.remove_global_admin}")
            migrator.remove_global_admin(args.remove_global_admin)
        elif args.run:
            logger.info(f"Running query: {args.run}")
            migrator.run_query(args.run, ignore_warnings=args.ignore_warnings)
        elif args.list:
            migrations = migrator.list_migrations()
            if not migrations:
                logger.info("No migrations found")
            for migration in migrations:
                print(f"Timestamp: {migration['timestamp']}, Name: {migration['name']}, Status: {migration['status']}, Applied: {migration['applied_at']}")
        elif args.status:
            status = migrator.get_status()
            print("\nMigration Status Overview")
            print("========================")
            if not status['all_migrations']:
                print("No migrations found.")
            else:
                table_data = []
                current_timestamp = status['current']['timestamp'] if status['current'] else None
                for mig in status['all_migrations']:
                    is_current = mig['timestamp'] == current_timestamp
                    status_str = f"*{mig['status']}*" if is_current else mig['status']
                    table_data.append({
                        'Migration ID': f"{mig['timestamp']}_{mig['name']}",
                        'Name': mig['name'],
                        'Timestamp': mig['timestamp'],
                        'Status': status_str,
                        'Applied At': mig['applied_at'] or 'N/A'
                    })
                print(tabulate(table_data, headers="keys", tablefmt="grid"))
                print("\nLegend: *CURRENT* indicates the currently applied migration.")
                print(f"Total Migrations: {len(status['all_migrations'])}")
                print(f"Applied: {len(status['behind']) + (1 if status['current'] else 0)}")
                print(f"Pending: {len(status['ahead'])}")
        elif args.new:
            migrator.create_migration(non_interactive=args.ignore_warnings)
        elif args.to_latest:
            migrator.run(dry_run=args.dry_run, ignore_warnings=args.ignore_warnings)
        elif args.to:
            migrator.run(target_version=args.to, dry_run=args.dry_run, ignore_warnings=args.ignore_warnings)
        else:
            parser.print_help()
    except Exception as e:
        logger.error(f"Command failed: {e}")
        exit(1)
    finally:
        migrator.close()

#!/usr/bin/env python3
"""
Simple migration runner for ClickHouse
This script applies SQL migrations in order
"""

import os
import sys
import glob
import clickhouse_connect
from pathlib import Path

class ClickHouseMigrator:
    def __init__(self, host='localhost', port=8123, user='default', password=''):
        self.client = clickhouse_connect.get_client(
            host=host, 
            port=port, 
            user=user, 
            password=password
        )
        self.migrations_dir = Path(__file__).parent.parent / 'migrations'
        
    def create_migrations_table(self):
        """Create table to track applied migrations"""
        self.client.command("""
            CREATE TABLE IF NOT EXISTS system.migrations (
                version String,
                applied_at DateTime DEFAULT now()
            ) ENGINE = MergeTree()
            ORDER BY version
        """)
    
    def get_applied_migrations(self):
        """Get list of already applied migrations"""
        try:
            result = self.client.query("SELECT version FROM system.migrations ORDER BY version")
            return [row[0] for row in result.result_rows]
        except:
            return []
    
    def apply_migration(self, migration_file):
        """Apply a single migration file"""
        print(f"Applying migration: {migration_file.name}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement:
                try:
                    self.client.command(statement)
                except Exception as e:
                    print(f"Error executing statement: {statement[:100]}...")
                    print(f"Error: {e}")
                    raise
        
        # Record migration as applied
        self.client.command(f"""
            INSERT INTO system.migrations (version) VALUES ('{migration_file.stem}')
        """)
        
        print(f"✓ Migration {migration_file.name} applied successfully")
    
    def migrate(self):
        """Run all pending migrations"""
        self.create_migrations_table()
        applied_migrations = self.get_applied_migrations()
        
        # Get all migration files
        migration_files = sorted(glob.glob(str(self.migrations_dir / "*.sql")))
        
        for migration_file in migration_files:
            migration_name = Path(migration_file).stem
            if migration_name not in applied_migrations:
                self.apply_migration(Path(migration_file))
            else:
                print(f"⏭️  Migration {migration_name} already applied")
        
        print("✅ All migrations completed")

if __name__ == "__main__":
    migrator = ClickHouseMigrator()
    migrator.migrate()

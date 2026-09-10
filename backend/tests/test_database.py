from sqlalchemy import inspect
from app.core.database import engine

def test_database_tables_exist():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = [
        "users",
        "roles",
        "user_roles",
        "production_lines",
        "machines",
        "machine_readings",
        "machine_predictions",
        "anomaly_predictions",
        "machine_health_history",
        "alerts",
        "maintenance_records",
        "products",
        "inventory_materials",
        "inventory_transactions",
        "production_orders",
        "production_batches",
        "production_schedules",
        "schedule_revisions",
        "quality_predictions",
        "demand_forecasts",
        "audit_logs",
    ]
    
    for table in expected_tables:
        assert table in tables, f"Expected table '{table}' not found in database!"

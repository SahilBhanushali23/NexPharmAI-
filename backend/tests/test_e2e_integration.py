import pytest
import uuid
from datetime import datetime, timezone, timedelta

def test_full_system_connected_workflow(client):
    """
    Final Acceptance Test (Section 51):
    LOGIN -> VIEW MACHINES -> ADD MACHINE -> ADD MACHINE READING -> 
    RUN PREDICTIVE MAINTENANCE -> RUN ANOMALY DETECTION -> CALCULATE HEALTH -> 
    GENERATE ALERT -> CREATE MAINTENANCE -> CHECK INVENTORY -> 
    CREATE PRODUCTION ORDER -> GENERATE OPTIMIZED SCHEDULE -> 
    MACHINE BECOMES UNHEALTHY -> DETECT SCHEDULING CONFLICT -> AUTOMATICALLY RESCHEDULE -> 
    BATCH QUALITY PREDICTION -> OEE ANALYTICS -> AI DECISION ASSISTANT
    """
    uid = uuid.uuid4().hex[:6]
    admin_email = f"e2e_admin_{uid}@nexpharm.ai"

    # 1. LOGIN / REGISTRATION
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": admin_email,
        "password": "E2ePassword2026!",
        "full_name": "Dr. Enterprise Tester",
        "role": "ADMIN"
    })
    assert reg_resp.status_code == 201

    login_resp = client.post("/api/v1/auth/login", json={
        "email": admin_email,
        "password": "E2ePassword2026!"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. VIEW MACHINES
    mach_list_resp = client.get("/api/v1/machines", headers=headers)
    assert mach_list_resp.status_code == 200
    assert len(mach_list_resp.json()) >= 1

    # 3. ADD MACHINE
    new_mach_id = f"M-TEST-{uid.upper()}"
    add_mach_resp = client.post("/api/v1/machines", json={
        "machine_id": new_mach_id,
        "machine_name": "Sterile Vial Depyrogenation Tunnel",
        "machine_type": "M",
        "production_line": "LINE-1",
        "location": "Aseptic Suite 105",
        "status": "IDLE"
    }, headers=headers)
    assert add_mach_resp.status_code == 201

    # 4. ADD MACHINE READING & INGEST (Runs PM ML, Anomaly, Health, Alerts)
    reading_payload = {
        "machine_id": new_mach_id,
        "machine_type": "M",
        "air_temperature": 298.5,
        "process_temperature": 308.8,
        "rotational_speed": 1520.0,
        "torque": 41.5,
        "tool_wear": 15.0
    }
    ingest_resp = client.post("/api/v1/readings/ingest", json=reading_payload, headers=headers)
    assert ingest_resp.status_code == 201
    ingest_data = ingest_resp.json()
    assert "prediction" in ingest_data
    assert "anomaly" in ingest_data
    assert "health" in ingest_data
    assert ingest_data["health"]["category"] in ["EXCELLENT", "GOOD"]

    # 5. RUN DIRECT PREDICTIVE MAINTENANCE INFERENCE
    pm_resp = client.post("/api/v1/predictive-maintenance/predict", json={
        "machine_type": "M",
        "air_temperature": 298.5,
        "process_temperature": 308.8,
        "rotational_speed": 1520.0,
        "torque": 41.5,
        "tool_wear": 15.0
    }, headers=headers)
    assert pm_resp.status_code == 200
    assert "failure_probability" in pm_resp.json()

    # 6. RUN DIRECT ANOMALY INFERENCE
    anom_resp = client.post("/api/v1/anomaly-detection/predict", json={
        "air_temperature": 298.5,
        "process_temperature": 308.8,
        "rotational_speed": 1520.0,
        "torque": 41.5,
        "tool_wear": 15.0
    }, headers=headers)
    assert anom_resp.status_code == 200
    assert "severity" in anom_resp.json()

    # 7. CREATE MAINTENANCE WORK ORDER
    maint_resp = client.post("/api/v1/maintenance", json={
        "machine_id": new_mach_id,
        "maintenance_type": "PREVENTIVE",
        "reason": "HEPA filter integrity testing and air velocity check",
        "priority": "MEDIUM",
        "scheduled_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    }, headers=headers)
    assert maint_resp.status_code == 201

    # 8. CHECK INVENTORY
    inv_resp = client.get("/api/v1/inventory", headers=headers)
    assert inv_resp.status_code == 200
    assert len(inv_resp.json()) >= 1

    # 9. GET PRODUCTS & CREATE PRODUCTION ORDER
    prods_resp = client.get("/api/v1/products", headers=headers)
    assert prods_resp.status_code == 200
    prod_id = prods_resp.json()[0]["id"]

    order_resp = client.post("/api/v1/production/orders", json={
        "order_code": f"ORD-E2E-{uid.upper()}",
        "product_id": prod_id,
        "quantity": 20000,
        "priority": "HIGH",
        "due_date": (datetime.now(timezone.utc) + timedelta(days=4)).isoformat()
    }, headers=headers)
    assert order_resp.status_code == 201

    # 10. GENERATE AI OPTIMIZED SCHEDULE (OR-Tools)
    sched_resp = client.post("/api/v1/scheduler/generate", json={"horizon_days": 7}, headers=headers)
    assert sched_resp.status_code == 200
    sched_data = sched_resp.json()
    assert sched_data["optimizer_status"] in ["OPTIMAL", "FEASIBLE"]
    assert len(sched_data["assignments"]) > 0

    # 11. INGEST CRITICAL MACHINE READING (Triggers Machine Degradation & Dynamic Rescheduling)
    critical_reading = {
        "machine_id": new_mach_id,
        "machine_type": "M",
        "air_temperature": 304.8,
        "process_temperature": 313.9,
        "rotational_speed": 1220.0,
        "torque": 68.5, # Overload
        "tool_wear": 245.0 # Extreme wear
    }
    crit_ingest_resp = client.post("/api/v1/readings/ingest", json=critical_reading, headers=headers)
    assert crit_ingest_resp.status_code == 201
    crit_data = crit_ingest_resp.json()
    assert crit_data["machine_status"] in ["CRITICAL", "WARNING"]

    # 12. VERIFY AUTOMATIC RESCHEDULING REVISION CREATED
    revs_resp = client.get("/api/v1/scheduler/revisions", headers=headers)
    assert revs_resp.status_code == 200
    revisions = revs_resp.json()
    assert len(revisions) >= 1
    assert "trigger_event" in revisions[0]

    # 13. BATCH QUALITY PREDICTION
    batches_resp = client.get("/api/v1/production/batches", headers=headers)
    assert batches_resp.status_code == 200
    batch_id = batches_resp.json()[0]["id"]

    qual_resp = client.post("/api/v1/quality/predict", json={
        "batch_id": batch_id,
        "temperature": 23.5,
        "pressure": 1.05,
        "ph": 7.02,
        "humidity": 44.0,
        "mixing_speed": 300.0,
        "mixing_time": 45.0
    }, headers=headers)
    assert qual_resp.status_code == 201
    qual_data = qual_resp.json()
    assert qual_data["status"] == "PASS"
    assert qual_data["quality_score"] >= 80.0

    # 14. OEE & PRODUCTION ANALYTICS DASHBOARD
    analytics_resp = client.get("/api/v1/analytics/dashboard", headers=headers)
    assert analytics_resp.status_code == 200
    kpis = analytics_resp.json()
    assert "oee" in kpis
    assert "machines" in kpis
    assert kpis["machines"]["total"] >= 6
    assert kpis["oee"]["overall"] > 0

    # 15. AI DECISION ASSISTANT
    query_resp = client.post("/api/v1/assistant/query", json={
        "query": "Which machine has the highest failure risk?"
    }, headers=headers)
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    assert "highest failure risk" in query_data["answer"] or "Machine" in query_data["answer"]

    # Test another question
    query_resp2 = client.post("/api/v1/assistant/query", json={
        "query": "What materials are low?"
    }, headers=headers)
    assert query_resp2.status_code == 200
    assert "PVDC" in query_resp2.json()["answer"] or "material" in query_resp2.json()["answer"]

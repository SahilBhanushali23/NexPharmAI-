def test_health_check(client):
    """
    Verify that the system health endpoint responds with 200 OK and expected status schema.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["service"] == "NexPharmAI"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data

import pytest
import uuid

def test_user_registration_and_login(client):
    uid = uuid.uuid4().hex[:6]
    admin_email = f"admin_{uid}@nexpharm.ai"
    operator_email = f"operator_{uid}@nexpharm.ai"

    # 1. Register Admin User
    admin_payload = {
        "email": admin_email,
        "password": "SecureAdminPassword2026!",
        "full_name": "Dr. Sarah Admin",
        "role": "ADMIN"
    }
    reg_response = client.post("/api/v1/auth/register", json=admin_payload)
    assert reg_response.status_code == 201
    user_data = reg_response.json()
    assert user_data["email"] == admin_email
    assert user_data["role"] == "ADMIN"
    assert "id" in user_data

    # 2. Login
    login_payload = {
        "email": admin_email,
        "password": "SecureAdminPassword2026!"
    }
    login_response = client.post("/api/v1/auth/login", json=login_payload)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Test /me protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == admin_email
    assert me_data["role"] == "ADMIN"

    # 4. Register Operator
    operator_payload = {
        "email": operator_email,
        "password": "OperatorPassword2026!",
        "full_name": "John Operator",
        "role": "OPERATOR"
    }
    op_reg_resp = client.post("/api/v1/auth/register", json=operator_payload)
    assert op_reg_resp.status_code == 201

    # Login Operator
    op_login_resp = client.post("/api/v1/auth/login", json={
        "email": operator_email,
        "password": "OperatorPassword2026!"
    })
    op_token = op_login_resp.json()["access_token"]
    op_headers = {"Authorization": f"Bearer {op_token}"}


    # 5. Verify RBAC protection: Operator cannot access Admin-only /users list
    forbidden_resp = client.get("/api/v1/users", headers=op_headers)
    assert forbidden_resp.status_code == 403

    # 6. Admin CAN access /users list
    admin_list_resp = client.get("/api/v1/users", headers=headers)
    assert admin_list_resp.status_code == 200
    users_list = admin_list_resp.json()
    assert len(users_list) >= 2

import json
import asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import status
from app.main import app

async def _post(client, url, json_data=None):
    r = await client.post(url, json=json_data)
    return r

async def test_questions_and_mock_evaluation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r_user = await _post(client, "/users/")
        assert r_user.status_code == 200, r_user.text
        user_id = r_user.json()["user_id"]
        r_q = await client.get("/questions/")
        assert r_q.status_code == 200, r_q.text
        questions = r_q.json()
        assert questions, "Debe haber preguntas sembradas"
        answers_payload = {"answers": [{"questionId": q["id"], "answer": q["options"][0]} for q in questions]}
        r_ans = await client.post(f"/submit-answers/?user_id={user_id}", json=answers_payload)
        assert r_ans.status_code == 200, r_ans.text
        r_eval = await _post(client, f"/evaluate/{user_id}")
        assert r_eval.status_code == 200, r_eval.text
        data = r_eval.json()
        assert "iq_score" in data
        assert "certificate_url" in data

async def test_paypal_debug():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/paypal/debug")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "client_id_present" in body

async def test_certificate_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r_user = await _post(client, "/users/")
        assert r_user.status_code == 200, r_user.text
        user_id = r_user.json()["user_id"]
        r_q = await client.get("/questions/")
        assert r_q.status_code == 200, r_q.text
        questions = r_q.json()
        answers_payload = {"answers": [{"questionId": q["id"], "answer": q["options"][0]} for q in questions]}
        await client.post(f"/submit-answers/?user_id={user_id}", json=answers_payload)
        await _post(client, f"/evaluate/{user_id}")
        r_pdf = await client.get(f"/certificates/{user_id}-anonimo.pdf")
        assert r_pdf.status_code == 200, r_pdf.text
        assert r_pdf.headers["content-type"].startswith("application/pdf")

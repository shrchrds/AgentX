import io

import docx
from httpx import AsyncClient


class TestTaskRoutes:
    """Tests for POST /tasks and GET /tasks/{id}."""

    async def test_create_task_success(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/tasks",
            json={"input_data": "Review this contract for missing clauses."},
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("completed", "failed")
        assert "task_id" in data

    async def test_create_task_no_api_key(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/tasks",
            json={"input_data": "Test input."},
        )
        assert resp.status_code == 422  # Missing required header

    async def test_create_task_invalid_input(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/tasks",
            json={"input_data": ""},
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 422

    async def test_get_task_success(self, client: AsyncClient) -> None:
        # First create a task
        create_resp = await client.post(
            "/api/v1/tasks",
            json={"input_data": "Review this NDA contract."},
            headers={"X-API-Key": "test-key"},
        )
        task_id = create_resp.json()["task_id"]

        # Then retrieve it
        get_resp = await client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"X-API-Key": "test-key"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["task_id"] == task_id

    async def test_get_task_not_found(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/api/v1/tasks/nonexistent-id",
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 404

    async def test_list_tasks(self, client: AsyncClient) -> None:
        # Create a task
        await client.post(
            "/api/v1/tasks",
            json={"input": "Review this agreement."},
            headers={"X-API-Key": "test-key"},
        )
        resp = await client.get(
            "/api/v1/tasks",
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 200
        tasks = resp.json()
        assert isinstance(tasks, list)
        assert len(tasks) >= 1

    async def test_extract_text_txt_success(self, client: AsyncClient) -> None:
        file_content = (
            b"Clause 9. Confidentiality and non-disclosure obligations shall endure 3 years."
        )
        files = {"file": ("nda_clause.txt", file_content, "text/plain")}
        resp = await client.post(
            "/api/v1/tasks/extract-text",
            files=files,
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "nda_clause.txt"
        assert "Confidentiality" in data["content"]
        assert data["format"] == "txt"
        assert data["char_count"] > 0

    async def test_extract_text_docx_success(self, client: AsyncClient) -> None:
        doc = docx.Document()

        doc.add_paragraph("Agreement for legal services between Client and Attorney.")
        buf = io.BytesIO()
        doc.save(buf)

        files = {
            "file": (
                "services.docx",
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        resp = await client.post(
            "/api/v1/tasks/extract-text",
            files=files,
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "services.docx"
        assert "Agreement for legal services" in data["content"]
        assert data["format"] == "docx"

    async def test_extract_text_unsupported_format(self, client: AsyncClient) -> None:
        files = {"file": ("malicious.exe", b"fake binary", "application/octet-stream")}
        resp = await client.post(
            "/api/v1/tasks/extract-text",
            files=files,
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 400
        assert "Unsupported file format" in resp.json()["detail"]

    async def test_upload_document_task_success(self, client: AsyncClient) -> None:
        file_content = b"Contract Review: Party A indemnifies Party B against all losses."
        files = {"file": ("contract.txt", file_content, "text/plain")}
        data = {"task_id": "upload-doc-task-001"}
        resp = await client.post(
            "/api/v1/tasks/upload",
            files=files,
            data=data,
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 200
        res = resp.json()
        assert res["task_id"] == "upload-doc-task-001"
        assert res["status"] in ("completed", "failed")

    async def test_upload_document_task_unsupported_format(self, client: AsyncClient) -> None:
        files = {"file": ("evidence.png", b"image bytes", "image/png")}
        resp = await client.post(
            "/api/v1/tasks/upload",
            files=files,
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 400
        assert "Unsupported file format" in resp.json()["detail"]

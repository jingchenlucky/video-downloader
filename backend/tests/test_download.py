import time


def test_download_creates_task(client, fake_downloader, tmp_path):
    url = "https://example.com/video"
    source = tmp_path / "sample.mp4"
    source.write_bytes(b"fake-video")
    fake_downloader.videos[url] = __import__(
        "app.services.video_downloader", fromlist=["sample_video_info"]
    ).sample_video_info(url)
    fake_downloader.download_files[url] = source

    response = client.post("/api/download", json={"url": url})

    assert response.status_code == 200
    assert "task_id" in response.json()


def test_task_status_reaches_completed(client, fake_downloader, tmp_path):
    url = "https://example.com/video"
    source = tmp_path / "sample.mp4"
    source.write_bytes(b"fake-video")
    fake_downloader.videos[url] = __import__(
        "app.services.video_downloader", fromlist=["sample_video_info"]
    ).sample_video_info(url)
    fake_downloader.download_files[url] = source

    create_response = client.post("/api/download", json={"url": url})
    task_id = create_response.json()["task_id"]

    final_status = None
    for _ in range(20):
        status_response = client.get(f"/api/tasks/{task_id}")
        assert status_response.status_code == 200
        body = status_response.json()
        if body["status"] in {"completed", "failed"}:
            final_status = body
            break
        time.sleep(0.05)

    assert final_status is not None
    assert final_status["status"] == "completed"
    assert final_status["progress"] == 1.0
    assert final_status["filename"] == "sample.mp4"


def test_unknown_task_returns_404(client):
    response = client.get("/api/tasks/does-not-exist")

    assert response.status_code == 404


def test_failed_download_reports_error(client, fake_downloader):
    url = "https://example.com/video"
    fake_downloader.videos[url] = __import__(
        "app.services.video_downloader", fromlist=["sample_video_info"]
    ).sample_video_info(url)
    fake_downloader.download_error = "network error"

    create_response = client.post("/api/download", json={"url": url})
    task_id = create_response.json()["task_id"]

    final_status = None
    for _ in range(20):
        status_response = client.get(f"/api/tasks/{task_id}")
        body = status_response.json()
        if body["status"] in {"completed", "failed"}:
            final_status = body
            break
        time.sleep(0.05)

    assert final_status is not None
    assert final_status["status"] == "failed"
    assert "network error" in final_status["error"].lower()

import time

from app.services.task_manager import TaskManager


def test_completed_task_file_can_be_downloaded(client, fake_downloader, tmp_path):
    url = "https://example.com/video"
    source = tmp_path / "sample.mp4"
    source.write_bytes(b"fake-video-content")
    fake_downloader.videos[url] = __import__(
        "app.services.video_downloader", fromlist=["sample_video_info"]
    ).sample_video_info(url)
    fake_downloader.download_files[url] = source

    task_id = client.post("/api/download", json={"url": url}).json()["task_id"]
    _wait_until_done(client, task_id)

    file_response = client.get(f"/api/tasks/{task_id}/file")

    assert file_response.status_code == 200
    assert file_response.content == b"fake-video-content"
    assert "sample.mp4" in file_response.headers.get("content-disposition", "")


def test_completed_task_file_supports_unicode_filename(client, fake_downloader, tmp_path):
    url = "https://example.com/video"
    source = tmp_path / "国内视频.mp4"
    source.write_bytes(b"fake-video-content")
    fake_downloader.videos[url] = __import__(
        "app.services.video_downloader", fromlist=["sample_video_info"]
    ).sample_video_info(url)
    fake_downloader.download_files[url] = source

    task_id = client.post("/api/download", json={"url": url}).json()["task_id"]
    _wait_until_done(client, task_id)

    file_response = client.get(f"/api/tasks/{task_id}/file")

    assert file_response.status_code == 200
    assert file_response.content == b"fake-video-content"
    disposition = file_response.headers.get("content-disposition", "")
    assert "filename*=" in disposition
    assert "%E5%9B%BD" in disposition


def test_incomplete_task_file_returns_conflict(client_factory):
    task_manager = TaskManager()
    task = task_manager.create_task("https://example.com/video", None)
    task.status = "downloading"

    client = client_factory(task_manager=task_manager)
    file_response = client.get(f"/api/tasks/{task.id}/file")

    assert file_response.status_code == 409


def test_file_is_removed_after_successful_download(client, fake_downloader, tmp_path):
    url = "https://example.com/video"
    source = tmp_path / "sample.mp4"
    source.write_bytes(b"fake-video-content")
    fake_downloader.videos[url] = __import__(
        "app.services.video_downloader", fromlist=["sample_video_info"]
    ).sample_video_info(url)
    fake_downloader.download_files[url] = source
    download_dir = tmp_path / "downloads"

    task_id = client.post("/api/download", json={"url": url}).json()["task_id"]
    _wait_until_done(client, task_id)

    file_response = client.get(f"/api/tasks/{task_id}/file")
    assert file_response.status_code == 200

    saved_files = list(download_dir.glob("*.mp4"))
    assert saved_files == []


def test_expired_task_file_is_cleaned_up(client_factory, fake_downloader, tmp_path):
    url = "https://example.com/video"
    source = tmp_path / "sample.mp4"
    source.write_bytes(b"fake-video-content")
    fake_downloader.videos[url] = __import__(
        "app.services.video_downloader", fromlist=["sample_video_info"]
    ).sample_video_info(url)
    fake_downloader.download_files[url] = source
    download_dir = tmp_path / "downloads"

    client = client_factory(cleanup_ttl_seconds=0.01)
    task_id = client.post("/api/download", json={"url": url}).json()["task_id"]
    _wait_until_done(client, task_id)

    time.sleep(0.02)
    client.get(f"/api/tasks/{task_id}")

    saved_files = list(download_dir.glob("*.mp4"))
    assert saved_files == []


def _wait_until_done(client, task_id: str):
    for _ in range(20):
        body = client.get(f"/api/tasks/{task_id}").json()
        if body["status"] in {"completed", "failed"}:
            return body
        time.sleep(0.05)
    raise AssertionError("task did not finish in time")

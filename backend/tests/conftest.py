import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.video_downloader import FakeVideoDownloader


@pytest.fixture
def fake_downloader():
    return FakeVideoDownloader()


@pytest.fixture
def client(fake_downloader, tmp_path):
    app = create_app(
        downloader=fake_downloader,
        download_dir=tmp_path / "downloads",
    )
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client_factory(fake_downloader, tmp_path):
    def _create_client(
        cleanup_ttl_seconds: float = 1800.0,
        task_manager=None,
    ):
        app = create_app(
            downloader=fake_downloader,
            download_dir=tmp_path / "downloads",
            cleanup_ttl_seconds=cleanup_ttl_seconds,
            task_manager=task_manager,
        )
        return TestClient(app)

    return _create_client

from app.main import create_app
from app.services.ytdlp_downloader import YtdlpVideoDownloader


def test_default_downloader_is_ytdlp():
    app = create_app()

    assert isinstance(app.state.downloader, YtdlpVideoDownloader)

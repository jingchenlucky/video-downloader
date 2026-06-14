def test_analyze_rejects_unsupported_url(client, fake_downloader):
    response = client.post("/api/analyze", json={"url": "https://bad.example/video"})

    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()


def test_analyze_returns_video_metadata(client, fake_downloader):
    url = "https://example.com/video"
    fake_downloader.videos[url] = __import__(
        "app.services.video_downloader", fromlist=["sample_video_info"]
    ).sample_video_info(url)

    response = client.post("/api/analyze", json={"url": url})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Sample Video"
    assert body["thumbnail"] == "https://example.com/thumb.jpg"
    assert body["duration"] == 120
    assert body["default_format_id"] == "best"
    assert len(body["formats"]) == 3
    assert body["formats"][0]["label"] == "最佳画质 (MP4)"

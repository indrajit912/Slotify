def test_homepage(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Welcome to Slotify" in response.data

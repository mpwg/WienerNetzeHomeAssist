"""Test the testing framework itself."""

from tests.utils import load_fixture, load_json_fixture


def test_load_fixture():
    """Test that fixture loading works."""
    data = load_fixture("oauth_token.json")
    assert data is not None
    assert "access_token" in data


def test_load_json_fixture():
    """Test that JSON fixture loading works."""
    data = load_json_fixture("oauth_token.json")
    assert isinstance(data, dict)
    assert "access_token" in data
    assert data["token_type"] == "Bearer"


def test_load_meter_points_fixture():
    """Test loading meter points fixture."""
    data = load_json_fixture("meter_points.json")
    assert isinstance(data, dict)
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0
    assert "zaehlpunktnummer" in data["items"][0]


def test_load_consumption_fixture():
    """Test loading consumption fixture."""
    data = load_json_fixture("consumption_quarter_hour.json")
    assert isinstance(data, dict)
    assert "zaehlpunkt" in data
    assert "zaehlwerke" in data
    assert len(data["zaehlwerke"]) == 1
    assert len(data["zaehlwerke"][0]["messwerte"]) == 3


def test_mock_config_entry_fixture(mock_config_entry):
    """Test that mock_config_entry fixture works."""
    assert mock_config_entry.domain == "wiener_netze"
    assert mock_config_entry.title == "Wiener Netze Smart Meter"
    assert "client_id" in mock_config_entry.data


def test_mock_api_client_fixture(mock_api_client):
    """Test that mock_api_client fixture works."""
    assert mock_api_client is not None
    assert mock_api_client.authenticate.return_value is True

    meter_points = mock_api_client.get_meter_points.return_value
    assert isinstance(meter_points, list)
    assert len(meter_points) > 0


def test_mock_oauth_response_fixture(mock_oauth_response):
    """Test that mock_oauth_response fixture works."""
    assert "access_token" in mock_oauth_response
    assert mock_oauth_response["token_type"] == "Bearer"
    assert mock_oauth_response["expires_in"] == 3600


def test_mock_meter_data_fixture(mock_meter_data):
    """Test that mock_meter_data fixture works."""
    assert "zaehlpunktnummer" in mock_meter_data
    assert "geraet" in mock_meter_data
    assert "geraetenummer" in mock_meter_data["geraet"]


def test_mock_consumption_data_fixture(mock_consumption_data):
    """Test that mock_consumption_data fixture works."""
    assert "werte" in mock_consumption_data
    assert len(mock_consumption_data["werte"]) == 2
    assert mock_consumption_data["wertetyp"] == "QUARTER_HOUR"

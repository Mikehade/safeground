"""Behavioral unit tests for IncidentService.

Tests: token generation, status lookup, error propagation.
"""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from infrastructure.db.models.incident import IncidentStatus, IncidentType
from infrastructure.services.incident import IncidentService


@pytest.fixture
def mock_repo(mocker):
    repo = mocker.AsyncMock()
    repo.create = mocker.AsyncMock()
    repo.get_all = mocker.AsyncMock()
    return repo


@pytest.fixture
def service(mock_repo):
    return IncidentService(incident_repo=mock_repo)


@pytest.fixture
def sample_incident(mocker):
    inc = mocker.Mock()
    inc.id = uuid4()
    inc.incident_type = IncidentType.POLICE_BRUTALITY
    inc.status = IncidentStatus.PENDING
    inc.created_at = mocker.Mock()
    inc.created_at.isoformat.return_value = "2026-09-15T14:00:00+00:00"
    return inc


class TestSubmitReport:

    @pytest.mark.asyncio
    async def test_returns_incident_dict_and_receipt_token(
        self, service, mock_repo, sample_incident
    ):
        """Submit creates a record and returns a plaintext receipt token."""
        mock_repo.create.return_value = sample_incident

        result, token = await service.submit_report({
            "incident_type": "police_brutality",
            "latitude": 6.45,
            "longitude": 3.40,
        })

        assert token.startswith("SG-")
        assert len(token) == 19  # "SG-" + 16 hex chars
        assert result["id"] == str(sample_incident.id)
        assert result["status"] == "pending"
        mock_repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stores_bcrypt_hash_not_plaintext(
        self, service, mock_repo, sample_incident
    ):
        """The token hash stored in DB must not equal the plaintext token."""
        mock_repo.create.return_value = sample_incident

        _, token = await service.submit_report({
            "incident_type": "robbery",
            "latitude": 6.5,
            "longitude": 3.3,
        })

        call_args = mock_repo.create.call_args[0][0]
        stored_hash = call_args["receipt_token_hash"]
        assert stored_hash != token
        assert stored_hash.startswith("$2b$")

    @pytest.mark.asyncio
    async def test_propagates_repo_error(self, service, mock_repo):
        mock_repo.create.side_effect = RuntimeError("db down")

        with pytest.raises(RuntimeError, match="db down"):
            await service.submit_report({
                "incident_type": "corruption",
                "latitude": 6.5,
                "longitude": 3.3,
            })


class TestCheckStatus:

    @pytest.mark.asyncio
    async def test_returns_status_for_valid_token(
        self, service, mock_repo, sample_incident, mocker
    ):
        """Look up incident by verifying bcrypt hash."""
        import bcrypt
        token = "SG-abc123def456"
        sample_incident.receipt_token_hash = bcrypt.hashpw(
            token.encode(), bcrypt.gensalt()
        ).decode()
        mock_repo.get_all.return_value = [sample_incident]

        result = await service.check_status(token)

        assert result is not None
        assert result["status"] == "pending"
        assert result["incident_type"] == "police_brutality"

    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_token(
        self, service, mock_repo
    ):
        mock_repo.get_all.return_value = []

        result = await service.check_status("SG-nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_hash_matches(
        self, service, mock_repo, mocker
    ):
        """No incident in DB matches this token hash."""
        import bcrypt
        inc = mocker.Mock()
        inc.receipt_token_hash = bcrypt.hashpw(
            b"SG-different", bcrypt.gensalt()
        ).decode()
        mock_repo.get_all.return_value = [inc]

        result = await service.check_status("SG-wrongtoken123")

        assert result is None


class TestGetRecent:

    @pytest.mark.asyncio
    async def test_returns_formatted_incident_list(
        self, service, mock_repo, sample_incident
    ):
        sample_incident.latitude = 6.45
        sample_incident.longitude = 3.40
        sample_incident.severity = 0.8
        sample_incident.city = "Lekki"
        mock_repo.get_all.return_value = [sample_incident]

        result = await service.get_recent(region="Lagos", limit=10)

        assert len(result) == 1
        assert result[0]["city"] == "Lekki"
        assert result[0]["severity"] == 0.8

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_incidents(
        self, service, mock_repo
    ):
        mock_repo.get_all.return_value = []

        result = await service.get_recent()

        assert result == []

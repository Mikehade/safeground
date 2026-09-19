"""Behavioral unit tests for IncidentRepository.

Same pattern as Elle's test_feedback.py: mock session factory,
Arrange/Act/Assert, transaction behavior, error propagation.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from infrastructure.db.models.incident import Incident, IncidentType, IncidentStatus
from infrastructure.repository.incident import IncidentRepository


@pytest.fixture
def mock_db_session(mocker):
    session = mocker.AsyncMock()
    session.execute = mocker.AsyncMock()
    session.flush = mocker.AsyncMock()
    session.commit = mocker.AsyncMock()
    session.refresh = mocker.AsyncMock()
    session.add = mocker.Mock()

    ctx = mocker.AsyncMock()
    ctx.__aenter__.return_value = session
    ctx.__aexit__.return_value = None

    factory = mocker.Mock(return_value=ctx)
    return factory, session


@pytest.fixture
def repository(mock_db_session):
    factory, _ = mock_db_session
    return IncidentRepository(session_factory=factory)


@pytest.fixture
def sample_incident(mocker):
    inc = mocker.Mock(spec=Incident)
    inc.id = uuid4()
    inc.receipt_token_hash = "$2b$12$hashedtokenvalue"
    inc.incident_type = IncidentType.POLICE_BRUTALITY
    inc.description = "Officers demanded bribes"
    inc.latitude = 6.4389
    inc.longitude = 3.4728
    inc.city = "Lekki"
    inc.region = "Lagos"
    inc.severity = 0.8
    inc.status = IncidentStatus.PENDING
    inc.created_at = datetime(2026, 9, 15, 14, 0, tzinfo=timezone.utc)
    inc.deleted_at = None
    return inc


class TestInitialization:

    def test_stores_injected_session_factory(self, mock_db_session):
        factory, _ = mock_db_session
        repo = IncidentRepository(session_factory=factory)
        assert repo.session_factory is factory

    def test_sets_correct_model(self, repository):
        assert repository.model is Incident


class TestFindInCorridor:

    @pytest.mark.asyncio
    async def test_returns_incidents_within_bounding_box(
        self, repository, mock_db_session, sample_incident, mocker
    ):
        """Query incidents within geographic corridor, most recent first."""
        _, session = mock_db_session
        result_proxy = mocker.Mock()
        result_proxy.scalars.return_value.all.return_value = [sample_incident]
        session.execute.return_value = result_proxy

        result = await repository.find_in_corridor(
            min_lat=6.40, max_lat=6.50,
            min_lng=3.40, max_lng=3.50,
            hours_back=72,
        )

        assert result == [sample_incident]
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_no_matches(
        self, repository, mock_db_session, mocker
    ):
        _, session = mock_db_session
        result_proxy = mocker.Mock()
        result_proxy.scalars.return_value.all.return_value = []
        session.execute.return_value = result_proxy

        result = await repository.find_in_corridor(0, 0, 0, 0, hours_back=1)

        assert result == []

    @pytest.mark.asyncio
    async def test_propagates_database_error(
        self, repository, mock_db_session
    ):
        _, session = mock_db_session
        session.execute.side_effect = RuntimeError("connection lost")

        with pytest.raises(RuntimeError, match="connection lost"):
            await repository.find_in_corridor(6.0, 7.0, 3.0, 4.0)


class TestGetByReceiptHash:

    @pytest.mark.asyncio
    async def test_returns_incident_matching_hash(
        self, repository, mock_db_session, sample_incident, mocker
    ):
        _, session = mock_db_session
        result_proxy = mocker.Mock()
        result_proxy.scalars.return_value.first.return_value = sample_incident
        session.execute.return_value = result_proxy

        result = await repository.get_by_receipt_hash("$2b$12$hashedtokenvalue")

        assert result is sample_incident

    @pytest.mark.asyncio
    async def test_returns_none_when_no_match(
        self, repository, mock_db_session, mocker
    ):
        _, session = mock_db_session
        result_proxy = mocker.Mock()
        result_proxy.scalars.return_value.first.return_value = None
        session.execute.return_value = result_proxy

        result = await repository.get_by_receipt_hash("nonexistent")

        assert result is None


class TestGetHotspots:

    @pytest.mark.asyncio
    async def test_returns_aggregated_hotspot_data(
        self, repository, mock_db_session, mocker
    ):
        _, session = mock_db_session
        row1 = mocker.Mock()
        row1._mapping = {"city": "Lekki", "incident_type": "robbery", "count": 5, "avg_severity": 0.7}
        row2 = mocker.Mock()
        row2._mapping = {"city": "Ikorodu", "incident_type": "police_brutality", "count": 3, "avg_severity": 0.85}
        session.execute.return_value = [row1, row2]

        result = await repository.get_hotspots("Lagos", limit=10)

        assert len(result) == 2
        assert result[0]["city"] == "Lekki"
        assert result[1]["count"] == 3

    @pytest.mark.asyncio
    async def test_returns_empty_for_region_with_no_incidents(
        self, repository, mock_db_session
    ):
        _, session = mock_db_session
        session.execute.return_value = []

        result = await repository.get_hotspots("EmptyRegion")

        assert result == []


class TestBaseRepositoryCRUD:

    @pytest.mark.asyncio
    async def test_create_adds_flushes_and_refreshes(
        self, repository, mock_db_session, mocker
    ):
        _, session = mock_db_session

        await repository.create({
            "receipt_token_hash": "hash",
            "incident_type": "robbery",
            "latitude": 6.5,
            "longitude": 3.3,
        })

        session.add.assert_called_once()
        session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_returns_matching_record(
        self, repository, mock_db_session, sample_incident, mocker
    ):
        _, session = mock_db_session
        result_proxy = mocker.Mock()
        result_proxy.scalars.return_value.first.return_value = sample_incident
        session.execute.return_value = result_proxy

        result = await repository.get_by_id(sample_incident.id)

        assert result is sample_incident

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_for_missing(
        self, repository, mock_db_session, mocker
    ):
        _, session = mock_db_session
        result_proxy = mocker.Mock()
        result_proxy.scalars.return_value.first.return_value = None
        session.execute.return_value = result_proxy

        result = await repository.get_by_id(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_returns_true_when_row_deleted(
        self, repository, mock_db_session, mocker
    ):
        _, session = mock_db_session
        result_proxy = mocker.Mock()
        result_proxy.rowcount = 1
        session.execute.return_value = result_proxy

        result = await repository.delete_by_id(uuid4())

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_no_row(
        self, repository, mock_db_session, mocker
    ):
        _, session = mock_db_session
        result_proxy = mocker.Mock()
        result_proxy.rowcount = 0
        session.execute.return_value = result_proxy

        result = await repository.delete_by_id(uuid4())

        assert result is False

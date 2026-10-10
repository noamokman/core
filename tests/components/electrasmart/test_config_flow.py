"""Test the Electra Smart config flow."""

from json import loads
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.electrasmart.config_flow import ElectraApiError
from homeassistant.components.electrasmart.const import (
    CONF_IMEI,
    CONF_OTP,
    CONF_PHONE_NUMBER,
    DOMAIN,
)
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry, async_load_fixture


async def test_form(hass: HomeAssistant) -> None:
    """Test user config."""

    mock_generate_token = loads(
        await async_load_fixture(hass, "generate_token_response.json", DOMAIN)
    )
    with patch(
        "electrasmart.api.ElectraAPI.generate_new_token",
        return_value=mock_generate_token,
    ):
        # test with required
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=None,
        )

        assert result["step_id"] == "user"

        # test with required
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PHONE_NUMBER: "0521234567"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == CONF_OTP


async def test_one_time_password(hass: HomeAssistant) -> None:
    """Test one time password."""

    mock_generate_token = loads(
        await async_load_fixture(hass, "generate_token_response.json", DOMAIN)
    )
    mock_otp_response = loads(
        await async_load_fixture(hass, "otp_response.json", DOMAIN)
    )
    with (
        patch(
            "electrasmart.api.ElectraAPI.generate_new_token",
            return_value=mock_generate_token,
        ),
        patch(
            "electrasmart.api.ElectraAPI.validate_one_time_password",
            return_value=mock_otp_response,
        ),
        patch(
            "electrasmart.api.ElectraAPI.fetch_devices",
            return_value=[],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PHONE_NUMBER: "0521234567"},
        )

        # test with required
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_OTP: "1234"}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_one_time_password_api_error(hass: HomeAssistant) -> None:
    """Test one time password."""
    mock_generate_token = loads(
        await async_load_fixture(hass, "generate_token_response.json", DOMAIN)
    )
    with (
        patch(
            "electrasmart.api.ElectraAPI.generate_new_token",
            return_value=mock_generate_token,
        ),
        patch(
            "electrasmart.api.ElectraAPI.validate_one_time_password",
            side_effect=ElectraApiError,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PHONE_NUMBER: "0521234567"},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_OTP: "1234"}
        )

    assert result["type"] is FlowResultType.FORM


async def test_cannot_connect(hass: HomeAssistant) -> None:
    """Test cannot connect."""

    with patch(
        "electrasmart.api.ElectraAPI.generate_new_token",
        side_effect=ElectraApiError,
    ):
        # test with required
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PHONE_NUMBER: "0521234567"},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_invalid_phone_number(hass: HomeAssistant) -> None:
    """Test invalid phone number."""

    mock_invalid_phone_number_response = loads(
        await async_load_fixture(hass, "invalid_phone_number_response.json", DOMAIN)
    )

    with patch(
        "electrasmart.api.ElectraAPI.generate_new_token",
        return_value=mock_invalid_phone_number_response,
    ):
        # test with required
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PHONE_NUMBER: "0521234567"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"phone_number": "invalid_phone_number"}


async def test_invalid_auth(hass: HomeAssistant) -> None:
    """Test invalid auth."""

    mock_generate_token_response = loads(
        await async_load_fixture(hass, "generate_token_response.json", DOMAIN)
    )
    mock_invalid_otp_response = loads(
        await async_load_fixture(hass, "invalid_otp_response.json", DOMAIN)
    )

    with (
        patch(
            "electrasmart.api.ElectraAPI.generate_new_token",
            return_value=mock_generate_token_response,
        ),
        patch(
            "electrasmart.api.ElectraAPI.validate_one_time_password",
            return_value=mock_invalid_otp_response,
        ),
    ):
        # test with required
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PHONE_NUMBER: "0521234567"},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_OTP: "1234"}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == CONF_OTP
    assert result["errors"] == {CONF_OTP: "invalid_auth"}


def _locked_out_entry() -> MockConfigEntry:
    """An entry whose account the vendor has locked out."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="0521234567",
        data={
            CONF_TOKEN: "token",
            CONF_IMEI: "2b950000024051000000000000000000",
            CONF_PHONE_NUMBER: "0521234567",
        },
    )


async def test_reauth(hass: HomeAssistant) -> None:
    """Signing in again clears the lockout without removing the entry."""
    entry = _locked_out_entry()
    entry.add_to_hass(hass)

    mock_generate_token = loads(
        await async_load_fixture(hass, "generate_token_response.json", DOMAIN)
    )
    mock_otp_response = loads(
        await async_load_fixture(hass, "otp_response.json", DOMAIN)
    )

    with (
        patch(
            "electrasmart.api.ElectraAPI.generate_new_token",
            return_value=mock_generate_token,
        ) as mock_send_otp,
        patch(
            "electrasmart.api.ElectraAPI.validate_one_time_password",
            return_value=mock_otp_response,
        ),
        patch("electrasmart.api.ElectraAPI.fetch_devices", return_value=[]),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

        # The phone number is already known, so only the code is asked for.
        mock_send_otp.assert_awaited_once_with(
            "0521234567", "2b950000024051000000000000000000"
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_OTP: "1234"}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data[CONF_TOKEN] == "ec7a0db6c1f148ca8c0f48aabb5f8150"


async def test_reauth_cannot_connect(hass: HomeAssistant) -> None:
    """A failure to send the code is reported on the form."""
    entry = _locked_out_entry()
    entry.add_to_hass(hass)

    with patch(
        "electrasmart.api.ElectraAPI.generate_new_token",
        side_effect=ElectraApiError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_reauth_invalid_code(hass: HomeAssistant) -> None:
    """A rejected code keeps the entry as it was."""
    entry = _locked_out_entry()
    entry.add_to_hass(hass)

    mock_generate_token = loads(
        await async_load_fixture(hass, "generate_token_response.json", DOMAIN)
    )
    mock_invalid_otp_response = loads(
        await async_load_fixture(hass, "invalid_otp_response.json", DOMAIN)
    )

    with (
        patch(
            "electrasmart.api.ElectraAPI.generate_new_token",
            return_value=mock_generate_token,
        ),
        patch(
            "electrasmart.api.ElectraAPI.validate_one_time_password",
            return_value=mock_invalid_otp_response,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": config_entries.SOURCE_REAUTH,
                "entry_id": entry.entry_id,
            },
            data=entry.data,
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_OTP: "1234"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {CONF_OTP: "invalid_auth"}
    assert entry.data[CONF_TOKEN] == "token"

import base64
from unittest.mock import patch

from chalice.app import AuthRequest

from alfred.auth.basic_auth_cached_authorizer import basic_auth_cached_authorizer


def test_basic_auth_cached_authorizer_authorized(
    dynamo_setup, basic_auth_token_valid, basic_auth_user
):
    auth_request = AuthRequest(
        auth_type="GET", token=basic_auth_token_valid, method_arn=""
    )

    auth_response = basic_auth_cached_authorizer(auth_request=auth_request)

    assert auth_response.routes == basic_auth_user.routes
    assert auth_response.principal_id == basic_auth_user.username


def test_basic_auth_cached_authorizer_unauthorized(
    dynamo_setup, basic_auth_token_invalid
):
    auth_request = AuthRequest(
        auth_type="GET", token=basic_auth_token_invalid, method_arn=""
    )

    auth_response = basic_auth_cached_authorizer(auth_request=auth_request)
    assert auth_response.routes == []
    assert auth_response.principal_id == "fake_user"


@patch("alfred.auth.basic_auth_cached_authorizer.Cache.get")
def test_basic_auth_cached_authorizer_cached_key(
    mock_cache_get, dynamo_setup, basic_auth_token_valid, basic_auth_user
):
    mock_cache_get.return_value = {
        "username": basic_auth_user.username,
        "password": basic_auth_user.password,
        "routes": "fake_routes",
    }

    auth_request = AuthRequest(
        auth_type="GET", token=basic_auth_token_valid, method_arn=""
    )

    auth_response = basic_auth_cached_authorizer(auth_request=auth_request)

    mock_cache_get.assert_called_once_with("alfred_basic_auth_admin", None)
    assert auth_response.routes == "fake_routes"
    assert auth_response.principal_id == basic_auth_user.username


@patch("alfred.auth.basic_auth_cached_authorizer.Cache.get")
def test_basic_auth_cached_authorizer_wrong_password(
    mock_cache_get, dynamo_setup, basic_auth_user
):
    basic_auth = f"{basic_auth_user.username}:0000"
    auth64 = base64.b64encode(bytes(basic_auth, "utf-8"))
    token = f"Basic {auth64.decode('utf-8')}"

    mock_cache_get.return_value = {
        "username": basic_auth_user.username,
        "password": basic_auth_user.password,
        "routes": basic_auth_user.routes,
    }

    auth_request = AuthRequest(auth_type="GET", token=token, method_arn="")

    auth_response = basic_auth_cached_authorizer(auth_request=auth_request)
    CACHE_KEY = f"alfred_basic_auth_{basic_auth_user.username}"
    mock_cache_get.assert_called_once_with(CACHE_KEY, None)
    assert auth_response.routes == []
    assert auth_response.principal_id == basic_auth_user.username


@patch("alfred.auth.basic_auth_cached_authorizer.Cache")
def test_basic_auth_cached_authorizer_has_no_cache(
    mock_cache, dynamo_setup, basic_auth_token_valid, basic_auth_user
):
    mock_cache.get.return_value = None

    auth_request = AuthRequest(
        auth_type="GET", token=basic_auth_token_valid, method_arn=""
    )

    auth_response = basic_auth_cached_authorizer(auth_request=auth_request)

    cached_auth = {
        "username": basic_auth_user.username,
        "password": basic_auth_user.password,
        "routes": basic_auth_user.routes,
    }

    mock_cache.set.assert_called_once_with(
        "alfred_basic_auth_admin", cached_auth, 60 * 60
    )
    assert auth_response.routes == basic_auth_user.routes
    assert auth_response.principal_id == basic_auth_user.username


def test_basic_auth_cached_authorizer_decode_error_token():
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6IjI4YzIzNjY4LT"
    "U1ZDYtNDVlMS05MGZhLTc2NDI5NWY4MjE2OSIsInRva2VuIjpudWxsLCJleHAiOjE2NT"
    "A0MDc0NzJ9.1T_JPXDoMTwNN7ZMdkNiNzFRC8pv_47xBSXTG7Xc2l8"

    auth_request = AuthRequest(auth_type="GET", token=token, method_arn="")
    response = basic_auth_cached_authorizer(auth_request=auth_request)

    assert response.routes == []
    assert response.principal_id is None

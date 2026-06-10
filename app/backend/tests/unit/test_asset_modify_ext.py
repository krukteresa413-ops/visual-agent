"""TDD: ModifyRequest model extension — RED."""
import pytest
from pydantic import ValidationError


def test_modify_request_accepts_operation_field():
    """ModifyRequest 应接受可选的 operation 和 crop_region 字段。"""
    from app.api.asset_routes import ModifyRequest

    # This should NOT raise ValidationError
    req = ModifyRequest(
        asset_type="main_image",
        original={"test": "data"},
        instruction="裁切到正方形",
        operation="crop",
        crop_region={"x": 0, "y": 0, "width": 400, "height": 400},
        brief={"product_name": "test"},
    )
    assert req.operation == "crop"
    assert req.crop_region.x == 0
    assert req.crop_region.y == 0
    assert req.crop_region.width == 400
    assert req.crop_region.height == 400


def test_modify_request_operation_defaults_to_text():
    """不传 operation 时默认为 text（向后兼容）。"""
    from app.api.asset_routes import ModifyRequest

    req = ModifyRequest(
        asset_type="main_image",
        original={"test": "data"},
        instruction="改文案",
        brief={"product_name": "test"},
    )
    assert req.operation == "text"
    assert req.crop_region is None

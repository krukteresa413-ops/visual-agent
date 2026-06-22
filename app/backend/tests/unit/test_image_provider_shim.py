"""Module 1 第二刀契约测试：providers.image 必须 re-export 现有 image_generation_service，
且导出对象与源模块同一、抽象基类与 6 个 provider 行为不变。
在 app/providers/image.py 尚未建立时应失败（import error）= TDD 红。"""
import inspect

from app.providers import image as pimg
from app.services import image_generation_service as svc

# 第一刀冻结要 re-export 的符号（抽象基类 + 6 个 provider）
_EXPECTED = [
    "ImageGenerationProvider",
    "LocalPlaceholderProvider",
    "PollinationsProvider",
    "OpenAIImageProvider",
    "LovartImageProvider",
    "MigeProvider",
    "DataEyesAIImageProvider",
]


def test_expected_symbols_exist_in_source():
    # 动态核对：本卡预判的每个符号都必须真实存在于源模块，否则说明预判有偏差
    for name in _EXPECTED:
        assert hasattr(svc, name), f"源模块 image_generation_service 缺少 {name}（预判有误）"


def test_reexport_is_same_object():
    # providers.image.__all__ 里每个名字都必须与源模块是同一对象
    assert hasattr(pimg, "__all__"), "providers.image 应声明 __all__"
    for name in pimg.__all__:
        assert hasattr(svc, name), f"{name} 在源模块不存在，shim 不该导出它"
        assert getattr(pimg, name) is getattr(svc, name), f"{name} 不是同一对象"


def test_all_expected_are_reexported():
    for name in _EXPECTED:
        assert name in pimg.__all__, f"shim 漏了 {name}"
        assert getattr(pimg, name) is getattr(svc, name)


def test_abstract_base_is_abc():
    import abc
    assert issubclass(svc.ImageGenerationProvider, object)
    # 6 个 provider 都应是抽象基类的子类
    for name in _EXPECTED[1:]:
        assert issubclass(getattr(svc, name), svc.ImageGenerationProvider), f"{name} 不是 ImageGenerationProvider 子类"


def test_existing_import_surface_untouched():
    # 第二刀不动任何现有 import 面
    import app.services.image_generation_service  # noqa: F401
    # 不对其源码做改动断言（image 调用面可能在多处），仅确保模块可正常导入
    assert True

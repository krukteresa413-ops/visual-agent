"""Module 1 第三刀契约测试：providers.video 必须 re-export 现有 video_generation_service，
导出对象与源模块同一、抽象基类与 6 个 provider 行为不变。
在 app/providers/video.py 尚未建立时应失败 = TDD 红。"""

from app.providers import video as pvid
from app.services import video_generation_service as svc

# 第一小步冻结要 re-export 的符号（抽象基类 + 6 个 provider）
_EXPECTED = [
    "VideoGenerationProvider",
    "LocalPlaceholderVideoProvider",
    "RunwayVideoProvider",
    "PikaVideoProvider",
    "LovartVideoProvider",
    "MigeVideoProvider",
    "DataEyesAIVideoProvider",
]


def test_expected_symbols_exist_in_source():
    # 动态核对：预判的每个符号必须真实存在于源模块，否则说明预判有偏差
    for name in _EXPECTED:
        assert hasattr(svc, name), f"源模块 video_generation_service 缺少 {name}（预判有误）"


def test_reexport_is_same_object():
    assert hasattr(pvid, "__all__"), "providers.video 应声明 __all__"
    for name in pvid.__all__:
        assert hasattr(svc, name), f"{name} 在源模块不存在，shim 不该导出它"
        assert getattr(pvid, name) is getattr(svc, name), f"{name} 不是同一对象"


def test_all_expected_are_reexported():
    for name in _EXPECTED:
        assert name in pvid.__all__, f"shim 漏了 {name}"
        assert getattr(pvid, name) is getattr(svc, name)


def test_six_providers_subclass_base():
    for name in _EXPECTED[1:]:
        assert issubclass(getattr(svc, name), svc.VideoGenerationProvider), f"{name} 不是 VideoGenerationProvider 子类"


def test_polling_worker_coupling_untouched():
    # 第一小步不动这条硬耦合：video_polling_worker 仍直接 import DataEyesAIVideoProvider
    import inspect, importlib
    try:
        worker = importlib.import_module("app.services.video_polling_worker")
    except ModuleNotFoundError:
        # 路径若不同则跳过该断言，不让它误红（耦合迁移留第二小步）
        return
    src = inspect.getsource(worker)
    assert "DataEyesAIVideoProvider" in src

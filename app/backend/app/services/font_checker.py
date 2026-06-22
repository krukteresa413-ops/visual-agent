"""
Font license checker service.
"""


class FontLicenseChecker:
    def __init__(self):
        self._free = {"Source Han Sans", "Noto Sans", "Noto Sans CJK"}
        self._restricted = {"Microsoft YaHei", "SimSun", "SimHei"}

    def check(self, font_name):
        if font_name in self._free:
            return {"status": "free"}
        if font_name in self._restricted:
            return {"status": "restricted"}
        return {"status": "unknown"}

    def validate_asset_fonts(self, fonts_used):
        warnings = []
        for font in fonts_used:
            result = self.check(font)
            if result["status"] == "restricted":
                warnings.append(f"{font} requires commercial license")
        return warnings

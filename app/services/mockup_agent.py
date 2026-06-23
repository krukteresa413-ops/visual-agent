"""app/services/mockup_agent.py"""

MOCKUP_TYPES = [
    {"id": "package_box", "width": 1200, "height": 1200, "description": "Product package box"},
    {"id": "phone_screen", "width": 1080, "height": 2340, "description": "Phone screen mockup"},
    {"id": "store_sign", "width": 1600, "height": 2400, "description": "Store sign display"},
]


class MockupAgent:
    def build_prompt(self, mockup_type, product_name, product_image_url):
        spec = self.get_spec(mockup_type)
        return f"{product_name} on {spec['description']}"

    def get_spec(self, mockup_type):
        for t in MOCKUP_TYPES:
            if t["id"] == mockup_type:
                return t
        raise ValueError(f"Unknown mockup type: {mockup_type}")

    def build_request(self, mockup_type, product_name, product_image_url):
        spec = self.get_spec(mockup_type)
        return {
            "prompt": self.build_prompt(mockup_type, product_name, product_image_url),
            "size": f"{spec['width']}x{spec['height']}",
            "mockup_type": mockup_type,
        }

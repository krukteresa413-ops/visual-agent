from app.services.quality_checker import QualityChecker
from PIL import Image
import tempfile, os

img = Image.new('RGB', (200, 200), '#E63946')
path = os.path.join(tempfile.gettempdir(), 'test_red.png')
img.save(path)

checker = QualityChecker(use_gpu=False)
result = checker.check_brand_colors(path, {'primary': '#E63946'}, tolerance=5.0)
print('passed:', result['passed'])
print('dominant:', result['dominant_colors'])
for d in result.get('deviations', []):
    print('  deviation:', d)
if result.get('error'):
    print('  error:', result['error'])
os.unlink(path)

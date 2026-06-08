import io
from PIL import Image

def remove_background(input_path: str, output_path: str) -> dict:
    from rembg import remove
    with open(input_path, 'rb') as f:
        input_data = f.read()
    output_data = remove(input_data)
    img = Image.open(io.BytesIO(output_data)).convert('RGBA')
    white_bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
    white_bg.paste(img, mask=img.split()[3])
    result = white_bg.convert('RGB')
    result.save(output_path, 'JPEG', quality=95)
    return {'input_path': input_path, 'output_path': output_path, 'output_size': f'{result.size[0]}x{result.size[1]}'}

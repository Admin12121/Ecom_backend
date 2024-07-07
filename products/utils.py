from django.core.exceptions import ValidationError
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
import random
import string
from django.utils.text import slugify

def validate_image_format(image):
    if not image.name.lower().endswith('.png'):
        raise ValidationError('Only PNG images are allowed.')

def compress_image(image, format='PNG', quality=85):
    try:
        image_temporary = Image.open(image)
        image_temporary = image_temporary.convert('RGBA' if format == 'PNG' else 'RGB')
        output_io_stream = BytesIO()
        image_temporary.save(output_io_stream, format=format, optimize=True, quality=quality)
        output_io_stream.seek(0)
        image = InMemoryUploadedFile(output_io_stream, 'ImageField', f"{image.name.split('.')[0]}.{format.lower()}", f'image/{format.lower()}', sys.getsizeof(output_io_stream), None)
    except Exception as e:
        raise ValidationError(f'Error processing image: {e}')
    return image

def remove_space(s):
    return "".join(s.split())

def generate_random_code(length=5):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_slug(*args):
    slug_fields = [str(arg).lower() for arg in args if arg]
    slug = '-'.join(map(remove_space, slug_fields))
    return f"{slug}{generate_random_code()}"

def generate_unique_slug(product_name, model):
    base_slug = slugify(product_name)

    base_slug = base_slug[:20]
    random_str = ''.join(random.choices(string.ascii_letters + string.digits + '-_', k=10))
    slug = f"{base_slug}-{random_str}"

    while len(slug) < 30:
        extra_str = ''.join(random.choices(string.ascii_letters + string.digits + '-_', k=1))
        slug = f"{slug}{extra_str}"

    slug = slug[:35]

    while model.objects.filter(productslug=slug).exists():
        random_str = ''.join(random.choices(string.ascii_letters + string.digits + '-_', k=10))
        slug = f"{base_slug}-{random_str}"
        slug = slug[:35]

    return slug
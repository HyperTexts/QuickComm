
from django.forms import ValidationError


def validate_image_upload_format(image):
    if image.content_type not in ['image/png', 'image/jpeg']:
        raise ValidationError('Image must be PNG or JPEG')

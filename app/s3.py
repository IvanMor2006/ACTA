import os, io

import boto3, botocore.exceptions
from botocore.config import Config
from PIL import Image

S3_ENDPOINT = os.getenv('S3_ENDPOINT')
S3_REGION = os.getenv('S3_REGION')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')

PUBLIC_BUCKET_NAME = os.getenv('PUBLIC_BUCKET_NAME')
SUPABASE_PROJECT_REF = os.getenv('SUPABASE_PROJECT_REF')

s3_client = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'},
        max_pool_connections=10,
        connect_timeout=5,
        read_timeout=10,
        retries={'max_attempts': 1}
    )
)

def process_and_upload_image(file, filename, max_size=(800, 800), quality=80):
    try:
        img = Image.open(file)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        output = io.BytesIO()
        img.save(output, format='WEBP', quality=quality)
        output.seek(0)
        filename = f'{filename}.webp'
        s3_client.upload_fileobj(
            output,
            PUBLIC_BUCKET_NAME,
            filename,
            ExtraArgs={'ContentType': 'image/webp'}
        )
        return f'https://{SUPABASE_PROJECT_REF}.supabase.co/storage/v1/object/public/{PUBLIC_BUCKET_NAME}/{filename}'
    except botocore.exceptions.ConnectTimeoutError:
        print('ОШИБКА S3: Таймаут подключения. Проверьте интернет или S3_ENDPOINT.')
        return None
    except botocore.exceptions.ReadTimeoutError:
        print('ОШИБКА S3: Сервер Supabase не ответил вовремя.')
        return None
    except Exception as e:
        print(f'Ошибка обработки картинки: {e}')
        return None
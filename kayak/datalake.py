"""Étape 3 : dépôt des CSV bruts dans le data lake S3 (préfixe raw/).

Lancer : python -m kayak.datalake
"""
import boto3

from kayak.config import CITIES_CSV, HOTELS_CSV, S3_BUCKET


def main() -> None:
    if not S3_BUCKET:
        raise SystemExit("S3_BUCKET manquant dans .env")
    s3 = boto3.client("s3")  # identifiants : ~/.aws/credentials ou variables AWS_*
    for path in (CITIES_CSV, HOTELS_CSV):
        key = f"raw/{path.name}"
        s3.upload_file(str(path), S3_BUCKET, key)
        print(f"-> s3://{S3_BUCKET}/{key}")


if __name__ == "__main__":
    main()

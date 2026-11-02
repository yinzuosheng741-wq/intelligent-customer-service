"""Create local configuration without overwriting existing credentials."""
from pathlib import Path
import re
import secrets


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    target = project / '.env'
    if target.exists():
        print('.env already exists; existing configuration was preserved.')
        return
    config = (project / '.env.example').read_text(encoding='utf-8')
    values = {
        'AUTH_SECRET': secrets.token_urlsafe(36),
        'INTERNAL_API_TOKEN': secrets.token_urlsafe(36),
        'MONGO_INITDB_ROOT_USERNAME': 'customer_service_admin',
        'MONGO_INITDB_ROOT_PASSWORD': secrets.token_urlsafe(24),
        'REDIS_PASSWORD': secrets.token_urlsafe(24),
    }
    values['MONGODB_URI'] = (
        f"mongodb://{values['MONGO_INITDB_ROOT_USERNAME']}:"
        f"{values['MONGO_INITDB_ROOT_PASSWORD']}@localhost:28017/shangzhi?authSource=admin"
    )
    values['REDIS_ADDR'] = f"redis://:{values['REDIS_PASSWORD']}@localhost:26379"
    for key, value in values.items():
        config = re.sub(rf'(?m)^{key}=.*$', key + '=' + value, config)
    target.write_text(config, encoding='utf-8')
    print('Created .env with local random secrets. Configure your model credentials before use.')


if __name__ == '__main__':
    main()

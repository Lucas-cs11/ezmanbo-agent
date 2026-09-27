import os
from dotenv import load_dotenv

load_dotenv()

print('=== 环境变量验证 ===')
checks = [
    ('EZPLM_API_KEY', bool(os.getenv('EZPLM_API_KEY'))),
    ('EZPLM_BASE_URL', os.getenv('EZPLM_BASE_URL')),
    ('ANTHROPIC_API_KEY', bool(os.getenv('ANTHROPIC_API_KEY'))),
    ('ANTHROPIC_MODEL', os.getenv('ANTHROPIC_MODEL')),
    ('DATABASE_URL', bool(os.getenv('DATABASE_URL'))),
]

for key, value in checks:
    status = '✅' if value else '❌'
    display = value if isinstance(value, str) else ('已配置' if value else '未配置')
    print(f'{status} {key}: {display}')

print('\n=== 测试 PostgreSQL 连接 ===')
try:
    from sqlalchemy import create_engine, text
    db_url = os.getenv('DATABASE_URL')
    engine = create_engine(db_url, connect_args={'connect_timeout': 10})
    
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version();'))
        version = result.fetchone()[0]
        print(f'✅ 数据库连接成功')
        print(f'   {version.split(chr(44))[0]}')
        
        result = conn.execute(text("SELECT datname FROM pg_database WHERE datname='ezmanbo';"))
        if result.fetchone():
            print(f'✅ ezmanbo 数据库已存在')
        else:
            print(f'⚠️  ezmanbo 数据库不存在')
            
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')

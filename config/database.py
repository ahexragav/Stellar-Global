
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, Session
# from typing import Generator
# import logging

# # Database connection details
# REMOTE_DB_HOST = 'auroraserverless-db-dbcluster-njvwuuqjvris.cluster-cpmo0s46s9x8.us-east-1.rds.amazonaws.com'
# DATABASE_NAME = 'test'
# DB_USER = 'master'
# DB_PASSWORD = 'Wo9yMaRsPb7C1Bn'

# # Set up logging to capture any issues with the database connection
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Create the engine and sessionmaker, binding to the Aurora PostgreSQL instance directly
# engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{REMOTE_DB_HOST}/{DATABASE_NAME}')
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Setup the Database connection without SSH Tunnel
# def get_db() -> Generator[Session, None, None]:
#     try:
#         # Use the sessionmaker to create a new session
#         db: Session = SessionLocal()
#         try:
#             yield db  # Yield the session to be used in the request
#         finally:
#             db.close()  # Ensure that the session is closed after usage
#     except Exception as e:
#         logger.error(f"Failed to establish database connection: {e}")
#         raise

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base,Session
from typing import Generator

# PostgreSQL connection URL
DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost:5432/new"

# Base ORM class
Base = declarative_base()

# Clear metadata to avoid duplicate table definitions during runtime
Base.metadata.clear()

# Create the database engine
try:
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    print("PostgreSQL Connection successful!")
    connection.close()
except Exception as e:
    print(f"Error connecting to PostgreSQL: {e}")

# Configure session and ORM base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



# Initialize tables in the database
Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, Session
# from sshtunnel import SSHTunnelForwarder
# from typing import Generator
# from config.config import settings
# import logging
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import create_engine

# DATABASE_URL = "mysql+pymysql://root:root@localhost:3306/tapme"


# Base = declarative_base()
# try:
#     engine = create_engine(DATABASE_URL)
#     connection = engine.connect()
#     print("Connection successful!")
#     connection.close()
# except Exception as e:
#     print(f"Error: {e}")



# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base.metadata.create_all(bind=engine)
# # Dependency to get the database session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
# SSH and database connection details
# SSH_HOST = settings.ADDRESS
# SSH_USERNAME = 'ubuntu'
# SSH_PRIVATE_KEY = 'C:/Users/Ahex-Tech/Documents/tapme/app/saitest.pem'
# REMOTE_DB_HOST = 'auroraserverless-db-dbcluster-njvwuuqjvris.cluster-cpmo0s46s9x8.us-east-1.rds.amazonaws.com'
# DATABASE_NAME = 'test'
# DB_USER = 'master'
# DB_PASSWORD = 'Wo9yMaRsPb7C1Bn'

# # Set up logging to capture any issues with the SSH tunnel or database connection
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Create the engine and sessionmaker, binding to the local SSH tunnel port
# engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@127.0.0.1:6543/{DATABASE_NAME}')
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Setup the SSH Tunnel and Database connection
# def get_db() -> Generator[Session, None, None]:
#     try:
#         # Start the SSH tunnel
#         with SSHTunnelForwarder(
#             (SSH_HOST, 22),
#             ssh_private_key=SSH_PRIVATE_KEY,
#             ssh_username=SSH_USERNAME,
#             remote_bind_address=(REMOTE_DB_HOST, 5432),
#             local_bind_address=('127.0.0.1', 6543)
#         ) as server:
#             # SSH tunnel is now active
#             logger.info("SSH tunnel established")

#             # Use the sessionmaker to create a new session
#             db: Session = SessionLocal()
#             try:
#                 yield db  # Yield the session to be used in the request
#             finally:
#                 db.close()  # Ensure that the session is closed after usage
#     except Exception as e:
#         logger.error(f"Failed to establish SSH tunnel or database connection: {e}")
#         raise


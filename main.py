import uvicorn
from auth import authrouter
from users import userrouter
from models import usermodels, productmodels
from product import productrouter
from fastapi.middleware.cors import CORSMiddleware
from config.config import settings
from fastapi import FastAPI,Request
from models.usermodels import Base
from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError
from mangum import Mangum
from tapme_social_media import my_cards,my_card_sticker,tap_events,individual_card,reports,active_card
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from BuyProduct import buy_cards,product_details,add_product
from config.database import engine, Base


app = FastAPI(
    title="TapMe API",
    description="This is a TapMe API application with Swagger docs.",
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "API Support",
        "url": "http://example.com/contact/",
        "email": "support@example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
    },
)
app.add_middleware(SessionMiddleware, secret_key="your-secret-key") 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this based on your requirements
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static files directory

# Mount the static files directory for serving images
app.mount("/images", StaticFiles(directory="C:/Users/Ahex-Tech/Documents/tapme/app/images"), name="images")


@app.on_event("startup")
async def startup_event():
    for table in Base.metadata.sorted_tables:
        print(f"Creating table: {table.name}")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")



# def create_ssh_tunnel():
#     try:
#         ssh_pkey = 'C:/Users/Ahex-Tech/Documents/tapme/app/saitest.pem'
#         return SSHTunnelForwarder(
#             (settings.ADDRESS, 22),
#             ssh_pkey=ssh_pkey,
#             ssh_username="ubuntu",
#             remote_bind_address=('auroraserverless-db-dbcluster-njvwuuqjvris.cluster-cpmo0s46s9x8.us-east-1.rds.amazonaws.com', 5432),
#             local_bind_address=('127.0.0.1', 6543)
#         )
#     except BaseSSHTunnelForwarderError as e:
#         print("SSH Tunnel Forwarder Error:", e)
#         raise
#     except Exception as e:
#         print("An error occurred while creating the SSH tunnel:", e)
#         raise



# @app.on_event("startup")
# async def startup_event():
#     try:
#         # Establish the SSH tunnel
#         server = create_ssh_tunnel()
#         server.start()
#         print(f"SSH tunnel established on {server.local_bind_port}")

#         # Create engine and tables
#         engine = create_engine(
#             f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@127.0.0.1:{server.local_bind_port}/{DATABASE_NAME}',
#             connect_args={"connect_timeout": 10},
#             pool_pre_ping=True
#         )
#         usermodels.Base.metadata.create_all(bind=engine)
#         productmodels.Base.metadata.create_all(bind=engine)
#         print("Database tables created.")

#     except BaseSSHTunnelForwarderError as e:
#         print("SSH Tunnel Error:", e)
#     except Exception as e:
#         print("Database connection failed:", e)



app.include_router(userrouter.router)
app.include_router(productrouter.router)
app.include_router(authrouter.router)
app.include_router(my_cards.router)
app.include_router(tap_events.router)
app.include_router(my_card_sticker.router)
app.include_router(individual_card.router)
app.include_router(reports.router)
app.include_router(active_card.router)
app.include_router(buy_cards.router)
app.include_router(product_details.router)
app.include_router(add_product.router)

# Wrap FastAPI app with Mangum for AWS Lambda
handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app)

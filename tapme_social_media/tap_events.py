from fastapi import APIRouter, Depends,HTTPException
from fastapi.responses import RedirectResponse,JSONResponse
from sqlalchemy.orm import Session
from config.database import get_db
from config.config import settings
from models.productmodels import TapCard,ActiveCard,Customer
from config.database import get_db
from fastapi import Request
from models.productmodels import TapEvent,AddCard
import csv
from fastapi.responses import StreamingResponse
from io import StringIO
from datetime import datetime
from utils.location_time import get_location_from_ip
import httpx
from fastapi.responses import FileResponse
import os
router = APIRouter(tags=["tap events"])



# @router.get("/tap/{id}")
# async def tap_card(id: str, request: Request, db: Session = Depends(get_db)):
#     print(id)
#     # Check if the TapCard exists
#     tap_card = db.query(TapCard).filter(TapCard.serial == id).first()
#     if not tap_card:
#         raise HTTPException(status_code=404, detail="TapCard not found")
    
#     # Check if the ActiveCard exists
#     active_card = db.query(AddCard).filter(AddCard.tapcard_serial == id).first()
#     if not active_card:
#         raise HTTPException(status_code=404, detail="ActiveCard not found")
    
#     active_status = active_card.active
#     if active_status == "no":
#         return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?id={id}")
    
#     # Check if the Customer exists
#     customer = db.query(Customer).filter(Customer.customer_id == active_card.customer_id).first()
#     if not customer:
#         raise HTTPException(status_code=404, detail="Customer not found")
    
#     # Get the social media URL
#     social_media_url = active_card.card_data
#     if not social_media_url:
#         raise HTTPException(status_code=404, detail="Social Media URL not found")
    
#     # Retrieve request details
#     ip_address = request.client.host
#     user_agent = request.headers.get('User-Agent')
#     location = get_location_from_ip(ip_address)
    
#     # Log the Tap Event with current UTC date and time
#     tap_event = TapEvent(
#         customer_id=active_card.customer_id,
#         tapcard_serial=id,
#         ip_address=ip_address,
#         user_agent=user_agent,
#         location=location,
#         timestamp=datetime.utcnow()
#     )
#     db.add(tap_event)
#     db.commit()

#     # Create a temporary directory if it doesn't exist
#     temp_directory = os.path.join(os.getcwd(), "temp")
#     os.makedirs(temp_directory, exist_ok=True)
#     file_path = os.path.join(temp_directory, f"{id}_website_content.html")

#     # Fetch the website content
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.get(social_media_url)
#             response.raise_for_status()
        
#         with open(file_path, "w", encoding="utf-8") as file:
#             file.write(response.text)

#         # Respond with a downloadable file
#         return FileResponse(
#             file_path,
#             media_type="text/html",
#             filename=f"{id}_website_content.html"
#         )
#     except httpx.RequestError as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to fetch the website content: {str(e)}"
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"An error occurred while processing the request: {str(e)}"
#         )
#     finally:
#         # Cleanup: remove the temporary file after serving it
#         if os.path.exists(file_path):
#             os.remove(file_path)

# # Your tap_card endpoint with location handling
@router.get("/tap/{id}")
async def tap_card(id: str, request: Request, db: Session = Depends(get_db)):
    print(id)
    # Check if the TapCard exists
    tap_card = db.query(TapCard).filter(TapCard.serial == id).first()
    if not tap_card:
        raise HTTPException(status_code=404, detail="TapCard not found")
    
    # Check if the ActiveCard exists
    active_card = db.query(AddCard).filter(AddCard.tapcard_serial == id).first()
    active_status=active_card.active
    if active_status=="no":
        # response_data = {"url": f"{settings.FRONTEND_URL}/login?id={id}"}
        # return JSONResponse(content=response_data)
        
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?id={id}")
    # Check if the Customer exists
    customer = db.query(Customer).filter(Customer.customer_id == active_card.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get the social media URL
    social_media_url = active_card.card_data
    if not social_media_url:
        raise HTTPException(status_code=404, detail="Social Media URL not found")
   
    # Retrieve request details
    ip_address = request.client.host
    user_agent = request.headers.get('User-Agent')
    location = get_location_from_ip(ip_address)  # Function to get location from IP
    
    # Log the Tap Event with current UTC date and time
    tap_event = TapEvent(
        customer_id=active_card.customer_id,
        tapcard_serial=id,
        ip_address=ip_address,
        user_agent=user_agent,
        location=location,
        timestamp=datetime.utcnow()  # Store the current UTC timestamp
    )
    db.add(tap_event)
    db.commit()
    print(social_media_url)
    return JSONResponse(
        content={
            "url": social_media_url,
            "message": "Redirect successfully",
            "location": location  # Include location in the response
        },
        status_code=200
    )

@router.get("/report/summary/{tapcard_serial}")
async def get_tap_summary(tapcard_serial: str, db: Session = Depends(get_db)):
    total_taps = db.query(TapEvent).filter(TapEvent.tapcard_serial == tapcard_serial).count()
    
    return {
        "tapcard_serial": tapcard_serial,
        "total_taps": total_taps
    }


@router.get("/report/detailed/{tapcard_serial}")
async def get_detailed_report(tapcard_serial: str, db: Session = Depends(get_db)):
    tap_events = db.query(TapEvent).filter(TapEvent.tapcard_serial == tapcard_serial).all()
    
    detailed_report = []
    for event in tap_events:
        detailed_report.append({
            "timestamp": event.timestamp,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent
        })
    
    return {
        "tapcard_serial": tapcard_serial,
        "total_taps": len(tap_events),
        "history": detailed_report
    }




@router.get("/report/download/{tapcard_serial}")
async def download_report(tapcard_serial: str, db: Session = Depends(get_db)):
    tap_events = db.query(TapEvent).filter(TapEvent.tapcard_serial == tapcard_serial).all()

    # Create a CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "IP Address", "User Agent"])
    for event in tap_events:
        writer.writerow([event.timestamp, event.ip_address, event.user_agent])

    output.seek(0)
    
    return StreamingResponse(output, media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename={tapcard_serial}_report.csv"
    })

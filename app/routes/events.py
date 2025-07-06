from fastapi import APIRouter, Depends, HTTPException, status,Body,Query,Path, Response
from ..model.event import Event, EventOut, EventDB, EventService
from ..database import SessionDep
from typing import Annotated
from  .user import get_current_active_user, UserIn

event_router = APIRouter(tags=["Event"])

@event_router.post("/event",response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(event: Annotated[Event, Body()], current_user: Annotated[UserIn, Depends(get_current_active_user)], session: SessionDep ):
    '''Create a new event in the database'''
    event.sport = event.sport.lower()
    eventDB =  EventDB(**event.model_dump(), organizer_id=current_user.id, active=True)
    
    try:
        saved_event = EventService.save_event(eventDB, session)
        return saved_event
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating event")    

@event_router.get("/event",response_model=list[EventOut], status_code=status.HTTP_200_OK)
async def get_events(session: SessionDep,sport: str | None = None, skip:int = 0, limit:int = 100):
    try:
        if sport:
            sport = sport.lower()
        events = EventService.get_events(session, sport , skip=skip, limit=limit)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching events: {e}")   
    

@event_router.get("/event/me", status_code=status.HTTP_200_OK, description="Get events for current user",response_model=list[EventOut])
async def get_events_by_user(session: SessionDep,current_user:Annotated[UserIn, Depends(get_current_active_user)],  skip: int = 0, limit: int = 100):
    try:
        events = EventService.get_events_by_user(session, current_user.id, skip=skip, limit=limit)
        if events:
            return events
        else:
            return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching events for user: {e}")    

@event_router.get("/event/{event_id}", status_code=status.HTTP_200_OK, description="Get event by ID") 
async def get_event(event_id: Annotated[int,Path(description="Event id",ge=1)], session: SessionDep,current_user: Annotated[UserIn, Depends(get_current_active_user)], response: Response):
    try:
        event = EventService.get_event_by_id(event_id, current_user.id, session)
        if event:
            return EventOut(**event.model_dump())
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {"detail": "Event not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching event: {e}")

@event_router.delete("/event/{event_id}",status_code= status.HTTP_200_OK, description="Delete event by ID")
async def delete_event(event_id: Annotated[int,Path(description="Event id",ge=1)], session: SessionDep,current_user: Annotated[UserIn, Depends(get_current_active_user)], response: Response):
    try:
        delete_event = EventService.delete_event(event_id,session, current_user.id)
        if delete_event:
            return {"detail": "Event deleted successfully"}
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {"detail": "Event not found or you are not the organizer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting event: {e}")

@event_router.put("/event/{event_id}",status_code = status.HTTP_200_OK, description="Update event by ID")
async def update_event(event_id: Annotated[int, Path(description="Event Id",ge=1)], event: Annotated[Event, Body()],session: SessionDep,current_user: Annotated[UserIn, Depends(get_current_active_user)],response: Response):
    try:
        event.sport = event.sport.lower()
        updated_event = EventService.update_event(event_id, current_user.id, event, session)
        if updated_event:
            return EventOut(**updated_event.model_dump())
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating event: {e}")
    
@event_router.post("/event/{event_id}/participate", status_code=status.HTTP_201_CREATED, description="Participate in an event")
async def add_participant(event_id: Annotated[int, Path(description="Event Id",ge=1)],session: SessionDep,current_user: Annotated[UserIn, Depends(get_current_active_user)],response: Response):
    try:
        participant_added = EventService.add_participant(event_id,current_user.id,session)
        if participant_added:
            return {"detail":"Particpant added successfully"}
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return{"detail": "Event not found or you are already participating in this event"}
    except Exception as e:    
        raise HTTPException(status_code=500, detail=f"Error participating in event: {e}") 

@event_router.delete("/event/{event_id}/participate",status_code=status.HTTP_200_OK, description="Remove participation from an event")
async def remove_participant(event_id: Annotated[int, Path(description="Event Id",ge=1)],session: SessionDep, current_user: Annotated[UserIn, Depends(get_current_active_user)],response: Response):
    try:
        removed_participant = EventService.remove_participant(event_id, current_user.id, session)
        if removed_participant:
            return {"detail": "Participation removed successfully"}
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {"detail": "Event not found or you are not participating in this event"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing participation from event: {e}")
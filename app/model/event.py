from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime,timezone
from sqlmodel import SQLModel, Session, Field as sqlmodel_Field,select

class Event(BaseModel):
    description: str = Field(description="Event name", min_length=1, max_length=300)    
    date: datetime = Field(description="Event date and time")
    ubication: str = Field(description="Event location", min_length=1, max_length=300)
    sport: str = Field(description="Sport type", min_length=1, max_length=100)


class EventOut(Event):
    id: int

class EventDB(SQLModel, table= True):
    id:int | None = sqlmodel_Field(default=None, primary_key=True)
    organizer_id: int | None = sqlmodel_Field(default=None, foreign_key="userdb.id")
    description: str = sqlmodel_Field(min_length=1, max_length=300)
    date: datetime
    ubication: str = sqlmodel_Field(min_length=1, max_length=300)
    sport: str = sqlmodel_Field(min_length=1, max_length=100)
    active: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc))

class EventParticipationDB(SQLModel, table=True):
    event_id_fk: int = sqlmodel_Field(foreign_key="eventdb.id", primary_key=True)
    user_id_fk: int = sqlmodel_Field(foreign_key="userdb.id", primary_key=True)    
    active: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc))

class EventService:
    @staticmethod
    def save_event(event: EventDB, session:Session)-> EventOut | None:
        try:
            session.add(event)
            session.commit()
            session.refresh(event)
            return event
        except Exception as e:
            session.rollback()
            print(f"Error saving event: {e}")
            return None
    @staticmethod
    def get_events(session: Session, sport: str, skip: int = 0, limit: int = 100) -> list[EventDB]:
        try:
            now = datetime.now(timezone.utc)
            if sport:
                # if there is a filter by sport
                statement = select(EventDB).offset(skip).limit(limit).where(EventDB.active == True, EventDB.date >= now, EventDB.sport == sport)
            else:    
                statement = select(EventDB).offset(skip).limit(limit).where(EventDB.active == True,EventDB.date >= now)
            events = session.exec(statement)
            return events
        except Exception as e:
            print(f"Error fetching events: {e}")
            return []
    @staticmethod
    def get_event_by_id(event_id:int,user_id: int,session: Session) -> EventDB | None:
        try:
           
            statement = select(EventDB).where(EventDB.id == event_id,EventDB.organizer_id == user_id)
            event = session.exec(statement).first()
            if event:
                return event
            return None
        except Exception as e:
            print(f"Error fetching event by id: {e}")
            return None   
    @staticmethod
    def delete_event(event_id: int, session: Session, user_id:int) -> bool:
        try: 
            statement  = select(EventDB).where(EventDB.id == event_id, EventDB.organizer_id == user_id, EventDB.active == True)
            event = session.exec(statement).first()
            if event:
                event.active = False
                event.updated_at = datetime.now(timezone.utc)
                session.add(event)
                session.commit()
                return True 
        except Exception as e:
            print(f"Error deleting event: {e}")
            return False   
    @staticmethod
    def get_events_by_user(session: Session,user_id:int, skip: int = 0, limit: int = 100)->list[EventDB]:
        try:
            statement = select(EventDB).where(EventDB.organizer_id == user_id,EventDB.active == True).offset(skip).limit(limit)
            events = session.exec(statement)
            return events
        except Exception as e:
            print(f"Error fetching events for user: {e}")
            return []
    @staticmethod
    def update_event(event_id:int, user_id:int,event: Event,session:Session)->EventDB | None:

        #First check if the event exists and belongs to the user
        try:
            statement = select(EventDB).where(EventDB.id == event_id, EventDB.organizer_id == user_id)
            eventDB:EventDB = session.exec(statement).first()
            if eventDB and eventDB.active:
                #Event exist in the databse
                eventDB.description = event.description
                eventDB.date = event.date
                eventDB.ubication = event.ubication
                eventDB.sport = event.sport
                eventDB.updated_at = datetime.now(timezone.utc)
                try:
                    session.add(eventDB)
                    session.commit()
                    session.refresh(eventDB)
                    return eventDB
                except Exception as e:
                    session.rollback()
                    print(f"Error updating event in database: {e}")
                    return None
            else:
                return None  
        except Exception as e:
            print(f"Error updating event: {e}")
            return None    
    @staticmethod
    def add_participant(event_id: int, user_id:int,session: Session) -> bool:
        try:
            #First check if the event exists and is active
            now = datetime.now(timezone.utc)
            statement = select(EventDB).where(EventDB.id == event_id, EventDB.active == True, EventDB.date >= now)
            event = session.exec(statement).first()
            if event:
                #Check if the user is already a participant
                statement = select(EventParticipationDB).where(EventParticipationDB.event_id_fk == event_id,EventParticipationDB.user_id_fk == user_id)
                participant = session.exec(statement).first()
                if not participant:
                    new_participant = EventParticipationDB(event_id_fk=event_id, user_id_fk=user_id, active=True,created_at= datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
                    try:
                        session.add(new_participant)
                        session.commit()
                        session.refresh(new_participant)
                        return True
                    except Exception as e:
                        session.rollback()
                        print("Error adding participant to database: ", e) 
                        return True   
                else:
                    return True

            else:
                return False
        except Exception as e:
            print(f"Error adding participant: {e}")
            return False    
    @staticmethod
    def remove_participant(event_id:int, user_id:int, session: Session) -> bool:
        try:
            #First check if the event exists and is active
            now = datetime.now(timezone.utc)
            statement = select(EventDB).where(EventDB.id == event_id, EventDB.active == True, EventDB.date >= now)
            event = session.exec(statement).first()

            if event:
                #Check if the user is a participant
                statement = select(EventParticipationDB).where(EventParticipationDB.event_id_fk == event_id, EventParticipationDB.user_id_fk == user_id,EventParticipationDB.active == True)
                participant: EventParticipationDB = session.exec(statement).first()
                if participant:
                    participant.active = False
                    participant.updated_at = datetime.now(timezone.utc)
                    try:
                        session.add(participant)
                        session.commit()
                        return True
                    except Exception as e:
                        session.rollback()
                        print(f"Error removing participant from database: {e}")
                        return False
                else:
                    print("Participant not found or already inactive")
                    return False
        except Exception as e:
            print(f"Error removing participant: {e}")
            return False
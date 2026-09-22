from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Problem, ProblemNote, User
from ..schemas import NoteOut, NoteUpdate
from .auth import get_current_user

router = APIRouter(prefix="/notes", tags=["notes"])

@router.get("/{problem_id}", response_model=NoteOut)
def get_note(problem_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    note = db.query(ProblemNote).filter(ProblemNote.problem_id == problem_id, ProblemNote.user_id == current_user.id).first()
    if not note:
        return NoteOut(id=None, problem_id=problem_id, idea="", key_points="", complexity="", pitfalls="", summary="")
    return note

@router.put("/{problem_id}", response_model=NoteOut)
def upsert_note(problem_id: int, payload: NoteUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    note = db.query(ProblemNote).filter(ProblemNote.problem_id == problem_id, ProblemNote.user_id == current_user.id).first()
    if not note:
        note = ProblemNote(problem_id=problem_id, user_id=current_user.id)
        db.add(note)
    note.idea = payload.idea
    note.key_points = payload.key_points
    note.complexity = payload.complexity
    note.pitfalls = payload.pitfalls
    note.summary = payload.summary
    db.commit()
    db.refresh(note)
    return note

"""
KSP Crime Analytics — Lookups Router
Provides dropdown/filter data for the frontend (districts, stations, crime types, etc.)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import (
    District, Unit, CrimeHead, CrimeSubHead,
    CaseStatusMaster, GravityOffence, CaseCategory
)
from app.schemas import (
    DistrictOut, UnitOut, CrimeHeadOut, CrimeSubHeadOut,
    CaseStatusOut, GravityOut, CrimeCategoryOut
)

router = APIRouter(prefix="/api/lookups", tags=["Lookups"])


@router.get("/districts", response_model=list[DistrictOut])
async def get_districts(db: AsyncSession = Depends(get_db)):
    """List all districts for filter dropdowns."""
    result = await db.execute(
        select(District).where(District.active == True).order_by(District.districtname)
    )
    return result.scalars().all()


@router.get("/stations", response_model=list[UnitOut])
async def get_stations(db: AsyncSession = Depends(get_db)):
    """List all police stations."""
    result = await db.execute(
        select(Unit).where(Unit.active == True).order_by(Unit.unitname)
    )
    return result.scalars().all()


@router.get("/crime-heads", response_model=list[CrimeHeadOut])
async def get_crime_heads(db: AsyncSession = Depends(get_db)):
    """List all major crime head categories."""
    result = await db.execute(
        select(CrimeHead).where(CrimeHead.active == True).order_by(CrimeHead.crimegroupname)
    )
    return result.scalars().all()


@router.get("/crime-sub-heads", response_model=list[CrimeSubHeadOut])
async def get_crime_sub_heads(db: AsyncSession = Depends(get_db)):
    """List all crime sub-heads (specific crime types)."""
    result = await db.execute(
        select(CrimeSubHead).order_by(CrimeSubHead.crimeheadname)
    )
    return result.scalars().all()


@router.get("/case-statuses", response_model=list[CaseStatusOut])
async def get_case_statuses(db: AsyncSession = Depends(get_db)):
    """List all case status options."""
    result = await db.execute(select(CaseStatusMaster))
    return result.scalars().all()


@router.get("/gravity-levels", response_model=list[GravityOut])
async def get_gravity_levels(db: AsyncSession = Depends(get_db)):
    """List all offence gravity levels."""
    result = await db.execute(select(GravityOffence))
    return result.scalars().all()


@router.get("/case-categories", response_model=list[CrimeCategoryOut])
async def get_case_categories(db: AsyncSession = Depends(get_db)):
    """List all case categories (FIR, UDR, PAR, etc.)."""
    result = await db.execute(select(CaseCategory))
    return result.scalars().all()

"""
KSP Crime Analytics — Cases Router
Endpoints for listing, filtering, and retrieving FIR case details.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import date

from app.database import get_db
from app.models import (
    CaseMaster, Victim, Accused, ComplainantDetails,
    ArrestSurrender, ActSectionAssociation, CrimeHead,
    CrimeSubHead, CaseStatusMaster, GravityOffence,
    CaseCategory, Unit, District, Employee, Court,
    InvOccuranceTime
)
from app.schemas import (
    CaseListItem, CaseDetail, PaginatedCases,
    VictimOut, AccusedOut, ComplainantOut, ArrestOut, ActSectionOut
)

router = APIRouter(prefix="/api/cases", tags=["Cases"])


@router.get("", response_model=PaginatedCases)
async def list_cases(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    district_id: Optional[int] = None,
    station_id: Optional[int] = None,
    status_id: Optional[int] = None,
    crime_head_id: Optional[int] = None,
    crime_sub_head_id: Optional[int] = None,
    gravity_id: Optional[int] = None,
    category_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
):
    """
    List FIR cases with filtering and pagination.
    Supports filtering by district, station, status, crime type, gravity, category, and date range.
    """
    # Base query with joins for resolved names
    query = (
        select(
            CaseMaster.casemasterid,
            CaseMaster.crimeno,
            CaseMaster.caseno,
            CaseMaster.crimeregistereddate,
            CaseMaster.latitude,
            CaseMaster.longitude,
            District.districtname.label("district_name"),
            Unit.unitname.label("station_name"),
            CrimeSubHead.crimeheadname.label("crime_type"),
            CrimeHead.crimegroupname.label("crime_group"),
            CaseStatusMaster.casestatusname.label("case_status"),
            GravityOffence.lookupvalue.label("gravity"),
            CaseCategory.lookupvalue.label("category"),
        )
        .join(Unit, CaseMaster.policestationid == Unit.unitid, isouter=True)
        .join(District, Unit.districtid == District.districtid, isouter=True)
        .join(CrimeSubHead, CaseMaster.crimeminorheadid == CrimeSubHead.crimesubheadid, isouter=True)
        .join(CrimeHead, CaseMaster.crimemajorheadid == CrimeHead.crimeheadid, isouter=True)
        .join(CaseStatusMaster, CaseMaster.casestatusid == CaseStatusMaster.casestatusid, isouter=True)
        .join(GravityOffence, CaseMaster.gravityoffenceid == GravityOffence.gravityoffenceid, isouter=True)
        .join(CaseCategory, CaseMaster.casecategoryid == CaseCategory.casecategoryid, isouter=True)
    )

    # Count query
    count_query = select(func.count()).select_from(CaseMaster)

    # Apply filters
    filters = []
    if district_id:
        filters.append(District.districtid == district_id)
    if station_id:
        filters.append(CaseMaster.policestationid == station_id)
    if status_id:
        filters.append(CaseMaster.casestatusid == status_id)
    if crime_head_id:
        filters.append(CaseMaster.crimemajorheadid == crime_head_id)
    if crime_sub_head_id:
        filters.append(CaseMaster.crimeminorheadid == crime_sub_head_id)
    if gravity_id:
        filters.append(CaseMaster.gravityoffenceid == gravity_id)
    if category_id:
        filters.append(CaseMaster.casecategoryid == category_id)
    if date_from:
        filters.append(CaseMaster.crimeregistereddate >= date_from)
    if date_to:
        filters.append(CaseMaster.crimeregistereddate <= date_to)
    if search:
        search_filter = f"%{search}%"
        filters.append(
            CaseMaster.crimeno.ilike(search_filter)
            | CaseMaster.brieffacts.ilike(search_filter)
        )

    if filters:
        query = query.where(and_(*filters))
        # For count, we need the same joins when filtering on joined tables
        count_query = (
            select(func.count())
            .select_from(CaseMaster)
            .join(Unit, CaseMaster.policestationid == Unit.unitid, isouter=True)
            .join(District, Unit.districtid == District.districtid, isouter=True)
            .where(and_(*filters))
        )

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply ordering and pagination
    query = (
        query
        .order_by(CaseMaster.crimeregistereddate.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    rows = result.all()

    cases = []
    for row in rows:
        cases.append(CaseListItem(
            casemasterid=row.casemasterid,
            crimeno=row.crimeno,
            caseno=row.caseno,
            crimeregistereddate=row.crimeregistereddate,
            latitude=float(row.latitude) if row.latitude else None,
            longitude=float(row.longitude) if row.longitude else None,
            district_name=row.district_name,
            station_name=row.station_name,
            crime_type=row.crime_type,
            crime_group=row.crime_group,
            case_status=row.case_status,
            gravity=row.gravity,
            category=row.category,
        ))

    total_pages = (total + page_size - 1) // page_size

    return PaginatedCases(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=cases,
    )


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(case_id: int, db: AsyncSession = Depends(get_db)):
    """Get full details of a specific FIR case, including victims, accused, and charges."""

    # Fetch case with joined lookups
    query = (
        select(
            CaseMaster,
            District.districtname.label("district_name"),
            Unit.unitname.label("station_name"),
            Employee.firstname.label("officer_name"),
            CrimeSubHead.crimeheadname.label("crime_type"),
            CrimeHead.crimegroupname.label("crime_group"),
            CaseStatusMaster.casestatusname.label("case_status"),
            GravityOffence.lookupvalue.label("gravity"),
            CaseCategory.lookupvalue.label("category"),
            Court.courtname.label("court_name"),
        )
        .join(Unit, CaseMaster.policestationid == Unit.unitid, isouter=True)
        .join(District, Unit.districtid == District.districtid, isouter=True)
        .join(Employee, CaseMaster.policepersonid == Employee.employeeid, isouter=True)
        .join(CrimeSubHead, CaseMaster.crimeminorheadid == CrimeSubHead.crimesubheadid, isouter=True)
        .join(CrimeHead, CaseMaster.crimemajorheadid == CrimeHead.crimeheadid, isouter=True)
        .join(CaseStatusMaster, CaseMaster.casestatusid == CaseStatusMaster.casestatusid, isouter=True)
        .join(GravityOffence, CaseMaster.gravityoffenceid == GravityOffence.gravityoffenceid, isouter=True)
        .join(CaseCategory, CaseMaster.casecategoryid == CaseCategory.casecategoryid, isouter=True)
        .join(Court, CaseMaster.courtid == Court.courtid, isouter=True)
        .where(CaseMaster.casemasterid == case_id)
    )

    result = await db.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")

    case = row[0]  # CaseMaster object

    # Fetch related entities
    victims_result = await db.execute(
        select(Victim).where(Victim.casemasterid == case_id)
    )
    accused_result = await db.execute(
        select(Accused).where(Accused.casemasterid == case_id)
    )
    complainants_result = await db.execute(
        select(ComplainantDetails).where(ComplainantDetails.casemasterid == case_id)
    )
    arrests_result = await db.execute(
        select(ArrestSurrender).where(ArrestSurrender.casemasterid == case_id)
    )
    act_sections_result = await db.execute(
        select(ActSectionAssociation).where(ActSectionAssociation.casemasterid == case_id)
    )

    return CaseDetail(
        casemasterid=case.casemasterid,
        crimeno=case.crimeno,
        caseno=case.caseno,
        crimeregistereddate=case.crimeregistereddate,
        incidentfromdate=case.incidentfromdate,
        incidenttodate=case.incidenttodate,
        inforeceivedpsdate=case.inforeceivedpsdate,
        latitude=float(case.latitude) if case.latitude else None,
        longitude=float(case.longitude) if case.longitude else None,
        brieffacts=case.brieffacts,
        district_name=row.district_name,
        station_name=row.station_name,
        officer_name=row.officer_name,
        crime_type=row.crime_type,
        crime_group=row.crime_group,
        case_status=row.case_status,
        gravity=row.gravity,
        category=row.category,
        court_name=row.court_name,
        victims=[VictimOut.model_validate(v) for v in victims_result.scalars().all()],
        accused=[AccusedOut.model_validate(a) for a in accused_result.scalars().all()],
        complainants=[ComplainantOut.model_validate(c) for c in complainants_result.scalars().all()],
        arrests=[ArrestOut.model_validate(a) for a in arrests_result.scalars().all()],
        act_sections=[ActSectionOut.model_validate(a) for a in act_sections_result.scalars().all()],
    )

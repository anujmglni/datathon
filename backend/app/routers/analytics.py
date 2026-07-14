"""
KSP Crime Analytics — Analytics Router
Dashboard statistics, crime trends, hotspot data, and distribution charts.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract, case, cast, Float
from typing import Optional
from datetime import date

from app.database import get_db
from app.models import (
    CaseMaster, Victim, Accused, ArrestSurrender,
    ChargesheetDetails, CrimeHead, CrimeSubHead,
    CaseStatusMaster, GravityOffence, CaseCategory,
    Unit, District
)
from app.schemas import (
    OverviewStats, CrimeTrendItem, DistrictCrimeItem,
    CrimeTypeItem, StatusDistributionItem, HotspotPoint
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", response_model=OverviewStats)
async def get_overview(db: AsyncSession = Depends(get_db)):
    """Dashboard overview — key statistics at a glance."""

    total_cases = (await db.execute(select(func.count()).select_from(CaseMaster))).scalar()

    # FIRs specifically (category 1)
    total_firs = (await db.execute(
        select(func.count()).select_from(CaseMaster).where(CaseMaster.casecategoryid == 1)
    )).scalar()

    total_victims = (await db.execute(select(func.count()).select_from(Victim))).scalar()
    total_accused = (await db.execute(select(func.count()).select_from(Accused))).scalar()
    total_arrests = (await db.execute(select(func.count()).select_from(ArrestSurrender))).scalar()
    total_chargesheets = (await db.execute(select(func.count()).select_from(ChargesheetDetails))).scalar()

    # Heinous cases (gravity_id = 1)
    heinous_cases = (await db.execute(
        select(func.count()).select_from(CaseMaster).where(CaseMaster.gravityoffenceid == 1)
    )).scalar()

    # Conviction rate (status 6 = Conviction out of total resolved cases)
    convictions = (await db.execute(
        select(func.count()).select_from(CaseMaster).where(CaseMaster.casestatusid == 6)
    )).scalar()
    resolved = (await db.execute(
        select(func.count()).select_from(CaseMaster).where(CaseMaster.casestatusid.in_([2, 6, 7]))
    )).scalar()
    conviction_rate = round((convictions / resolved * 100), 1) if resolved > 0 else 0.0

    return OverviewStats(
        total_cases=total_cases,
        total_firs=total_firs,
        total_victims=total_victims,
        total_accused=total_accused,
        total_arrests=total_arrests,
        total_chargesheets=total_chargesheets,
        heinous_cases=heinous_cases,
        conviction_rate=conviction_rate,
    )


@router.get("/crime-trends", response_model=list[CrimeTrendItem])
async def get_crime_trends(
    db: AsyncSession = Depends(get_db),
    months: int = Query(12, ge=1, le=36),
):
    """Monthly crime count trend for the last N months."""

    query = (
        select(
            func.to_char(CaseMaster.crimeregistereddate, 'YYYY-MM').label("month"),
            func.count().label("count"),
        )
        .group_by(func.to_char(CaseMaster.crimeregistereddate, 'YYYY-MM'))
        .order_by(func.to_char(CaseMaster.crimeregistereddate, 'YYYY-MM').desc())
        .limit(months)
    )

    result = await db.execute(query)
    rows = result.all()

    return [CrimeTrendItem(month=row.month, count=row.count) for row in reversed(rows)]


@router.get("/crime-by-district", response_model=list[DistrictCrimeItem])
async def get_crime_by_district(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(15, ge=1, le=30),
):
    """Crime count grouped by district, sorted descending."""

    query = (
        select(
            District.districtname.label("district"),
            func.count().label("count"),
        )
        .select_from(CaseMaster)
        .join(Unit, CaseMaster.policestationid == Unit.unitid)
        .join(District, Unit.districtid == District.districtid)
        .group_by(District.districtname)
        .order_by(func.count().desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return [DistrictCrimeItem(district=row.district, count=row.count) for row in result.all()]


@router.get("/crime-by-type", response_model=list[CrimeTypeItem])
async def get_crime_by_type(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(15, ge=1, le=50),
):
    """Crime count grouped by crime sub-head (type), with parent group."""

    query = (
        select(
            CrimeSubHead.crimeheadname.label("crime_type"),
            CrimeHead.crimegroupname.label("crime_group"),
            func.count().label("count"),
        )
        .select_from(CaseMaster)
        .join(CrimeSubHead, CaseMaster.crimeminorheadid == CrimeSubHead.crimesubheadid)
        .join(CrimeHead, CaseMaster.crimemajorheadid == CrimeHead.crimeheadid)
        .group_by(CrimeSubHead.crimeheadname, CrimeHead.crimegroupname)
        .order_by(func.count().desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return [
        CrimeTypeItem(crime_type=row.crime_type, crime_group=row.crime_group, count=row.count)
        for row in result.all()
    ]


@router.get("/status-distribution", response_model=list[StatusDistributionItem])
async def get_status_distribution(db: AsyncSession = Depends(get_db)):
    """Case count grouped by current status."""

    query = (
        select(
            CaseStatusMaster.casestatusname.label("status"),
            func.count().label("count"),
        )
        .select_from(CaseMaster)
        .join(CaseStatusMaster, CaseMaster.casestatusid == CaseStatusMaster.casestatusid)
        .group_by(CaseStatusMaster.casestatusname)
        .order_by(func.count().desc())
    )

    result = await db.execute(query)
    return [StatusDistributionItem(status=row.status, count=row.count) for row in result.all()]


@router.get("/hotspots", response_model=list[HotspotPoint])
async def get_hotspots(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(500, ge=1, le=2000),
    crime_head_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
):
    """Lat/Lon points for crime heatmap visualization."""

    query = (
        select(
            CaseMaster.latitude,
            CaseMaster.longitude,
            CrimeSubHead.crimeheadname.label("crime_type"),
        )
        .join(CrimeSubHead, CaseMaster.crimeminorheadid == CrimeSubHead.crimesubheadid, isouter=True)
        .where(CaseMaster.latitude.isnot(None))
        .where(CaseMaster.longitude.isnot(None))
    )

    if crime_head_id:
        query = query.where(CaseMaster.crimemajorheadid == crime_head_id)
    if date_from:
        query = query.where(CaseMaster.crimeregistereddate >= date_from)
    if date_to:
        query = query.where(CaseMaster.crimeregistereddate <= date_to)

    query = query.limit(limit)

    result = await db.execute(query)
    return [
        HotspotPoint(
            latitude=float(row.latitude),
            longitude=float(row.longitude),
            crime_type=row.crime_type,
        )
        for row in result.all()
    ]


@router.get("/repeat-offenders")
async def get_repeat_offenders(
    db: AsyncSession = Depends(get_db),
    min_cases: int = Query(2, ge=2),
    limit: int = Query(20, ge=1, le=100),
):
    """Identify repeat offenders — accused names appearing in multiple FIRs."""

    query = (
        select(
            Accused.accusedname,
            func.count(func.distinct(Accused.casemasterid)).label("case_count"),
            func.array_agg(func.distinct(Accused.casemasterid)).label("case_ids"),
        )
        .group_by(Accused.accusedname)
        .having(func.count(func.distinct(Accused.casemasterid)) >= min_cases)
        .order_by(func.count(func.distinct(Accused.casemasterid)).desc())
        .limit(limit)
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "accused_name": row.accusedname,
            "case_count": row.case_count,
            "case_ids": row.case_ids,
        }
        for row in rows
    ]


@router.get("/age-distribution")
async def get_age_distribution(
    db: AsyncSession = Depends(get_db),
    entity: str = Query("accused", pattern="^(accused|victim)$"),
):
    """Age distribution of accused or victims, bucketed into ranges."""

    if entity == "accused":
        age_col = Accused.ageyear
        table = Accused
    else:
        age_col = Victim.ageyear
        table = Victim

    query = (
        select(
            case(
                (age_col < 18, "Under 18"),
                (age_col.between(18, 25), "18-25"),
                (age_col.between(26, 35), "26-35"),
                (age_col.between(36, 45), "36-45"),
                (age_col.between(46, 60), "46-60"),
                else_="60+",
            ).label("age_group"),
            func.count().label("count"),
        )
        .where(age_col.isnot(None))
        .group_by("age_group")
        .order_by("age_group")
    )

    result = await db.execute(query)
    return [{"age_group": row.age_group, "count": row.count} for row in result.all()]

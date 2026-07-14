"""
KSP Crime Analytics — Pydantic Response Schemas
Defines the shape of API responses for type safety and auto-documentation.
"""

from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional


# ==================== LOOKUP SCHEMAS ====================

class DistrictOut(BaseModel):
    districtid: int
    districtname: str
    model_config = {"from_attributes": True}


class UnitOut(BaseModel):
    unitid: int
    unitname: str
    districtid: Optional[int] = None
    model_config = {"from_attributes": True}


class EmployeeOut(BaseModel):
    employeeid: int
    firstname: str
    kgid: Optional[str] = None
    model_config = {"from_attributes": True}


class CrimeCategoryOut(BaseModel):
    casecategoryid: int
    lookupvalue: str
    model_config = {"from_attributes": True}


class CrimeHeadOut(BaseModel):
    crimeheadid: int
    crimegroupname: str
    model_config = {"from_attributes": True}


class CrimeSubHeadOut(BaseModel):
    crimesubheadid: int
    crimeheadname: str
    crimeheadid: int
    model_config = {"from_attributes": True}


class CaseStatusOut(BaseModel):
    casestatusid: int
    casestatusname: str
    model_config = {"from_attributes": True}


class GravityOut(BaseModel):
    gravityoffenceid: int
    lookupvalue: str
    model_config = {"from_attributes": True}


# ==================== PEOPLE SCHEMAS ====================

class VictimOut(BaseModel):
    victimmasterid: int
    victimname: str
    ageyear: Optional[int] = None
    genderid: Optional[int] = None
    victimpolice: Optional[str] = None
    model_config = {"from_attributes": True}


class AccusedOut(BaseModel):
    accusedmasterid: int
    accusedname: str
    ageyear: Optional[int] = None
    genderid: Optional[int] = None
    personid: Optional[str] = None
    model_config = {"from_attributes": True}


class ComplainantOut(BaseModel):
    complainantid: int
    complainantname: str
    ageyear: Optional[int] = None
    genderid: Optional[int] = None
    model_config = {"from_attributes": True}


class ArrestOut(BaseModel):
    arrestsurrenderid: int
    arrestsurrenderdate: Optional[date] = None
    arrestsurrendertypeid: Optional[int] = None
    isaccused: Optional[bool] = None
    model_config = {"from_attributes": True}


class ActSectionOut(BaseModel):
    actid: str
    sectionid: str
    model_config = {"from_attributes": True}


# ==================== CASE SCHEMAS ====================

class CaseListItem(BaseModel):
    """Compact case representation for list views."""
    casemasterid: int
    crimeno: str
    caseno: Optional[str] = None
    crimeregistereddate: date
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Resolved names (populated via joins)
    district_name: Optional[str] = None
    station_name: Optional[str] = None
    crime_type: Optional[str] = None
    crime_group: Optional[str] = None
    case_status: Optional[str] = None
    gravity: Optional[str] = None
    category: Optional[str] = None

    model_config = {"from_attributes": True}


class CaseDetail(BaseModel):
    """Full case detail with all related entities."""
    casemasterid: int
    crimeno: str
    caseno: Optional[str] = None
    crimeregistereddate: date
    incidentfromdate: Optional[datetime] = None
    incidenttodate: Optional[datetime] = None
    inforeceivedpsdate: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    brieffacts: Optional[str] = None

    # Resolved names
    district_name: Optional[str] = None
    station_name: Optional[str] = None
    officer_name: Optional[str] = None
    crime_type: Optional[str] = None
    crime_group: Optional[str] = None
    case_status: Optional[str] = None
    gravity: Optional[str] = None
    category: Optional[str] = None
    court_name: Optional[str] = None

    # Related entities
    victims: list[VictimOut] = []
    accused: list[AccusedOut] = []
    complainants: list[ComplainantOut] = []
    arrests: list[ArrestOut] = []
    act_sections: list[ActSectionOut] = []

    model_config = {"from_attributes": True}


# ==================== PAGINATED RESPONSE ====================

class PaginatedCases(BaseModel):
    """Paginated list of cases."""
    total: int
    page: int
    page_size: int
    total_pages: int
    results: list[CaseListItem]


# ==================== ANALYTICS SCHEMAS ====================

class OverviewStats(BaseModel):
    total_cases: int
    total_firs: int
    total_victims: int
    total_accused: int
    total_arrests: int
    total_chargesheets: int
    heinous_cases: int
    conviction_rate: float


class CrimeTrendItem(BaseModel):
    month: str
    count: int


class DistrictCrimeItem(BaseModel):
    district: str
    count: int


class CrimeTypeItem(BaseModel):
    crime_type: str
    crime_group: str
    count: int


class StatusDistributionItem(BaseModel):
    status: str
    count: int


class HotspotPoint(BaseModel):
    latitude: float
    longitude: float
    crime_type: Optional[str] = None
    intensity: int = 1

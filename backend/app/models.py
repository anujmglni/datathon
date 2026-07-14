"""
KSP Crime Analytics — SQLAlchemy ORM Models
Maps all 22 tables from the Police FIR ER Diagram to Python classes.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime, Text,
    Numeric, ForeignKey, CHAR
)
from sqlalchemy.orm import relationship
from app.database import Base


# ==================== LOOKUP / MASTER TABLES ====================

class State(Base):
    __tablename__ = "state"

    stateid = Column("stateid", Integer, primary_key=True)
    statename = Column("statename", String(100), nullable=False)
    nationalityid = Column("nationalityid", Integer)
    active = Column("active", Boolean, default=True)

    districts = relationship("District", back_populates="state")


class District(Base):
    __tablename__ = "district"

    districtid = Column("districtid", Integer, primary_key=True)
    districtname = Column("districtname", String(100), nullable=False)
    stateid = Column("stateid", Integer, ForeignKey("state.stateid"), nullable=False)
    active = Column("active", Boolean, default=True)

    state = relationship("State", back_populates="districts")
    units = relationship("Unit", back_populates="district")
    courts = relationship("Court", back_populates="district")


class UnitType(Base):
    __tablename__ = "unittype"

    unittypeid = Column("unittypeid", Integer, primary_key=True)
    unittypename = Column("unittypename", String(100), nullable=False)
    citydiststate = Column("citydiststate", String(20))
    hierarchy = Column("hierarchy", Integer)
    active = Column("active", Boolean, default=True)


class Unit(Base):
    __tablename__ = "unit"

    unitid = Column("unitid", Integer, primary_key=True)
    unitname = Column("unitname", String(200), nullable=False)
    typeid = Column("typeid", Integer, ForeignKey("unittype.unittypeid"))
    parentunit = Column("parentunit", Integer)
    nationalityid = Column("nationalityid", Integer)
    stateid = Column("stateid", Integer, ForeignKey("state.stateid"))
    districtid = Column("districtid", Integer, ForeignKey("district.districtid"))
    active = Column("active", Boolean, default=True)

    district = relationship("District", back_populates="units")


class Rank(Base):
    __tablename__ = "rank"

    rankid = Column("rankid", Integer, primary_key=True)
    rankname = Column("rankname", String(100), nullable=False)
    hierarchy = Column("hierarchy", Integer)
    active = Column("active", Boolean, default=True)


class Designation(Base):
    __tablename__ = "designation"

    designationid = Column("designationid", Integer, primary_key=True)
    designationname = Column("designationname", String(100), nullable=False)
    active = Column("active", Boolean, default=True)
    sortorder = Column("sortorder", Integer)


class Employee(Base):
    __tablename__ = "employee"

    employeeid = Column("employeeid", Integer, primary_key=True)
    districtid = Column("districtid", Integer, ForeignKey("district.districtid"))
    unitid = Column("unitid", Integer, ForeignKey("unit.unitid"))
    rankid = Column("rankid", Integer, ForeignKey("rank.rankid"))
    designationid = Column("designationid", Integer, ForeignKey("designation.designationid"))
    kgid = Column("kgid", String(50))
    firstname = Column("firstname", String(100), nullable=False)
    employeedob = Column("employeedob", Date)
    genderid = Column("genderid", Integer)
    bloodgroupid = Column("bloodgroupid", Integer)
    physicallychallenged = Column("physicallychallenged", Boolean, default=False)
    appointmentdate = Column("appointmentdate", Date)

    rank = relationship("Rank")
    designation = relationship("Designation")
    unit = relationship("Unit")


class CaseCategory(Base):
    __tablename__ = "casecategory"

    casecategoryid = Column("casecategoryid", Integer, primary_key=True)
    lookupvalue = Column("lookupvalue", String(50), nullable=False)


class GravityOffence(Base):
    __tablename__ = "gravityoffence"

    gravityoffenceid = Column("gravityoffenceid", Integer, primary_key=True)
    lookupvalue = Column("lookupvalue", String(50), nullable=False)


class CaseStatusMaster(Base):
    __tablename__ = "casestatusmaster"

    casestatusid = Column("casestatusid", Integer, primary_key=True)
    casestatusname = Column("casestatusname", String(100), nullable=False)


class ReligionMaster(Base):
    __tablename__ = "religionmaster"

    religionid = Column("religionid", Integer, primary_key=True)
    religionname = Column("religionname", String(50), nullable=False)


class CasteMaster(Base):
    __tablename__ = "castemaster"

    caste_master_id = Column("caste_master_id", Integer, primary_key=True)
    caste_master_name = Column("caste_master_name", String(100), nullable=False)


class OccupationMaster(Base):
    __tablename__ = "occupationmaster"

    occupationid = Column("occupationid", Integer, primary_key=True)
    occupationname = Column("occupationname", String(100), nullable=False)


class Court(Base):
    __tablename__ = "court"

    courtid = Column("courtid", Integer, primary_key=True)
    courtname = Column("courtname", String(200), nullable=False)
    districtid = Column("districtid", Integer, ForeignKey("district.districtid"))
    stateid = Column("stateid", Integer, ForeignKey("state.stateid"))
    active = Column("active", Boolean, default=True)

    district = relationship("District", back_populates="courts")


# ==================== CRIME CLASSIFICATION ====================

class Act(Base):
    __tablename__ = "act"

    actcode = Column("actcode", String(20), primary_key=True)
    actdescription = Column("actdescription", String(500))
    shortname = Column("shortname", String(50))
    active = Column("active", Boolean, default=True)

    sections = relationship("Section", back_populates="act")


class Section(Base):
    __tablename__ = "section"

    sectioncode = Column("sectioncode", String(20), primary_key=True)
    actcode = Column("actcode", String(20), ForeignKey("act.actcode"), primary_key=True)
    sectiondescription = Column("sectiondescription", String(500))
    active = Column("active", Boolean, default=True)

    act = relationship("Act", back_populates="sections")


class CrimeHead(Base):
    __tablename__ = "crimehead"

    crimeheadid = Column("crimeheadid", Integer, primary_key=True)
    crimegroupname = Column("crimegroupname", String(200), nullable=False)
    active = Column("active", Boolean, default=True)

    sub_heads = relationship("CrimeSubHead", back_populates="crime_head")


class CrimeSubHead(Base):
    __tablename__ = "crimesubhead"

    crimesubheadid = Column("crimesubheadid", Integer, primary_key=True)
    crimeheadid = Column("crimeheadid", Integer, ForeignKey("crimehead.crimeheadid"), nullable=False)
    crimeheadname = Column("crimeheadname", String(200), nullable=False)
    seqid = Column("seqid", Integer)

    crime_head = relationship("CrimeHead", back_populates="sub_heads")


class CrimeHeadActSection(Base):
    __tablename__ = "crimeheadactsection"

    crimeheadid = Column("crimeheadid", Integer, ForeignKey("crimehead.crimeheadid"), primary_key=True)
    actcode = Column("actcode", String(20), ForeignKey("act.actcode"), primary_key=True)
    sectioncode = Column("sectioncode", String(20), primary_key=True)


# ==================== CORE FIR / CASE ====================

class CaseMaster(Base):
    __tablename__ = "casemaster"

    casemasterid = Column("casemasterid", Integer, primary_key=True)
    crimeno = Column("crimeno", String(30), nullable=False)
    caseno = Column("caseno", String(20))
    crimeregistereddate = Column("crimeregistereddate", Date, nullable=False)
    policepersonid = Column("policepersonid", Integer, ForeignKey("employee.employeeid"))
    policestationid = Column("policestationid", Integer, ForeignKey("unit.unitid"))
    casecategoryid = Column("casecategoryid", Integer, ForeignKey("casecategory.casecategoryid"))
    gravityoffenceid = Column("gravityoffenceid", Integer, ForeignKey("gravityoffence.gravityoffenceid"))
    crimemajorheadid = Column("crimemajorheadid", Integer, ForeignKey("crimehead.crimeheadid"))
    crimeminorheadid = Column("crimeminorheadid", Integer, ForeignKey("crimesubhead.crimesubheadid"))
    casestatusid = Column("casestatusid", Integer, ForeignKey("casestatusmaster.casestatusid"))
    courtid = Column("courtid", Integer, ForeignKey("court.courtid"))
    incidentfromdate = Column("incidentfromdate", DateTime)
    incidenttodate = Column("incidenttodate", DateTime)
    inforeceivedpsdate = Column("inforeceivedpsdate", DateTime)
    latitude = Column("latitude", Numeric(10, 7))
    longitude = Column("longitude", Numeric(10, 7))
    brieffacts = Column("brieffacts", Text)

    # Relationships
    police_person = relationship("Employee")
    police_station = relationship("Unit")
    case_category = relationship("CaseCategory")
    gravity_offence = relationship("GravityOffence")
    crime_major_head = relationship("CrimeHead")
    crime_minor_head = relationship("CrimeSubHead")
    case_status = relationship("CaseStatusMaster")
    court = relationship("Court")
    victims = relationship("Victim", back_populates="case")
    accused_list = relationship("Accused", back_populates="case")
    complainants = relationship("ComplainantDetails", back_populates="case")
    arrests = relationship("ArrestSurrender", back_populates="case")
    act_sections = relationship("ActSectionAssociation", back_populates="case")
    chargesheet = relationship("ChargesheetDetails", back_populates="case")
    occurrence = relationship("InvOccuranceTime", back_populates="case", uselist=False)


# ==================== PEOPLE LINKED TO CASES ====================

class ComplainantDetails(Base):
    __tablename__ = "complainantdetails"

    complainantid = Column("complainantid", Integer, primary_key=True)
    casemasterid = Column("casemasterid", Integer, ForeignKey("casemaster.casemasterid"), nullable=False)
    complainantname = Column("complainantname", String(200), nullable=False)
    ageyear = Column("ageyear", Integer)
    occupationid = Column("occupationid", Integer, ForeignKey("occupationmaster.occupationid"))
    religionid = Column("religionid", Integer, ForeignKey("religionmaster.religionid"))
    casteid = Column("casteid", Integer, ForeignKey("castemaster.caste_master_id"))
    genderid = Column("genderid", Integer)

    case = relationship("CaseMaster", back_populates="complainants")
    occupation = relationship("OccupationMaster")
    religion = relationship("ReligionMaster")
    caste = relationship("CasteMaster")


class Victim(Base):
    __tablename__ = "victim"

    victimmasterid = Column("victimmasterid", Integer, primary_key=True)
    casemasterid = Column("casemasterid", Integer, ForeignKey("casemaster.casemasterid"), nullable=False)
    victimname = Column("victimname", String(200), nullable=False)
    ageyear = Column("ageyear", Integer)
    genderid = Column("genderid", Integer)
    victimpolice = Column("victimpolice", String(5))

    case = relationship("CaseMaster", back_populates="victims")


class Accused(Base):
    __tablename__ = "accused"

    accusedmasterid = Column("accusedmasterid", Integer, primary_key=True)
    casemasterid = Column("casemasterid", Integer, ForeignKey("casemaster.casemasterid"), nullable=False)
    accusedname = Column("accusedname", String(200), nullable=False)
    ageyear = Column("ageyear", Integer)
    genderid = Column("genderid", Integer)
    personid = Column("personid", String(10))

    case = relationship("CaseMaster", back_populates="accused_list")


# ==================== ARREST / SURRENDER ====================

class ArrestSurrender(Base):
    __tablename__ = "arrestsurrender"

    arrestsurrenderid = Column("arrestsurrenderid", Integer, primary_key=True)
    casemasterid = Column("casemasterid", Integer, ForeignKey("casemaster.casemasterid"), nullable=False)
    arrestsurrendertypeid = Column("arrestsurrendertypeid", Integer)
    arrestsurrenderdate = Column("arrestsurrenderdate", Date)
    arrestsurrenderstateid = Column("arrestsurrenderstateid", Integer, ForeignKey("state.stateid"))
    arrestsurrenderdistrictid = Column("arrestsurrenderdistrictid", Integer, ForeignKey("district.districtid"))
    policestationid = Column("policestationid", Integer, ForeignKey("unit.unitid"))
    ioid = Column("ioid", Integer, ForeignKey("employee.employeeid"))
    courtid = Column("courtid", Integer, ForeignKey("court.courtid"))
    accusedmasterid = Column("accusedmasterid", Integer, ForeignKey("accused.accusedmasterid"))
    isaccused = Column("isaccused", Boolean)
    iscomplainantaccused = Column("iscomplainantaccused", Boolean)

    case = relationship("CaseMaster", back_populates="arrests")
    accused = relationship("Accused")
    io = relationship("Employee")


class InvArrestSurrenderAccused(Base):
    __tablename__ = "inv_arrestsurrenderaccused"

    arrestsurrenderid = Column("arrestsurrenderid", Integer, ForeignKey("arrestsurrender.arrestsurrenderid"), primary_key=True)
    accusedmasterid = Column("accusedmasterid", Integer, ForeignKey("accused.accusedmasterid"), primary_key=True)


# ==================== ACT-SECTION ASSOCIATION ====================

class ActSectionAssociation(Base):
    __tablename__ = "actsectionassociation"

    casemasterid = Column("casemasterid", Integer, ForeignKey("casemaster.casemasterid"), primary_key=True)
    actid = Column("actid", String(20), ForeignKey("act.actcode"), primary_key=True)
    sectionid = Column("sectionid", String(20), primary_key=True)
    actorderid = Column("actorderid", Integer)
    sectionorderid = Column("sectionorderid", Integer)

    case = relationship("CaseMaster", back_populates="act_sections")
    act = relationship("Act")


# ==================== OCCURRENCE DETAILS ====================

class InvOccuranceTime(Base):
    __tablename__ = "inv_occurancetime"

    casemasterid = Column("casemasterid", Integer, ForeignKey("casemaster.casemasterid"), primary_key=True)
    occurancefromdate = Column("occurancefromdate", DateTime)
    occurancetodate = Column("occurancetodate", DateTime)
    placeofoccurance = Column("placeofoccurance", Text)
    latitude = Column("latitude", Numeric(10, 7))
    longitude = Column("longitude", Numeric(10, 7))

    case = relationship("CaseMaster", back_populates="occurrence")


# ==================== CHARGESHEET ====================

class ChargesheetDetails(Base):
    __tablename__ = "chargesheetdetails"

    csid = Column("csid", Integer, primary_key=True)
    casemasterid = Column("casemasterid", Integer, ForeignKey("casemaster.casemasterid"), nullable=False)
    csdate = Column("csdate", DateTime)
    cstype = Column("cstype", CHAR(1))
    policepersonid = Column("policepersonid", Integer, ForeignKey("employee.employeeid"))

    case = relationship("CaseMaster", back_populates="chargesheet")
    officer = relationship("Employee")

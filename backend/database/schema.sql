-- ============================================================
-- Police FIR System — PostgreSQL Schema
-- Karnataka Police Department
-- Generated from: Police_FIR_ER_Diagram.pdf
-- ============================================================

-- ==================== LOOKUP / MASTER TABLES ====================

-- State
CREATE TABLE IF NOT EXISTS State (
    StateID         SERIAL PRIMARY KEY,
    StateName       VARCHAR(100) NOT NULL,
    NationalityID   INT,
    Active          BOOLEAN DEFAULT TRUE
);

-- District
CREATE TABLE IF NOT EXISTS District (
    DistrictID      SERIAL PRIMARY KEY,
    DistrictName    VARCHAR(100) NOT NULL,
    StateID         INT NOT NULL REFERENCES State(StateID),
    Active          BOOLEAN DEFAULT TRUE
);

-- UnitType
CREATE TABLE IF NOT EXISTS UnitType (
    UnitTypeID      SERIAL PRIMARY KEY,
    UnitTypeName    VARCHAR(100) NOT NULL,       -- e.g. Police Station, Circle Office
    CityDistState   VARCHAR(20),                 -- Operational level: City / District / State
    Hierarchy       INT,                         -- Hierarchy level (lower = higher authority)
    Active          BOOLEAN DEFAULT TRUE
);

-- Unit (Police Stations, Circle Offices, etc.)
CREATE TABLE IF NOT EXISTS Unit (
    UnitID          SERIAL PRIMARY KEY,
    UnitName        VARCHAR(200) NOT NULL,
    TypeID          INT REFERENCES UnitType(UnitTypeID),
    ParentUnit      INT,                         -- Self-reference for hierarchy
    NationalityID   INT,
    StateID         INT REFERENCES State(StateID),
    DistrictID      INT REFERENCES District(DistrictID),
    Active          BOOLEAN DEFAULT TRUE
);

-- Rank
CREATE TABLE IF NOT EXISTS Rank (
    RankID          SERIAL PRIMARY KEY,
    RankName        VARCHAR(100) NOT NULL,       -- e.g. Constable, Inspector, DSP
    Hierarchy       INT,                         -- Lower = higher rank
    Active          BOOLEAN DEFAULT TRUE
);

-- Designation
CREATE TABLE IF NOT EXISTS Designation (
    DesignationID   SERIAL PRIMARY KEY,
    DesignationName VARCHAR(100) NOT NULL,       -- e.g. Investigating Officer, SHO
    Active          BOOLEAN DEFAULT TRUE,
    SortOrder       INT
);

-- Employee (Police Personnel)
CREATE TABLE IF NOT EXISTS Employee (
    EmployeeID          SERIAL PRIMARY KEY,
    DistrictID          INT REFERENCES District(DistrictID),
    UnitID              INT REFERENCES Unit(UnitID),
    RankID              INT REFERENCES Rank(RankID),
    DesignationID       INT REFERENCES Designation(DesignationID),
    KGID                VARCHAR(50),             -- Karnataka Government ID
    FirstName           VARCHAR(100) NOT NULL,
    EmployeeDOB         DATE,
    GenderID            INT,
    BloodGroupID        INT,
    PhysicallyChallenged BOOLEAN DEFAULT FALSE,
    AppointmentDate     DATE
);

-- CaseCategory
CREATE TABLE IF NOT EXISTS CaseCategory (
    CaseCategoryID  SERIAL PRIMARY KEY,
    LookupValue     VARCHAR(50) NOT NULL         -- FIR, UDR, PAR, Zero FIR, etc.
);

-- GravityOffence
CREATE TABLE IF NOT EXISTS GravityOffence (
    GravityOffenceID SERIAL PRIMARY KEY,
    LookupValue      VARCHAR(50) NOT NULL        -- Heinous, Non-Heinous, etc.
);

-- CaseStatusMaster
CREATE TABLE IF NOT EXISTS CaseStatusMaster (
    CaseStatusID    SERIAL PRIMARY KEY,
    CaseStatusName  VARCHAR(100) NOT NULL        -- Under Investigation, Charge Sheeted, Closed
);

-- ReligionMaster
CREATE TABLE IF NOT EXISTS ReligionMaster (
    ReligionID      SERIAL PRIMARY KEY,
    ReligionName    VARCHAR(50) NOT NULL         -- Hindu, Muslim, Christian, etc.
);

-- CasteMaster
CREATE TABLE IF NOT EXISTS CasteMaster (
    caste_master_id SERIAL PRIMARY KEY,
    caste_master_name VARCHAR(100) NOT NULL
);

-- OccupationMaster
CREATE TABLE IF NOT EXISTS OccupationMaster (
    OccupationID    SERIAL PRIMARY KEY,
    OccupationName  VARCHAR(100) NOT NULL        -- Farmer, Government Employee, etc.
);

-- Court
CREATE TABLE IF NOT EXISTS Court (
    CourtID         SERIAL PRIMARY KEY,
    CourtName       VARCHAR(200) NOT NULL,
    DistrictID      INT REFERENCES District(DistrictID),
    StateID         INT REFERENCES State(StateID),
    Active          BOOLEAN DEFAULT TRUE
);

-- ==================== CRIME CLASSIFICATION TABLES ====================

-- Act (Legal Acts — IPC, NDPS, etc.)
CREATE TABLE IF NOT EXISTS Act (
    ActCode         VARCHAR(20) PRIMARY KEY,
    ActDescription  VARCHAR(500),
    ShortName       VARCHAR(50),
    Active          BOOLEAN DEFAULT TRUE
);

-- Section (Sections within an Act)
CREATE TABLE IF NOT EXISTS Section (
    SectionCode     VARCHAR(20) NOT NULL,
    ActCode         VARCHAR(20) NOT NULL REFERENCES Act(ActCode),
    SectionDescription VARCHAR(500),
    Active          BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (SectionCode, ActCode)
);

-- CrimeHead (Major Crime Categories)
CREATE TABLE IF NOT EXISTS CrimeHead (
    CrimeHeadID     SERIAL PRIMARY KEY,
    CrimeGroupName  VARCHAR(200) NOT NULL,       -- e.g. Crimes Against Body
    Active          BOOLEAN DEFAULT TRUE
);

-- CrimeSubHead (Sub-categories under CrimeHead)
CREATE TABLE IF NOT EXISTS CrimeSubHead (
    CrimeSubHeadID  SERIAL PRIMARY KEY,
    CrimeHeadID     INT NOT NULL REFERENCES CrimeHead(CrimeHeadID),
    CrimeHeadName   VARCHAR(200) NOT NULL,       -- e.g. Murder, Robbery
    SeqID           INT
);

-- CrimeHeadActSection (Maps CrimeHead to Act+Section combinations)
CREATE TABLE IF NOT EXISTS CrimeHeadActSection (
    CrimeHeadID     INT NOT NULL REFERENCES CrimeHead(CrimeHeadID),
    ActCode         VARCHAR(20) NOT NULL REFERENCES Act(ActCode),
    SectionCode     VARCHAR(20) NOT NULL,
    PRIMARY KEY (CrimeHeadID, ActCode, SectionCode)
);

-- ==================== CORE FIR / CASE TABLE ====================

-- CaseMaster (The central FIR table)
CREATE TABLE IF NOT EXISTS CaseMaster (
    CaseMasterID        SERIAL PRIMARY KEY,
    CrimeNo             VARCHAR(30) NOT NULL,    -- Structured crime number
    CaseNo              VARCHAR(20),             -- YYYY + 5-digit serial
    CrimeRegisteredDate DATE NOT NULL,
    PolicePersonID      INT REFERENCES Employee(EmployeeID),
    PoliceStationID     INT REFERENCES Unit(UnitID),
    CaseCategoryID      INT REFERENCES CaseCategory(CaseCategoryID),
    GravityOffenceID    INT REFERENCES GravityOffence(GravityOffenceID),
    CrimeMajorHeadID    INT REFERENCES CrimeHead(CrimeHeadID),
    CrimeMinorHeadID    INT REFERENCES CrimeSubHead(CrimeSubHeadID),
    CaseStatusID        INT REFERENCES CaseStatusMaster(CaseStatusID),
    CourtID             INT REFERENCES Court(CourtID),
    IncidentFromDate    TIMESTAMP,
    IncidentToDate      TIMESTAMP,
    InfoReceivedPSDate  TIMESTAMP,
    latitude            DECIMAL(10, 7),
    longitude           DECIMAL(10, 7),
    BriefFacts          TEXT                     -- Case summary (used for RAG)
);

-- ==================== PEOPLE LINKED TO CASES ====================

-- ComplainantDetails
CREATE TABLE IF NOT EXISTS ComplainantDetails (
    ComplainantID   SERIAL PRIMARY KEY,
    CaseMasterID    INT NOT NULL REFERENCES CaseMaster(CaseMasterID),
    ComplainantName VARCHAR(200) NOT NULL,
    AgeYear         INT,
    OccupationID    INT REFERENCES OccupationMaster(OccupationID),
    ReligionID      INT REFERENCES ReligionMaster(ReligionID),
    CasteID         INT REFERENCES CasteMaster(caste_master_id),
    GenderID        INT
);

-- Victim
CREATE TABLE IF NOT EXISTS Victim (
    VictimMasterID  SERIAL PRIMARY KEY,
    CaseMasterID    INT NOT NULL REFERENCES CaseMaster(CaseMasterID),
    VictimName      VARCHAR(200) NOT NULL,
    AgeYear         INT,
    GenderID        INT,                         -- M, F, T
    VictimPolice    VARCHAR(5)                   -- 1 = Police, 0 = Civilian
);

-- Accused
CREATE TABLE IF NOT EXISTS Accused (
    AccusedMasterID SERIAL PRIMARY KEY,
    CaseMasterID    INT NOT NULL REFERENCES CaseMaster(CaseMasterID),
    AccusedName     VARCHAR(200) NOT NULL,
    AgeYear         INT,
    GenderID        INT,                         -- M/F/T
    PersonID        VARCHAR(10)                  -- Sorting label: A1, A2, A3...
);

-- ==================== ARREST / SURRENDER ====================

-- ArrestSurrender
CREATE TABLE IF NOT EXISTS ArrestSurrender (
    ArrestSurrenderID       SERIAL PRIMARY KEY,
    CaseMasterID            INT NOT NULL REFERENCES CaseMaster(CaseMasterID),
    ArrestSurrenderTypeID   INT,                 -- Arrest or Voluntary Surrender
    ArrestSurrenderDate     DATE,
    ArrestSurrenderStateId  INT REFERENCES State(StateID),
    ArrestSurrenderDistrictId INT REFERENCES District(DistrictID),
    PoliceStationID         INT REFERENCES Unit(UnitID),
    IOID                    INT REFERENCES Employee(EmployeeID),   -- Investigating Officer
    CourtID                 INT REFERENCES Court(CourtID),
    AccusedMasterID         INT REFERENCES Accused(AccusedMasterID),
    IsAccused               BOOLEAN,             -- Is the primary accused?
    IsComplainantAccused    BOOLEAN              -- Is the complainant also accused?
);

-- inv_arrestsurrenderaccused (Junction table for many-to-many)
CREATE TABLE IF NOT EXISTS inv_arrestsurrenderaccused (
    ArrestSurrenderID   INT NOT NULL REFERENCES ArrestSurrender(ArrestSurrenderID),
    AccusedMasterID     INT NOT NULL REFERENCES Accused(AccusedMasterID),
    PRIMARY KEY (ArrestSurrenderID, AccusedMasterID)
);

-- ==================== ACT-SECTION ASSOCIATION ====================

-- ActSectionAssociation (Links FIRs to specific Act + Section charges)
CREATE TABLE IF NOT EXISTS ActSectionAssociation (
    CaseMasterID    INT NOT NULL REFERENCES CaseMaster(CaseMasterID),
    ActID           VARCHAR(20) NOT NULL REFERENCES Act(ActCode),
    SectionID       VARCHAR(20) NOT NULL,
    ActOrderID      INT,
    SectionOrderID  INT,
    PRIMARY KEY (CaseMasterID, ActID, SectionID)
);

-- ==================== OCCURRENCE DETAILS ====================

-- Inv_OccuranceTime (One-to-one with CaseMaster)
CREATE TABLE IF NOT EXISTS Inv_OccuranceTime (
    CaseMasterID    INT PRIMARY KEY REFERENCES CaseMaster(CaseMasterID),
    OccuranceFromDate TIMESTAMP,
    OccuranceToDate   TIMESTAMP,
    PlaceOfOccurance  TEXT,
    latitude          DECIMAL(10, 7),
    longitude         DECIMAL(10, 7)
);

-- ==================== CHARGESHEET ====================

-- ChargesheetDetails
CREATE TABLE IF NOT EXISTS ChargesheetDetails (
    CSID            SERIAL PRIMARY KEY,
    CaseMasterID    INT NOT NULL REFERENCES CaseMaster(CaseMasterID),
    csdate          TIMESTAMP,
    cstype          CHAR(1),                     -- A=Chargesheet, B=False Case, C=Undetected
    PolicePersonID  INT REFERENCES Employee(EmployeeID)
);

-- ==================== INDEXES FOR PERFORMANCE ====================

CREATE INDEX idx_casemaster_crime_date ON CaseMaster(CrimeRegisteredDate);
CREATE INDEX idx_casemaster_station ON CaseMaster(PoliceStationID);
CREATE INDEX idx_casemaster_status ON CaseMaster(CaseStatusID);
CREATE INDEX idx_casemaster_major_head ON CaseMaster(CrimeMajorHeadID);
CREATE INDEX idx_casemaster_latlon ON CaseMaster(latitude, longitude);
CREATE INDEX idx_accused_case ON Accused(CaseMasterID);
CREATE INDEX idx_victim_case ON Victim(CaseMasterID);
CREATE INDEX idx_complainant_case ON ComplainantDetails(CaseMasterID);
CREATE INDEX idx_arrest_case ON ArrestSurrender(CaseMasterID);
CREATE INDEX idx_actsection_case ON ActSectionAssociation(CaseMasterID);

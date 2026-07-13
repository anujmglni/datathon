"""
Synthetic Data Generator for KSP Crime Database
================================================
Generates realistic fake data for all tables in the Police FIR System.
Uses the Faker library with Indian locale for realistic names and addresses.

Usage:
    pip install faker psycopg2-binary
    python seed_data.py
"""

import random
import string
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('en_IN')  # Indian locale for realistic names
Faker.seed(42)
random.seed(42)

# ============================================================
# CONFIG
# ============================================================
NUM_CASES = 500          # Number of FIR cases to generate
NUM_EMPLOYEES = 80       # Police personnel
OUTPUT_FILE = "seed_data.sql"

# ============================================================
# KARNATAKA-SPECIFIC REFERENCE DATA
# ============================================================

KARNATAKA_DISTRICTS = [
    "Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Mangaluru (DK)",
    "Hubballi-Dharwad", "Belagavi", "Kalaburagi", "Ballari",
    "Tumakuru", "Shivamogga", "Raichur", "Vijayapura", "Davanagere",
    "Hassan", "Chitradurga", "Mandya", "Kodagu", "Udupi",
    "Gadag", "Haveri", "Koppal", "Bagalkot", "Ramanagara",
    "Chikkaballapura", "Chikkamagaluru", "Yadgir", "Chamarajanagara",
    "Dharwad", "Uttara Kannada", "Bidar"
]

# Lat/Lon bounding box for Karnataka
KA_LAT_MIN, KA_LAT_MAX = 11.5, 18.5
KA_LON_MIN, KA_LON_MAX = 74.0, 78.5

# Hotspot clusters (Bengaluru, Mysuru, Hubballi) for realistic crime hotspots
HOTSPOT_CENTERS = [
    (12.9716, 77.5946),   # Bengaluru
    (12.2958, 76.6394),   # Mysuru
    (15.3647, 75.1240),   # Hubballi
    (15.8497, 74.4977),   # Belagavi
    (12.8685, 74.8425),   # Mangaluru
]

POLICE_STATION_NAMES = [
    "Cubbon Park PS", "Koramangala PS", "Whitefield PS", "HSR Layout PS",
    "Jayanagar PS", "Vijayanagar PS", "Yelahanka PS", "KR Puram PS",
    "Peenya PS", "Marathahalli PS", "Indiranagar PS", "Basavanagudi PS",
    "Rajajinagar PS", "Majestic PS", "Kengeri PS", "Banashankari PS",
    "Electronic City PS", "Hebbal PS", "Yeshwanthpur PS", "JP Nagar PS",
    "Mysuru North PS", "Mysuru South PS", "Mysuru Rural PS",
    "Hubballi PS", "Dharwad PS", "Belagavi City PS", "Mangaluru North PS",
    "Mangaluru South PS", "Kalaburagi PS", "Ballari PS",
]

RANKS = ["Constable", "Head Constable", "ASI", "PSI", "PI", "DySP", "SP", "DIG", "IGP", "ADGP", "DGP"]
DESIGNATIONS = ["Beat Constable", "Writer", "Investigating Officer", "SHO", "Station Writer", "Circle Inspector"]

RELIGIONS = ["Hindu", "Muslim", "Christian", "Jain", "Buddhist", "Sikh", "Other"]
CASTES = ["General", "OBC", "SC", "ST", "Other"]
OCCUPATIONS = [
    "Farmer", "Government Employee", "Private Employee", "Business",
    "Student", "Unemployed", "Daily Wage Worker", "Auto/Cab Driver",
    "Shopkeeper", "Teacher", "Homemaker", "Retired", "IT Professional",
    "Lawyer", "Doctor", "Construction Worker"
]

CASE_CATEGORIES = [
    ("FIR", 1), ("NCR", 2), ("UDR", 3), ("PAR", 4),
    ("Zero FIR", 8)
]

GRAVITY_LEVELS = ["Heinous", "Non-Heinous", "Economic Offence", "Cyber Crime"]
CASE_STATUSES = [
    "Under Investigation", "Charge Sheeted", "Closed (Undetected)",
    "Closed (Mistake of Fact)", "Referred", "Conviction", "Acquittal"
]

CRIME_HEADS = [
    ("Crimes Against Body", [
        "Murder", "Attempt to Murder", "Culpable Homicide", "Grievous Hurt",
        "Simple Hurt", "Assault", "Dowry Death", "Kidnapping"
    ]),
    ("Crimes Against Property", [
        "Robbery", "Dacoity", "Burglary", "Theft", "Snatching",
        "Motor Vehicle Theft", "House Breaking", "Cheating"
    ]),
    ("Crimes Against Women", [
        "Rape", "Dowry Harassment", "Molestation", "Eve Teasing",
        "Domestic Violence", "Cruelty by Husband"
    ]),
    ("Crimes Against Children", [
        "POCSO", "Child Labour", "Missing Child", "Child Trafficking"
    ]),
    ("Economic Offences", [
        "Forgery", "Counterfeiting", "Criminal Breach of Trust",
        "Fraud", "Money Laundering"
    ]),
    ("Cyber Crimes", [
        "Online Fraud", "Identity Theft", "Hacking", "Cyber Stalking",
        "Social Media Crime", "UPI/Banking Fraud"
    ]),
    ("Narcotic Crimes", [
        "NDPS Possession", "NDPS Trafficking", "Ganja Cultivation"
    ]),
    ("Public Order", [
        "Rioting", "Unlawful Assembly", "Affray", "Criminal Intimidation"
    ]),
]

ACTS = [
    ("IPC", "Indian Penal Code, 1860", "IPC"),
    ("BNS", "Bharatiya Nyaya Sanhita, 2023", "BNS"),
    ("CrPC", "Code of Criminal Procedure, 1973", "CrPC"),
    ("NDPS", "Narcotic Drugs and Psychotropic Substances Act, 1985", "NDPS"),
    ("POCSO", "Protection of Children from Sexual Offences Act, 2012", "POCSO"),
    ("ITA", "Information Technology Act, 2000", "IT Act"),
    ("ArmA", "Arms Act, 1959", "Arms Act"),
    ("DPA", "Dowry Prohibition Act, 1961", "DP Act"),
    ("SCA", "SC/ST (Prevention of Atrocities) Act, 1989", "SC/ST Act"),
    ("MVA", "Motor Vehicles Act, 1988", "MV Act"),
    ("KPA", "Karnataka Police Act, 1963", "KP Act"),
]

IPC_SECTIONS = {
    "IPC": [
        ("302", "Punishment for Murder"),
        ("307", "Attempt to Murder"),
        ("304", "Culpable Homicide not amounting to Murder"),
        ("323", "Punishment for voluntarily causing hurt"),
        ("324", "Voluntarily causing hurt by dangerous weapons"),
        ("354", "Assault or criminal force to woman"),
        ("376", "Punishment for rape"),
        ("379", "Punishment for theft"),
        ("392", "Punishment for robbery"),
        ("395", "Punishment for dacoity"),
        ("397", "Robbery or dacoity with attempt to cause death"),
        ("406", "Criminal breach of trust"),
        ("420", "Cheating and dishonestly inducing delivery of property"),
        ("498A", "Husband or relative subjecting woman to cruelty"),
        ("506", "Criminal intimidation"),
        ("509", "Word, gesture or act intended to insult modesty of a woman"),
        ("34", "Acts done by several persons in furtherance of common intention"),
        ("120B", "Criminal conspiracy"),
        ("147", "Punishment for rioting"),
        ("148", "Rioting, armed with deadly weapon"),
        ("149", "Every member of unlawful assembly guilty of offence"),
        ("341", "Punishment for wrongful restraint"),
        ("363", "Punishment for kidnapping"),
        ("365", "Kidnapping with intent secretly and wrongfully to confine"),
        ("427", "Mischief causing damage"),
        ("452", "House-trespass after preparation for hurt"),
        ("457", "Lurking house-trespass by night"),
        ("504", "Intentional insult with intent to provoke breach of peace"),
        ("511", "Punishment for attempting to commit offences"),
    ],
    "NDPS": [
        ("20", "Punishment for contravention in relation to cannabis"),
        ("22", "Punishment for contravention in relation to psychotropic substances"),
        ("27", "Punishment for consumption of narcotic drug"),
    ],
    "POCSO": [
        ("4", "Punishment for penetrative sexual assault"),
        ("6", "Punishment for aggravated penetrative sexual assault"),
        ("8", "Punishment for sexual assault"),
    ],
    "ITA": [
        ("66", "Computer related offences"),
        ("66C", "Punishment for identity theft"),
        ("66D", "Punishment for cheating by personation"),
        ("67", "Punishment for publishing obscene material"),
    ],
}

# Brief facts templates for realistic FIR summaries
BRIEF_FACTS_TEMPLATES = [
    "On {date}, the complainant {complainant} reported that unknown persons broke into their residence at {location} and stole cash amounting to Rs. {amount} and gold ornaments. The accused {accused} was later identified through CCTV footage from a nearby shop.",
    "The victim {victim}, aged {age}, was assaulted by the accused {accused} near {location} on {date} at approximately {time}. The accused used a sharp weapon causing grievous injuries. The victim was rushed to {hospital} for treatment.",
    "A case of cheating was reported by {complainant} stating that the accused {accused} fraudulently obtained Rs. {amount} by promising a job in a government department. The accused collected money over a period of {months} months and disappeared.",
    "On {date}, the complainant {complainant} reported that their {vehicle_type} bearing registration number {reg_no} was stolen from {location}. The vehicle was parked outside {place} and was found missing when the complainant returned.",
    "The complainant {complainant} reported domestic violence by husband {accused} and in-laws. The accused demanded additional dowry of Rs. {amount} and subjected the complainant to physical and mental harassment since {duration}.",
    "On {date}, at about {time}, the accused {accused} along with {num_associates} associates formed an unlawful assembly near {location} and attacked the complainant {complainant} with lethal weapons resulting in injuries.",
    "A cyber fraud was reported by {complainant}. The accused posed as a bank official and obtained OTP and banking credentials through a phone call on {date}. An amount of Rs. {amount} was fraudulently transferred from the complainant's account.",
    "The deceased {victim}, aged {age}, was found dead under suspicious circumstances at {location} on {date}. The investigation revealed that the accused {accused}, who is a relative of the deceased, had a dispute over property worth Rs. {amount}.",
    "On {date}, the Anti-Narcotics squad conducted a raid at {location} and seized {quantity} grams of {substance} from the possession of the accused {accused}. The accused was found to be part of a supply chain operating across {districts}.",
    "The complainant {complainant}, a shopkeeper at {location}, reported that the accused {accused} along with others robbed the shop at knife-point on {date} and fled with cash Rs. {amount} and valuables.",
]

HOSPITALS = [
    "Victoria Hospital", "Bowring Hospital", "KC General Hospital",
    "Jayadeva Hospital", "St. John's Hospital", "Manipal Hospital",
    "BGS Global Hospital", "Sapthagiri Hospital", "District Hospital"
]

VEHICLES = ["two-wheeler", "car", "auto-rickshaw", "lorry", "SUV", "bus"]
SUBSTANCES = ["ganja", "heroin", "cocaine", "MDMA", "methamphetamine", "hashish"]


def generate_lat_lon():
    """Generate realistic lat/lon within Karnataka, with clustering around hotspots."""
    if random.random() < 0.6:
        center = random.choice(HOTSPOT_CENTERS)
        lat = center[0] + random.gauss(0, 0.05)
        lon = center[1] + random.gauss(0, 0.05)
    else:
        lat = random.uniform(KA_LAT_MIN, KA_LAT_MAX)
        lon = random.uniform(KA_LON_MIN, KA_LON_MAX)
    return round(lat, 7), round(lon, 7)


def generate_crime_no(cat_code, district_id, unit_id, year, serial):
    """Generate structured CrimeNo as per schema format."""
    return f"{cat_code}{district_id:04d}{unit_id:04d}{year}{serial:05d}"


def generate_brief_facts(complainant, accused, victim, date_str, location):
    """Generate a realistic FIR brief facts narrative."""
    template = random.choice(BRIEF_FACTS_TEMPLATES)
    return template.format(
        date=date_str,
        complainant=complainant,
        accused=accused,
        victim=victim or complainant,
        age=random.randint(18, 65),
        location=location,
        time=f"{random.randint(1,12)}:{random.choice(['00','15','30','45'])} {'AM' if random.random()>0.5 else 'PM'}",
        amount=random.choice([5000, 10000, 25000, 50000, 100000, 250000, 500000, 1000000, 2500000]),
        hospital=random.choice(HOSPITALS),
        months=random.randint(2, 18),
        vehicle_type=random.choice(VEHICLES),
        reg_no=f"KA-{random.randint(1,56):02d}-{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}-{random.randint(1000,9999)}",
        place=random.choice(["a shopping mall", "a residential apartment", "a commercial complex", "the office", "the bus stand"]),
        duration=f"{random.randint(1,5)} years",
        num_associates=random.randint(2, 6),
        quantity=random.choice([50, 100, 250, 500, 1000, 2500, 5000]),
        substance=random.choice(SUBSTANCES),
        districts=f"{random.choice(KARNATAKA_DISTRICTS)} and {random.choice(KARNATAKA_DISTRICTS)}",
    )


def escape_sql(s):
    """Escape single quotes for SQL insertion."""
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def main():
    lines = []
    lines.append("-- ============================================================")
    lines.append("-- SYNTHETIC SEED DATA for KSP Crime Database")
    lines.append("-- Auto-generated — DO NOT EDIT MANUALLY")
    lines.append("-- ============================================================\n")
    lines.append("BEGIN;\n")

    # ====================== 1. States ======================
    lines.append("-- States")
    states = ["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh", "Telangana",
              "Maharashtra", "Goa", "Puducherry"]
    for i, s in enumerate(states, 1):
        lines.append(f"INSERT INTO State (StateID, StateName, NationalityID, Active) VALUES ({i}, {escape_sql(s)}, 1, TRUE);")
    KA_STATE_ID = 1
    lines.append("")

    # ====================== 2. Districts ======================
    lines.append("-- Districts")
    for i, d in enumerate(KARNATAKA_DISTRICTS, 1):
        lines.append(f"INSERT INTO District (DistrictID, DistrictName, StateID, Active) VALUES ({i}, {escape_sql(d)}, {KA_STATE_ID}, TRUE);")
    lines.append("")

    # ====================== 3. UnitTypes ======================
    lines.append("-- Unit Types")
    unit_types = [
        (1, "Police Station", "City", 5),
        (2, "Circle Office", "City", 4),
        (3, "Sub-Division", "District", 3),
        (4, "District HQ", "District", 2),
        (5, "Commissionerate", "City", 1),
    ]
    for ut in unit_types:
        lines.append(f"INSERT INTO UnitType (UnitTypeID, UnitTypeName, CityDistState, Hierarchy, Active) VALUES ({ut[0]}, {escape_sql(ut[1])}, {escape_sql(ut[2])}, {ut[3]}, TRUE);")
    lines.append("")

    # ====================== 4. Units (Police Stations) ======================
    lines.append("-- Units (Police Stations)")
    for i, ps in enumerate(POLICE_STATION_NAMES, 1):
        dist_id = (i % len(KARNATAKA_DISTRICTS)) + 1
        lines.append(f"INSERT INTO Unit (UnitID, UnitName, TypeID, ParentUnit, NationalityID, StateID, DistrictID, Active) VALUES ({i}, {escape_sql(ps)}, 1, NULL, 1, {KA_STATE_ID}, {dist_id}, TRUE);")
    lines.append("")

    # ====================== 5. Ranks ======================
    lines.append("-- Ranks")
    for i, r in enumerate(RANKS, 1):
        lines.append(f"INSERT INTO Rank (RankID, RankName, Hierarchy, Active) VALUES ({i}, {escape_sql(r)}, {i}, TRUE);")
    lines.append("")

    # ====================== 6. Designations ======================
    lines.append("-- Designations")
    for i, d in enumerate(DESIGNATIONS, 1):
        lines.append(f"INSERT INTO Designation (DesignationID, DesignationName, Active, SortOrder) VALUES ({i}, {escape_sql(d)}, TRUE, {i});")
    lines.append("")

    # ====================== 7. Employees ======================
    lines.append("-- Employees (Police Personnel)")
    employees = []
    for i in range(1, NUM_EMPLOYEES + 1):
        fname = fake.first_name()
        dist_id = random.randint(1, len(KARNATAKA_DISTRICTS))
        unit_id = random.randint(1, len(POLICE_STATION_NAMES))
        rank_id = random.randint(1, len(RANKS))
        desig_id = random.randint(1, len(DESIGNATIONS))
        kgid = f"KG{random.randint(100000, 999999)}"
        dob = fake.date_of_birth(minimum_age=25, maximum_age=58).isoformat()
        gender = random.choice([1, 2])   # 1=M, 2=F
        blood = random.randint(1, 8)
        appt_date = fake.date_between(start_date='-30y', end_date='-2y').isoformat()
        employees.append(fname)
        lines.append(
            f"INSERT INTO Employee (EmployeeID, DistrictID, UnitID, RankID, DesignationID, KGID, FirstName, EmployeeDOB, GenderID, BloodGroupID, PhysicallyChallenged, AppointmentDate) "
            f"VALUES ({i}, {dist_id}, {unit_id}, {rank_id}, {desig_id}, {escape_sql(kgid)}, {escape_sql(fname)}, '{dob}', {gender}, {blood}, FALSE, '{appt_date}');"
        )
    lines.append("")

    # ====================== 8. Case Categories ======================
    lines.append("-- Case Categories")
    for name, code in CASE_CATEGORIES:
        lines.append(f"INSERT INTO CaseCategory (CaseCategoryID, LookupValue) VALUES ({code}, {escape_sql(name)});")
    lines.append("")

    # ====================== 9. Gravity Offence ======================
    lines.append("-- Gravity Offence")
    for i, g in enumerate(GRAVITY_LEVELS, 1):
        lines.append(f"INSERT INTO GravityOffence (GravityOffenceID, LookupValue) VALUES ({i}, {escape_sql(g)});")
    lines.append("")

    # ====================== 10. Case Statuses ======================
    lines.append("-- Case Status Master")
    for i, cs in enumerate(CASE_STATUSES, 1):
        lines.append(f"INSERT INTO CaseStatusMaster (CaseStatusID, CaseStatusName) VALUES ({i}, {escape_sql(cs)});")
    lines.append("")

    # ====================== 11. Religion, Caste, Occupation ======================
    lines.append("-- Religion Master")
    for i, r in enumerate(RELIGIONS, 1):
        lines.append(f"INSERT INTO ReligionMaster (ReligionID, ReligionName) VALUES ({i}, {escape_sql(r)});")
    lines.append("")

    lines.append("-- Caste Master")
    for i, c in enumerate(CASTES, 1):
        lines.append(f"INSERT INTO CasteMaster (caste_master_id, caste_master_name) VALUES ({i}, {escape_sql(c)});")
    lines.append("")

    lines.append("-- Occupation Master")
    for i, o in enumerate(OCCUPATIONS, 1):
        lines.append(f"INSERT INTO OccupationMaster (OccupationID, OccupationName) VALUES ({i}, {escape_sql(o)});")
    lines.append("")

    # ====================== 12. Courts ======================
    lines.append("-- Courts")
    court_types = ["JMFC", "Civil Judge", "Sessions Court", "High Court", "Fast Track Court"]
    court_id = 1
    for dist_id in range(1, min(16, len(KARNATAKA_DISTRICTS) + 1)):
        for ct in random.sample(court_types, k=random.randint(2, 4)):
            lines.append(
                f"INSERT INTO Court (CourtID, CourtName, DistrictID, StateID, Active) "
                f"VALUES ({court_id}, {escape_sql(f'{ct}, {KARNATAKA_DISTRICTS[dist_id-1]}')}, {dist_id}, {KA_STATE_ID}, TRUE);"
            )
            court_id += 1
    total_courts = court_id - 1
    lines.append("")

    # ====================== 13. Acts ======================
    lines.append("-- Acts")
    for code, desc, short in ACTS:
        lines.append(f"INSERT INTO Act (ActCode, ActDescription, ShortName, Active) VALUES ({escape_sql(code)}, {escape_sql(desc)}, {escape_sql(short)}, TRUE);")
    lines.append("")

    # ====================== 14. Sections ======================
    lines.append("-- Sections")
    for act_code, sections in IPC_SECTIONS.items():
        for sec_code, sec_desc in sections:
            lines.append(
                f"INSERT INTO Section (SectionCode, ActCode, SectionDescription, Active) "
                f"VALUES ({escape_sql(sec_code)}, {escape_sql(act_code)}, {escape_sql(sec_desc)}, TRUE);"
            )
    lines.append("")

    # ====================== 15. Crime Heads & Sub-Heads ======================
    lines.append("-- Crime Heads")
    crime_head_id = 1
    crime_sub_head_id = 1
    crime_head_map = {}       # crime_head_id -> name
    crime_sub_head_map = {}   # crime_sub_head_id -> (crime_head_id, name)

    for group_name, sub_heads in CRIME_HEADS:
        lines.append(f"INSERT INTO CrimeHead (CrimeHeadID, CrimeGroupName, Active) VALUES ({crime_head_id}, {escape_sql(group_name)}, TRUE);")
        crime_head_map[crime_head_id] = group_name
        for seq, sh in enumerate(sub_heads, 1):
            lines.append(
                f"INSERT INTO CrimeSubHead (CrimeSubHeadID, CrimeHeadID, CrimeHeadName, SeqID) "
                f"VALUES ({crime_sub_head_id}, {crime_head_id}, {escape_sql(sh)}, {seq});"
            )
            crime_sub_head_map[crime_sub_head_id] = (crime_head_id, sh)
            crime_sub_head_id += 1
        crime_head_id += 1
    total_crime_heads = crime_head_id - 1
    total_sub_heads = crime_sub_head_id - 1
    lines.append("")

    # ====================== 16. CaseMaster (FIRs) ======================
    lines.append("-- ============================================================")
    lines.append("-- CASE MASTER (FIRs) — Core Records")
    lines.append("-- ============================================================\n")

    # Build a pool of ~30 repeat offender names for network analysis realism
    repeat_offender_pool = [fake.name() for _ in range(30)]

    case_serials = {}   # (station, cat, year) -> serial counter
    accused_id = 1
    victim_id = 1
    complainant_id = 1
    arrest_id = 1
    cs_id = 1

    for case_id in range(1, NUM_CASES + 1):
        # Random date in the last 3 years
        crime_date = fake.date_between(start_date='-3y', end_date='today')
        year = crime_date.year

        cat_idx = random.randint(0, len(CASE_CATEGORIES) - 1)
        cat_name, cat_code = CASE_CATEGORIES[cat_idx]

        station_id = random.randint(1, len(POLICE_STATION_NAMES))
        dist_id = (station_id % len(KARNATAKA_DISTRICTS)) + 1

        # Serial number per station/category/year
        key = (station_id, cat_code, year)
        case_serials[key] = case_serials.get(key, 0) + 1
        serial = case_serials[key]

        crime_no = generate_crime_no(cat_code, dist_id, station_id, year, serial)
        case_no = f"{year}{serial:05d}"

        officer_id = random.randint(1, NUM_EMPLOYEES)
        gravity_id = random.randint(1, len(GRAVITY_LEVELS))
        sub_head_id = random.randint(1, total_sub_heads)
        major_head_id = crime_sub_head_map[sub_head_id][0]
        status_id = random.choices(range(1, len(CASE_STATUSES)+1), weights=[40, 25, 15, 5, 5, 5, 5])[0]
        court_id = random.randint(1, total_courts)

        lat, lon = generate_lat_lon()

        incident_from = datetime.combine(crime_date, datetime.min.time()) + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
        incident_to = incident_from + timedelta(hours=random.randint(0, 4))
        info_received = incident_to + timedelta(hours=random.randint(0, 12))

        # Generate people for this case
        complainant_name = fake.name()
        victim_name = fake.name() if random.random() > 0.3 else complainant_name

        # 20% chance accused is from repeat offender pool (for network analysis)
        if random.random() < 0.2:
            accused_name = random.choice(repeat_offender_pool)
        else:
            accused_name = fake.name()

        location = f"{fake.street_name()}, {KARNATAKA_DISTRICTS[dist_id-1]}"
        brief_facts = generate_brief_facts(complainant_name, accused_name, victim_name, crime_date.isoformat(), location)

        lines.append(
            f"INSERT INTO CaseMaster (CaseMasterID, CrimeNo, CaseNo, CrimeRegisteredDate, PolicePersonID, PoliceStationID, "
            f"CaseCategoryID, GravityOffenceID, CrimeMajorHeadID, CrimeMinorHeadID, CaseStatusID, CourtID, "
            f"IncidentFromDate, IncidentToDate, InfoReceivedPSDate, latitude, longitude, BriefFacts) "
            f"VALUES ({case_id}, {escape_sql(crime_no)}, {escape_sql(case_no)}, '{crime_date.isoformat()}', {officer_id}, {station_id}, "
            f"{cat_code}, {gravity_id}, {major_head_id}, {sub_head_id}, {status_id}, {court_id}, "
            f"'{incident_from.isoformat()}', '{incident_to.isoformat()}', '{info_received.isoformat()}', "
            f"{lat}, {lon}, {escape_sql(brief_facts)});"
        )

        # -- Complainant --
        lines.append(
            f"INSERT INTO ComplainantDetails (ComplainantID, CaseMasterID, ComplainantName, AgeYear, OccupationID, ReligionID, CasteID, GenderID) "
            f"VALUES ({complainant_id}, {case_id}, {escape_sql(complainant_name)}, {random.randint(20,65)}, "
            f"{random.randint(1,len(OCCUPATIONS))}, {random.randint(1,len(RELIGIONS))}, {random.randint(1,len(CASTES))}, {random.choice([1,2])});"
        )
        complainant_id += 1

        # -- Victims (1–3 per case) --
        num_victims = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
        for v in range(num_victims):
            vname = victim_name if v == 0 else fake.name()
            lines.append(
                f"INSERT INTO Victim (VictimMasterID, CaseMasterID, VictimName, AgeYear, GenderID, VictimPolice) "
                f"VALUES ({victim_id}, {case_id}, {escape_sql(vname)}, {random.randint(5,75)}, {random.choice([1,2,3])}, "
                f"'{1 if random.random() < 0.05 else 0}');"
            )
            victim_id += 1

        # -- Accused (1–5 per case) --
        num_accused = random.choices([1, 2, 3, 4, 5], weights=[40, 25, 15, 10, 10])[0]
        case_accused_ids = []
        for a in range(num_accused):
            if a == 0:
                aname = accused_name
            elif random.random() < 0.15:
                aname = random.choice(repeat_offender_pool)  # Gang member
            else:
                aname = fake.name()
            lines.append(
                f"INSERT INTO Accused (AccusedMasterID, CaseMasterID, AccusedName, AgeYear, GenderID, PersonID) "
                f"VALUES ({accused_id}, {case_id}, {escape_sql(aname)}, {random.randint(18,55)}, {random.choice([1,2])}, 'A{a+1}');"
            )
            case_accused_ids.append(accused_id)
            accused_id += 1

        # -- ActSectionAssociation (1–3 sections per case) --
        num_sections = random.randint(1, 3)
        used_sections = set()
        for order in range(1, num_sections + 1):
            act_code = random.choice(list(IPC_SECTIONS.keys()))
            sec = random.choice(IPC_SECTIONS[act_code])
            sec_key = (act_code, sec[0])
            if sec_key not in used_sections:
                used_sections.add(sec_key)
                lines.append(
                    f"INSERT INTO ActSectionAssociation (CaseMasterID, ActID, SectionID, ActOrderID, SectionOrderID) "
                    f"VALUES ({case_id}, {escape_sql(act_code)}, {escape_sql(sec[0])}, {order}, {order});"
                )

        # -- ArrestSurrender (for ~60% of cases) --
        if random.random() < 0.6:
            for acc_id in random.sample(case_accused_ids, k=min(random.randint(1, 2), len(case_accused_ids))):
                arrest_date = crime_date + timedelta(days=random.randint(0, 60))
                lines.append(
                    f"INSERT INTO ArrestSurrender (ArrestSurrenderID, CaseMasterID, ArrestSurrenderTypeID, ArrestSurrenderDate, "
                    f"ArrestSurrenderStateId, ArrestSurrenderDistrictId, PoliceStationID, IOID, CourtID, AccusedMasterID, IsAccused, IsComplainantAccused) "
                    f"VALUES ({arrest_id}, {case_id}, {random.choice([1,2])}, '{arrest_date.isoformat()}', "
                    f"{KA_STATE_ID}, {dist_id}, {station_id}, {random.randint(1, NUM_EMPLOYEES)}, {court_id}, {acc_id}, TRUE, FALSE);"
                )

                # Junction table
                lines.append(
                    f"INSERT INTO inv_arrestsurrenderaccused (ArrestSurrenderID, AccusedMasterID) "
                    f"VALUES ({arrest_id}, {acc_id});"
                )
                arrest_id += 1

        # -- Inv_OccuranceTime --
        lines.append(
            f"INSERT INTO Inv_OccuranceTime (CaseMasterID, OccuranceFromDate, OccuranceToDate, PlaceOfOccurance, latitude, longitude) "
            f"VALUES ({case_id}, '{incident_from.isoformat()}', '{incident_to.isoformat()}', {escape_sql(location)}, {lat}, {lon});"
        )

        # -- ChargesheetDetails (for charge-sheeted cases) --
        if status_id == 2:   # Charge Sheeted
            cs_date = crime_date + timedelta(days=random.randint(30, 180))
            lines.append(
                f"INSERT INTO ChargesheetDetails (CSID, CaseMasterID, csdate, cstype, PolicePersonID) "
                f"VALUES ({cs_id}, {case_id}, '{cs_date.isoformat()}', 'A', {random.randint(1, NUM_EMPLOYEES)});"
            )
            cs_id += 1

        lines.append("")

    lines.append("COMMIT;")
    lines.append(f"\n-- Total Cases Generated: {NUM_CASES}")
    lines.append(f"-- Total Victims: {victim_id - 1}")
    lines.append(f"-- Total Accused: {accused_id - 1}")
    lines.append(f"-- Total Arrests: {arrest_id - 1}")
    lines.append(f"-- Total Chargesheets: {cs_id - 1}")

    # Write to file
    with open(OUTPUT_FILE, 'w') as f:
        f.write('\n'.join(lines))

    print(f"✅ Seed data written to {OUTPUT_FILE}")
    print(f"   Cases: {NUM_CASES}")
    print(f"   Victims: {victim_id - 1}")
    print(f"   Accused: {accused_id - 1}")
    print(f"   Arrests: {arrest_id - 1}")
    print(f"   Chargesheets: {cs_id - 1}")


if __name__ == "__main__":
    main()

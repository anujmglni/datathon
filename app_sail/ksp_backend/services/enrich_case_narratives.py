"""
Case Narrative Enrichment & Realistic Modus Operandi Generator for KSP Platform.
Enriches BriefFacts in CaseMaster by joining CrimeSubHead to generate specific, realistic
police narratives (motorcycle theft, mobile phone snatching, OTP cyber fraud,
locked house burglaries, gold chain snatching, highway collisions, etc.) and re-runs embedding.
"""

import sys
import random
import time
import logging
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import get_connection, release_connection
from services.embed_cases import embed_all_cases

logger = logging.getLogger(__name__)

# Specific Modus Operandi Narrative Templates grouped by exact CrimeSubHead
SUBHEAD_NARRATIVE_MAP = {
    "Theft": [
        "Complainant reported theft of a parked Hero Honda Splendor motorcycle (Reg KA-05-MJ-4821) outside residential apartment complex overnight. Ignition lock forcibly broken.",
        "Victim reported snatching of Samsung Galaxy smartphone by two unidentified suspects riding a black Pulsar motorcycle near the city bus stand.",
        "Theft of two-wheeler Honda Activa scooter (Reg KA-01-EE-9012) stolen from outside Metro station parking lot using master key.",
        "Complainant reported theft of iPhone 14 Pro mobile phone stolen from coat pocket while traveling on a crowded KSRTC public bus.",
        "Victim reported chain snatching of a 25-gram gold neck chain by pillion rider on a high-speed motorcycle during morning walk.",
        "Theft of silver ornaments and cash reported from a parked Maruti Suzuki car after suspects smashed the side window glass near commercial market area.",
        "Theft of laptop bag containing Lenovo ThinkPad laptop, company ID, and wallet stolen from parked car trunk.",
        "Complainant reported theft of Royal Enfield Bullet motorcycle (Reg KA-03-HV-1092) parked outside commercial office building."
    ],
    "Burglary": [
        "Nighttime house break-in burglary reported at locked residential quarters while family was away on vacation. Main entrance iron latch pried open, gold jewelry and Rs 1,50,000 cash stolen from bedroom almirah.",
        "Daytime house burglary reported at independent villa. Suspects broke rear window grill, ransacked cupboards, and decamped with silver utensils and electronics.",
        "Commercial shop burglary reported at electronics store. Shutter locks cut with heavy iron cutters, high-end smartphones and laptops stolen overnight.",
        "House break-in burglary targeting locked residence near highway bypass. Suspects bypassed security lock and stole gold coins and expensive watches."
    ],
    "Forgery": [
        "Victim received a fraudulent phone call from suspect impersonating a bank customer support manager requesting urgent KYC update. Victim shared OTP after which Rs 1,25,000 was fraudulently debited via UPI.",
        "Cyber financial fraud reported where victim was lured into a fake online telegram cryptocurrency investment scheme promising 300% return, losing Rs 4,50,000 across multiple bank transfers.",
        "Cheating case registered against suspects operating fraudulent job consultancy portal that collected Rs 75,000 from job seekers promising overseas employment visas.",
        "Credit card fraud reported where unauthorized online international transactions totaling Rs 92,000 were executed after victim's card details were compromised via phishing link.",
        "ATM card cloning fraud reported after victim used ATM kiosk with installed skimming device, resulting in fraudulent cash withdrawals of Rs 60,000."
    ],
    "Murder": [
        "Fatal homicide incident reported following heated property boundary and land inheritance dispute between neighboring relatives. Deceased suffered severe blunt force head trauma and fatal stab wounds inflicted with sharp sickles.",
        "Murder case registered after unidentified body of male aged 35 was discovered near railway tracks with deep cut injuries on neck caused by sharp weapons.",
        "Gang rivalry homicide incident reported where suspects ambushed victim outside hotel premises, attacking with iron rods and daggers causing fatal injuries.",
        "Domestic dispute culminating in fatal violence where suspect attacked spouse with heavy sharp wooden club inside residence."
    ],
    "Attempt to Commit Murder": [
        "Attempted homicide reported following violent altercation at local eatery. Accused stabbed victim multiple times in chest and abdomen with pocket knife causing critical injuries.",
        "Attempt to commit murder case registered after suspects fired gunshots targeting victim's car near bypass road following business rivalry."
    ],
    "Kidnapping": [
        "Forcible abduction and kidnapping incident reported where minor child was bundled into an unnumbered white van outside school premises demanding ransom.",
        "Human trafficking and illegal confinement case registered against syndicate luring young victims with fake factory job offers in neighboring states."
    ],
    "Rash Driving": [
        "Fatal road accident case registered involving rash driving by commercial heavy lorry truck colliding with a motorcycle on national highway.",
        "Over-speeding car crash reported near highway junction resulting in vehicle collision and severe injuries to passengers.",
        "Hit and run incident reported where an unidentified speeding SUV knocked down a pedestrian near traffic signal and fled the scene."
    ],
    "Breach of Trust": [
        "Criminal breach of trust registered against warehouse manager who fraudulently misappropriated inventory electronics worth Rs 12,000,000 and falsified dispatch logs.",
        "Breach of trust case filed against company accountant who diverted firm funds totaling Rs 18,50,000 to personal family bank accounts over 6 months."
    ],
    "Rioting": [
        "Violent group rioting and stone-pelting incident reported following local political rally clash. Suspects damaged public transport buses and street shops.",
        "Unlawful assembly and rioting reported between two local youth groups armed with wooden sticks and iron pipes causing public disturbance."
    ],
    "Mischief": [
        "Arson and malicious mischief case registered after unidentified miscreants set fire to parked agricultural tractor and haystacks in farmland.",
        "Mischief and property destruction case reported where suspects broke streetlight poles and damaged municipal water pipeline infrastructure."
    ]
}

DEFAULT_NARRATIVES = [
    "Incriminating incident reported involving local law and order violation. Investigating officers collected physical evidence from scene.",
    "Complaint registered regarding unlawful activities in station limits. Further investigation underway under relevant statutory provisions.",
    "Police action initiated following public complaint regarding suspicious gathering and public order disruption."
]


def enrich_database_narratives():
    """
    Updates BriefFacts across all 8,000 cases in CaseMaster by joining CrimeSubHead,
    generating specific, realistic crime narratives for theft, burglary, fraud, murder, etc.
    """
    print("\n" + "="*60)
    print("✨ NARRATIVE ENRICHMENT PIPELINE (SubHead Specific MO Mapping)")
    print("="*60 + "\n")

    conn, db_type = get_connection()
    try:
        sql = """
            SELECT 
                c.casemasterid,
                COALESCE(csh.crimeheadname, ch.crimegroupname, '') AS subhead_name,
                d.districtname
            FROM casemaster c
            JOIN unit u ON c.policestationid = u.unitid
            JOIN district d ON u.districtid = d.districtid
            LEFT JOIN crimesubhead csh ON c.crimeminorheadid = csh.crimesubheadid
            LEFT JOIN crimehead ch ON c.crimemajorheadid = ch.crimeheadid
            ORDER BY c.casemasterid ASC;
        """

        if db_type == "postgresql":
            with conn.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        else:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()

        total_rows = len(rows)
        print(f"📊 Found {total_rows} cases to enrich with realistic SubHead narratives.")

        updated_count = 0
        random.seed(42)

        for r in rows:
            cid = r[0]
            subhead = str(r[1] or "")
            district_name = str(r[2] or "Karnataka")

            # Match subhead name to specific narrative template
            matched_templates = None
            for key in SUBHEAD_NARRATIVE_MAP.keys():
                if key.lower() in subhead.lower():
                    matched_templates = SUBHEAD_NARRATIVE_MAP[key]
                    break

            if not matched_templates:
                if "theft" in subhead.lower() or "property" in subhead.lower():
                    matched_templates = SUBHEAD_NARRATIVE_MAP["Theft"]
                elif "fraud" in subhead.lower() or "cheat" in subhead.lower() or "trust" in subhead.lower():
                    matched_templates = SUBHEAD_NARRATIVE_MAP["Forgery"]
                elif "murder" in subhead.lower() or "hurt" in subhead.lower() or "homicide" in subhead.lower():
                    matched_templates = SUBHEAD_NARRATIVE_MAP["Murder"]
                elif "driving" in subhead.lower() or "accident" in subhead.lower():
                    matched_templates = SUBHEAD_NARRATIVE_MAP["Rash Driving"]
                else:
                    matched_templates = DEFAULT_NARRATIVES

            detailed_mo = random.choice(matched_templates)
            new_brief_facts = f"{detailed_mo} Reported in {district_name} jurisdiction. | Case ID {cid}."

            if db_type == "postgresql":
                with conn.cursor() as cur:
                    cur.execute("UPDATE casemaster SET brieffacts = %s WHERE casemasterid = %s;", (new_brief_facts, cid))
            else:
                conn.execute("UPDATE casemaster SET brieffacts = ? WHERE casemasterid = ?;", (new_brief_facts, cid))

            updated_count += 1

        if db_type == "postgresql":
            conn.commit()
        else:
            conn.commit()

        print(f"✅ Successfully enriched {updated_count} cases with SubHead-specific narratives.")

        # Re-run embedding pipeline
        print("\n🔄 Re-running batch embedding pipeline over enriched narratives...")
        embed_all_cases()

    finally:
        release_connection(conn, db_type)


if __name__ == "__main__":
    enrich_database_narratives()

#!/usr/bin/env python3
"""
COMPLETE 151 INDICATORS DEFINITIONS
All indicator definitions with patterns and keywords for document extraction
"""

def get_all_151_indicators():
    """Complete set of all 151 ESG indicators with extraction patterns"""

    return {
            # Module 1: General & Organizational Profile (7 indicators)
            "IMP-M01-I01": {
                "name": "Company Overview & Legal Information",
                "keywords": ["CIN", "company identification", "founded", "established", "incorporation"],
                "patterns": [r"CIN[:\s]*([A-Z0-9]{21})", r"founded[:\s]*(\d{4})", r"established[:\s]*(\d{4})"]
            },
            "IMP-M01-I02": {
                "name": "Primary Business Activities",
                "keywords": ["business activities", "operations", "revenue", "turnover", "manufacturing"],
                "patterns": [r"revenue[:\s]*INR\s*([\d,]+)", r"turnover[:\s]*([^\\n]+?)"]
            },
            "IMP-M01-I03": {
                "name": "Operational Footprint",
                "keywords": ["facilities", "locations", "operations", "footprint", "presence"],
                "patterns": [r"(\d+)\s*facilities", r"operations.*?(\d+).*?countries"]
            },
            "IMP-M01-I04": {
                "name": "Reporting Period & Boundary",
                "keywords": ["reporting period", "financial year", "FY", "April", "March"],
                "patterns": [r"FY\s*(\d{4})", r"April.*?(\d{4}).*?March.*?(\d{4})"]
            },
            "IMP-M01-I05": {
                "name": "Subsidiaries & Joint Ventures",
                "keywords": ["subsidiaries", "joint ventures", "wholly owned", "investments"],
                "patterns": [r"(\d+).*?subsidiaries", r"joint ventures.*?(\d+)"]
            },
            "IMP-M01-I06": {
                "name": "Stakeholder Engagement",
                "keywords": ["stakeholders", "engagement", "shareholders", "employees", "customers"],
                "patterns": [r"stakeholder.*?engagement", r"shareholders.*?(\d+)"]
            },
            "IMP-M01-I07": {
                "name": "Value Chain Mapping",
                "keywords": ["value chain", "supply chain", "mapping", "suppliers", "vendors"],
                "patterns": [r"value chain.*?mapping", r"(\d+).*?suppliers"]
            },

            # Module 2: Sustainability Management & Reporting (8 indicators)
            "IMP-M02-I01": {
                "name": "Sustainability Policies",
                "keywords": ["sustainability policy", "environmental policy", "ESG policy"],
                "patterns": [r"sustainability policy.*?(approved|adopted)", r"environmental policy"]
            },
            "IMP-M02-I02": {
                "name": "Sustainability Targets",
                "keywords": ["net zero", "carbon neutral", "targets", "goals", "2030", "2050"],
                "patterns": [r"net zero.*?(\d{4})", r"carbon neutral.*?(\d{4})", r"renewable energy.*?(\d+)%"]
            },
            "IMP-M02-I03": {
                "name": "Certifications & Standards",
                "keywords": ["ISO 14001", "ISO 45001", "ISO 50001", "certification"],
                "patterns": [r"ISO\s*(\d+)[:\s]*(\d{4})", r"certified.*?(ISO|OHSAS)"]
            },
            "IMP-M02-I04": {
                "name": "Sustainability Reporting Framework",
                "keywords": ["GRI", "SASB", "TCFD", "reporting framework"],
                "patterns": [r"GRI.*?standards", r"TCFD.*?disclosure", r"SASB.*?framework"]
            },
            "IMP-M02-I05": {
                "name": "ESG Risk Assessment",
                "keywords": ["ESG risk", "sustainability risk", "climate risk"],
                "patterns": [r"ESG.*?risk.*?assessment", r"climate.*?risk.*?evaluation"]
            },
            "IMP-M02-I06": {
                "name": "Sustainability Governance",
                "keywords": ["sustainability committee", "ESG committee", "environmental committee"],
                "patterns": [r"sustainability.*?committee", r"ESG.*?governance"]
            },
            "IMP-M02-I07": {
                "name": "Stakeholder Materiality Assessment",
                "keywords": ["materiality assessment", "materiality analysis", "stakeholder priorities"],
                "patterns": [r"materiality.*?assessment", r"material.*?topics"]
            },
            "IMP-M02-I08": {
                "name": "Third-Party ESG Ratings",
                "keywords": ["ESG rating", "sustainability rating", "MSCI", "Sustainalytics"],
                "patterns": [r"MSCI.*?rating.*?([A-Z]+)", r"ESG.*?score.*?([\d.]+)"]
            },

            # Module 3: Economic Performance (9 indicators)
            "IMP-M03-I01": {
                "name": "Total Revenue",
                "keywords": ["revenue", "net sales", "total income", "turnover"],
                "patterns": [r"revenue[:\s]*INR\s*([\d,]+)\s*crores?", r"net sales[:\s]*INR\s*([\d,]+)"]
            },
            "IMP-M03-I02": {
                "name": "Profit Before Tax",
                "keywords": ["profit before tax", "PBT", "operating profit"],
                "patterns": [r"PBT[:\s]*INR\s*([\d,]+)", r"profit before tax[:\s]*INR\s*([\d,]+)"]
            },
            "IMP-M03-I03": {
                "name": "Net Profit After Tax",
                "keywords": ["net profit", "PAT", "profit after tax"],
                "patterns": [r"PAT[:\s]*INR\s*([\d,]+)", r"net profit[:\s]*INR\s*([\d,]+)"]
            },
            "IMP-M03-I04": {
                "name": "EBITDA",
                "keywords": ["EBITDA", "earnings before interest", "operating earnings"],
                "patterns": [r"EBITDA[:\s]*INR\s*([\d,]+)", r"operating.*?earnings[:\s]*INR\s*([\d,]+)"]
            },
            "IMP-M03-I05": {
                "name": "Market Capitalization",
                "keywords": ["market cap", "market capitalisation", "market value"],
                "patterns": [r"market.*?cap[:\s]*INR\s*([\d,]+)", r"market.*?value[:\s]*INR\s*([\d,]+)"]
            },
            "IMP-M03-I06": {
                "name": "Dividend Distribution",
                "keywords": ["dividend", "distribution", "shareholder payout"],
                "patterns": [r"dividend[:\s]*INR\s*([\d,]+)", r"dividend.*?per.*?share"]
            },
            "IMP-M03-I07": {
                "name": "Tax Payments",
                "keywords": ["tax paid", "income tax", "corporate tax"],
                "patterns": [r"tax.*?paid[:\s]*INR\s*([\d,]+)", r"income tax[:\s]*INR\s*([\d,]+)"]
            },
            "IMP-M03-I08": {
                "name": "Economic Value Generated",
                "keywords": ["economic value", "value creation", "stakeholder value"],
                "patterns": [r"economic.*?value.*?generated[:\s]*INR\s*([\d,]+)"]
            },
            "IMP-M03-I09": {
                "name": "Economic Value Distributed",
                "keywords": ["value distributed", "payments to stakeholders", "economic distribution"],
                "patterns": [r"value.*?distributed[:\s]*INR\s*([\d,]+)"]
            },

            # Module 4: Risk & Opportunity Management (5 indicators)
            "IMP-M04-I01": {
                "name": "Risk Management Framework",
                "keywords": ["risk management", "risk framework", "enterprise risk"],
                "patterns": [r"risk.*?management.*?framework", r"enterprise.*?risk"]
            },
            "IMP-M04-I02": {
                "name": "Climate-Related Risks",
                "keywords": ["climate risk", "physical risk", "transition risk"],
                "patterns": [r"climate.*?risk.*?assessment", r"physical.*?risk.*?evaluation"]
            },
            "IMP-M04-I03": {
                "name": "Operational Risk Assessment",
                "keywords": ["operational risk", "business continuity", "operational resilience"],
                "patterns": [r"operational.*?risk.*?assessment", r"business.*?continuity"]
            },
            "IMP-M04-I04": {
                "name": "Strategic Risk Management",
                "keywords": ["strategic risk", "business strategy", "strategic planning"],
                "patterns": [r"strategic.*?risk.*?management", r"strategic.*?planning"]
            },
            "IMP-M04-I05": {
                "name": "Opportunity Identification",
                "keywords": ["business opportunities", "growth opportunities", "market opportunities"],
                "patterns": [r"business.*?opportunities", r"growth.*?opportunities"]
            },

            # Module 5: GHG Emissions & Climate Change (9 indicators)
            "IMP-M05-I01": {
                "name": "Scope 1 Emissions",
                "keywords": ["scope 1", "direct emissions", "fuel combustion"],
                "patterns": [r"scope 1[:\s]*([\d,]+)\s*tCO2e?", r"direct emissions[:\s]*([\d,]+)"]
            },
            "IMP-M05-I02": {
                "name": "Scope 2 Emissions",
                "keywords": ["scope 2", "electricity emissions", "purchased electricity"],
                "patterns": [r"scope 2[:\s]*([\d,]+)\s*tCO2e?", r"electricity emissions[:\s]*([\d,]+)"]
            },
            "IMP-M05-I03": {
                "name": "Scope 3 Emissions",
                "keywords": ["scope 3", "indirect emissions", "value chain"],
                "patterns": [r"scope 3[:\s]*([\d,]+)\s*tCO2e?", r"indirect emissions[:\s]*([\d,]+)"]
            },
            "IMP-M05-I04": {
                "name": "Total GHG Emissions",
                "keywords": ["total emissions", "GHG emissions", "carbon footprint"],
                "patterns": [r"total.*?emissions[:\s]*([\d,]+)", r"GHG emissions[:\s]*([\d,]+)\s*tCO2e?"]
            },
            "IMP-M05-I05": {
                "name": "Carbon Intensity",
                "keywords": ["carbon intensity", "emissions per unit", "specific emissions"],
                "patterns": [r"carbon intensity[:\s]*([\d.]+)", r"emissions.*?per.*?unit[:\s]*([\d.]+)"]
            },
            "IMP-M05-I06": {
                "name": "Carbon Neutrality Goals",
                "keywords": ["carbon neutral", "net zero", "carbon neutrality"],
                "patterns": [r"carbon neutral.*?(\d{4})", r"net zero.*?target.*?(\d{4})"]
            },
            "IMP-M05-I07": {
                "name": "Carbon Offsets",
                "keywords": ["carbon offsets", "offset credits", "carbon credits"],
                "patterns": [r"carbon offsets[:\s]*([\d,]+)", r"offset.*?credits[:\s]*([\d,]+)"]
            },
            "IMP-M05-I08": {
                "name": "Science-Based Targets",
                "keywords": ["science based targets", "SBTi", "science based"],
                "patterns": [r"science.*?based.*?targets?", r"SBTi.*?commitment"]
            },
            "IMP-M05-I09": {
                "name": "Climate Change Adaptation",
                "keywords": ["climate adaptation", "resilience measures", "climate risk mitigation"],
                "patterns": [r"climate.*?adaptation.*?measures", r"resilience.*?building"]
            },

            # Module 6: Energy (6 indicators)
            "IMP-M06-I01": {
                "name": "Total Energy Consumption",
                "keywords": ["energy consumption", "total energy", "energy usage"],
                "patterns": [r"energy consumption[:\s]*([\d,]+)\s*(TJ|MWh|GJ)", r"total energy[:\s]*([\d,]+)"]
            },
            "IMP-M06-I02": {
                "name": "Renewable Energy",
                "keywords": ["renewable energy", "solar", "wind", "clean energy"],
                "patterns": [r"renewable energy[:\s]*([\d,]+)", r"solar.*?([\d,]+)\s*(MW|MWh)"]
            },
            "IMP-M06-I03": {
                "name": "Energy Intensity",
                "keywords": ["energy intensity", "specific energy", "energy per unit"],
                "patterns": [r"energy intensity[:\s]*([\d.]+)", r"specific energy[:\s]*([\d.]+)"]
            },
            "IMP-M06-I04": {
                "name": "Energy Efficiency",
                "keywords": ["energy efficiency", "energy savings", "efficiency programs"],
                "patterns": [r"energy.*?efficiency.*?([\d.]+)%", r"energy.*?savings[:\s]*([\d,]+)"]
            },
            "IMP-M06-I05": {
                "name": "Grid Electricity Consumption",
                "keywords": ["grid electricity", "purchased power", "electricity from grid"],
                "patterns": [r"grid electricity[:\s]*([\d,]+)", r"purchased.*?power[:\s]*([\d,]+)"]
            },
            "IMP-M06-I06": {
                "name": "Self-Generated Energy",
                "keywords": ["self generated", "captive power", "own generation"],
                "patterns": [r"self.*?generated[:\s]*([\d,]+)", r"captive.*?power[:\s]*([\d,]+)"]
            },

            # Module 7: Water & Effluents (10 indicators)
            "IMP-M07-I01": {
                "name": "Total Water Consumption",
                "keywords": ["water consumption", "water usage", "water withdrawal"],
                "patterns": [r"water consumption[:\s]*([\d,]+)\s*(ML|megalitres|cubic meters)"]
            },
            "IMP-M07-I02": {
                "name": "Water Withdrawal by Source",
                "keywords": ["groundwater", "surface water", "municipal water"],
                "patterns": [r"groundwater[:\s]*([\d,]+)", r"surface water[:\s]*([\d,]+)"]
            },
            "IMP-M07-I03": {
                "name": "Water Recycling",
                "keywords": ["water recycled", "water reused", "recycling rate"],
                "patterns": [r"water recycled[:\s]*([\d,]+)", r"recycling.*?rate[:\s]*([\d,]+)%"]
            },
            "IMP-M07-I04": {
                "name": "Water Discharge",
                "keywords": ["water discharge", "effluent discharge", "wastewater"],
                "patterns": [r"water discharge[:\s]*([\d,]+)", r"effluent.*?discharge[:\s]*([\d,]+)"]
            },
            "IMP-M07-I05": {
                "name": "Water Intensity",
                "keywords": ["water intensity", "specific water", "water per unit"],
                "patterns": [r"water intensity[:\s]*([\d.]+)", r"specific water[:\s]*([\d.]+)"]
            },
            "IMP-M07-I06": {
                "name": "Water Quality",
                "keywords": ["water quality", "BOD", "COD", "TSS"],
                "patterns": [r"BOD[:\s]*([\d,]+)", r"COD[:\s]*([\d,]+)", r"TSS[:\s]*([\d,]+)"]
            },
            "IMP-M07-I07": {
                "name": "Zero Liquid Discharge",
                "keywords": ["zero liquid discharge", "ZLD", "no discharge"],
                "patterns": [r"zero liquid discharge", r"ZLD.*?implemented"]
            },
            "IMP-M07-I08": {
                "name": "Rainwater Harvesting",
                "keywords": ["rainwater harvesting", "rain water", "harvesting capacity"],
                "patterns": [r"rainwater.*?harvesting[:\s]*([\d,]+)", r"rain water.*?capacity"]
            },
            "IMP-M07-I09": {
                "name": "Water Conservation",
                "keywords": ["water conservation", "water savings", "conservation measures"],
                "patterns": [r"water.*?conservation[:\s]*([^.]+)", r"water.*?savings[:\s]*([\d,]+)"]
            },
            "IMP-M07-I10": {
                "name": "Water Stress Areas",
                "keywords": ["water stress", "water scarce", "stressed regions"],
                "patterns": [r"water.*?stress.*?areas", r"water.*?scarce.*?regions"]
            },

            # Module 8: Biodiversity & Land Use (9 indicators)
            "IMP-M08-I01": {
                "name": "Land Use & Land Use Change",
                "keywords": ["land use", "land area", "operational land"],
                "patterns": [r"land.*?area[:\s]*([\d,]+)", r"operational.*?land[:\s]*([\d,]+)"]
            },
            "IMP-M08-I02": {
                "name": "Biodiversity Conservation",
                "keywords": ["biodiversity", "conservation", "protected areas"],
                "patterns": [r"biodiversity.*?conservation", r"protected.*?areas[:\s]*([\d,]+)"]
            },
            "IMP-M08-I03": {
                "name": "Afforestation & Reforestation",
                "keywords": ["afforestation", "plantation", "tree planting"],
                "patterns": [r"afforestation[:\s]*([\d,]+)", r"trees.*?planted[:\s]*([\d,]+)"]
            },
            "IMP-M08-I04": {
                "name": "Green Belt Development",
                "keywords": ["green belt", "green cover", "landscaping"],
                "patterns": [r"green belt[:\s]*([\d,]+)", r"green.*?cover[:\s]*([\d.]+)%"]
            },
            "IMP-M08-I05": {
                "name": "Ecological Impact Assessment",
                "keywords": ["impact assessment", "EIA", "environmental impact"],
                "patterns": [r"environmental.*?impact.*?assessment", r"EIA.*?conducted"]
            },
            "IMP-M08-I06": {
                "name": "Habitat Protection",
                "keywords": ["habitat protection", "wildlife protection", "ecosystem preservation"],
                "patterns": [r"habitat.*?protection", r"wildlife.*?conservation"]
            },
            "IMP-M08-I07": {
                "name": "Restoration Projects",
                "keywords": ["restoration projects", "habitat restoration", "ecosystem restoration"],
                "patterns": [r"restoration.*?projects[:\s]*(\d+)", r"habitat.*?restoration"]
            },
            "IMP-M08-I08": {
                "name": "No Net Loss Policy",
                "keywords": ["no net loss", "biodiversity offset", "compensation"],
                "patterns": [r"no net loss", r"biodiversity.*?offset"]
            },
            "IMP-M08-I09": {
                "name": "Species Conservation",
                "keywords": ["species conservation", "endangered species", "species protection"],
                "patterns": [r"species.*?conservation", r"endangered.*?species"]
            },

            # Module 9: Waste & Materials (7 indicators)
            "IMP-M09-I01": {
                "name": "Total Waste Generated",
                "keywords": ["total waste", "waste generated", "waste production", "total waste generated"],
                "patterns": [r"total waste[:\s]*([\d,]+)\s*tonnes", r"waste generated[:\s]*([\d,]+)", r"waste production[:\s]*([\d,]+)"]
            },
            "IMP-M09-I02": {
                "name": "Hazardous Waste",
                "keywords": ["hazardous waste", "dangerous waste", "toxic waste", "hazardous materials"],
                "patterns": [r"hazardous waste[:\s]*([\d,]+)", r"dangerous waste[:\s]*([\d,]+)", r"toxic waste[:\s]*([\d,]+)"]
            },
            "IMP-M09-I03": {
                "name": "Non-Hazardous Waste",
                "keywords": ["non-hazardous waste", "general waste", "solid waste", "municipal waste"],
                "patterns": [r"non.?hazardous waste[:\s]*([\d,]+)", r"general waste[:\s]*([\d,]+)", r"solid waste[:\s]*([\d,]+)"]
            },
            "IMP-M09-I04": {
                "name": "Waste Recycling",
                "keywords": ["waste recycled", "recycling rate", "waste recovery", "recycled waste"],
                "patterns": [r"waste recycled[:\s]*([\d,]+)", r"recycling rate[:\s]*([\d,]+)%", r"waste recovery[:\s]*([\d,]+)"]
            },
            "IMP-M09-I05": {
                "name": "Waste to Landfill",
                "keywords": ["waste to landfill", "landfill disposal", "disposed waste"],
                "patterns": [r"waste.*?landfill[:\s]*([\d,]+)", r"landfill.*?disposal[:\s]*([\d,]+)"]
            },
            "IMP-M09-I06": {
                "name": "Waste Disposal Methods",
                "keywords": ["waste disposal", "disposal methods", "treatment methods", "waste management"],
                "patterns": [r"waste disposal[:\s]*([^.]+)", r"disposal methods[:\s]*([^.]+)"]
            },
            "IMP-M09-I07": {
                "name": "Waste Management Initiatives",
                "keywords": ["waste management", "5R approach", "circular economy", "waste reduction"],
                "patterns": [r"waste management[:\s]*([^.]+)", r"5R approach", r"circular economy"]
            },

            # Module 10: Raw Materials & Resource Efficiency (6 indicators)
            "IMP-M10-I01": {
                "name": "Raw Materials Consumption",
                "keywords": ["raw materials", "material consumption", "total materials", "materials used"],
                "patterns": [r"raw materials[:\s]*([\d,]+)", r"material consumption[:\s]*([\d,]+)", r"total materials[:\s]*([\d,]+)"]
            },
            "IMP-M10-I02": {
                "name": "Renewable Materials",
                "keywords": ["renewable materials", "bio-based materials", "sustainable materials"],
                "patterns": [r"renewable materials[:\s]*([\d,]+)", r"bio.?based materials[:\s]*([\d,]+)"]
            },
            "IMP-M10-I03": {
                "name": "Recycled Content",
                "keywords": ["recycled content", "recycled materials", "post-consumer recycled"],
                "patterns": [r"recycled content[:\s]*([\d,]+)", r"recycled materials[:\s]*([\d,]+)"]
            },
            "IMP-M10-I04": {
                "name": "Material Intensity",
                "keywords": ["material intensity", "material efficiency", "materials per unit"],
                "patterns": [r"material intensity[:\s]*([\d.]+)", r"materials.*?per.*?unit[:\s]*([\d.]+)"]
            },
            "IMP-M10-I05": {
                "name": "Sustainable Materials Sourcing",
                "keywords": ["sustainable sourcing", "responsible sourcing", "certified materials"],
                "patterns": [r"sustainable sourcing[:\s]*([^.]+)", r"responsible sourcing[:\s]*([^.]+)"]
            },
            "IMP-M10-I06": {
                "name": "Material Efficiency Programs",
                "keywords": ["material efficiency", "resource efficiency", "lean manufacturing"],
                "patterns": [r"material efficiency[:\s]*([^.]+)", r"resource efficiency[:\s]*([^.]+)"]
            },

            # Module 11: Air Quality & Emissions (5 indicators)
            "IMP-M11-I01": {
                "name": "Air Pollutant Emissions",
                "keywords": ["NOx", "SOx", "air pollutants", "emissions to air"],
                "patterns": [r"NOx[:\s]*([\d,]+)", r"SOx[:\s]*([\d,]+)", r"air pollutants[:\s]*([\d,]+)"]
            },
            "IMP-M11-I02": {
                "name": "Particulate Matter",
                "keywords": ["particulate matter", "PM10", "PM2.5", "dust emissions"],
                "patterns": [r"PM10[:\s]*([\d,]+)", r"PM2\.5[:\s]*([\d,]+)", r"particulate matter[:\s]*([\d,]+)"]
            },
            "IMP-M11-I03": {
                "name": "Ozone Depleting Substances",
                "keywords": ["ODS", "ozone depleting", "CFCs", "HCFCs"],
                "patterns": [r"ODS[:\s]*([\d,]+)", r"ozone depleting[:\s]*([\d,]+)", r"CFCs[:\s]*([\d,]+)"]
            },
            "IMP-M11-I04": {
                "name": "Volatile Organic Compounds",
                "keywords": ["VOC", "volatile organic", "organic compounds"],
                "patterns": [r"VOC[:\s]*([\d,]+)", r"volatile organic[:\s]*([\d,]+)"]
            },
            "IMP-M11-I05": {
                "name": "Noise Pollution",
                "keywords": ["noise pollution", "noise levels", "sound pollution", "acoustic emissions"],
                "patterns": [r"noise.*?levels[:\s]*([\d.]+)", r"noise pollution[:\s]*([^.]+)"]
            },

            # Module 12: Circular Economy (5 indicators)
            "IMP-M12-I01": {
                "name": "Circular Design Principles",
                "keywords": ["circular design", "design for recycling", "eco-design", "design for circularity"],
                "patterns": [r"circular design[:\s]*([^.]+)", r"eco.?design[:\s]*([^.]+)"]
            },
            "IMP-M12-I02": {
                "name": "Product Life Cycle Management",
                "keywords": ["life cycle", "LCA", "lifecycle assessment", "cradle to cradle"],
                "patterns": [r"life cycle[:\s]*([^.]+)", r"LCA[:\s]*([^.]+)"]
            },
            "IMP-M12-I03": {
                "name": "Material Recovery",
                "keywords": ["material recovery", "end-of-life recovery", "product take-back"],
                "patterns": [r"material recovery[:\s]*([\d,]+)", r"end.?of.?life.*?recovery[:\s]*([\d,]+)"]
            },
            "IMP-M12-I04": {
                "name": "Resource Efficiency",
                "keywords": ["resource efficiency", "circular economy", "resource optimization"],
                "patterns": [r"resource efficiency[:\s]*([^.]+)", r"circular economy[:\s]*([^.]+)"]
            },
            "IMP-M12-I05": {
                "name": "Closed-Loop Systems",
                "keywords": ["closed loop", "zero waste", "circular systems"],
                "patterns": [r"closed.?loop[:\s]*([^.]+)", r"zero waste[:\s]*([^.]+)"]
            },

            # Module 13: Supply Chain & Procurement (7 indicators)
            "IMP-M13-I01": {
                "name": "Supplier ESG Assessment",
                "keywords": ["supplier assessment", "vendor assessment", "supplier ESG", "supplier evaluation"],
                "patterns": [r"(\d+).*?suppliers.*?assessed", r"supplier.*?assessment[:\s]*([^.]+)"]
            },
            "IMP-M13-I02": {
                "name": "Supplier Audits",
                "keywords": ["supplier audits", "vendor audits", "supply chain audits"],
                "patterns": [r"(\d+).*?supplier.*?audits", r"supplier audits[:\s]*(\d+)"]
            },
            "IMP-M13-I03": {
                "name": "Local Sourcing",
                "keywords": ["local sourcing", "local procurement", "regional suppliers"],
                "patterns": [r"local sourcing[:\s]*([\d,]+)%", r"local procurement[:\s]*([\d,]+)"]
            },
            "IMP-M13-I04": {
                "name": "Supplier Code of Conduct",
                "keywords": ["supplier code", "vendor code", "code of conduct"],
                "patterns": [r"supplier.*?code[:\s]*([^.]+)", r"code of conduct[:\s]*([^.]+)"]
            },
            "IMP-M13-I05": {
                "name": "Supply Chain Risk Management",
                "keywords": ["supply chain risk", "supplier risk", "procurement risk"],
                "patterns": [r"supply chain.*?risk[:\s]*([^.]+)", r"supplier.*?risk[:\s]*([^.]+)"]
            },
            "IMP-M13-I06": {
                "name": "Vendor Sustainability Development",
                "keywords": ["vendor development", "supplier development", "capability building"],
                "patterns": [r"vendor development[:\s]*([^.]+)", r"supplier development[:\s]*([^.]+)"]
            },
            "IMP-M13-I07": {
                "name": "Sustainable Procurement Policy",
                "keywords": ["sustainable procurement", "green procurement", "responsible procurement"],
                "patterns": [r"sustainable procurement[:\s]*([^.]+)", r"green procurement[:\s]*([^.]+)"]
            },

            # Module 14: Labor & Human Rights (13 indicators)
            "IMP-M14-I01": {
                "name": "Total Workforce",
                "keywords": ["total employees", "total workforce", "headcount", "employee count"],
                "patterns": [r"total employees[:\s]*([\d,]+)", r"total workforce[:\s]*([\d,]+)", r"headcount[:\s]*([\d,]+)"]
            },
            "IMP-M14-I02": {
                "name": "Employee Demographics by Gender",
                "keywords": ["male employees", "female employees", "gender diversity", "women employees"],
                "patterns": [r"male[:\s]*([\d,]+)", r"female[:\s]*([\d,]+)", r"women[:\s]*([\d,]+)"]
            },
            "IMP-M14-I03": {
                "name": "Employee Compensation & Benefits",
                "keywords": ["employee compensation", "total compensation", "benefits", "salary"],
                "patterns": [r"employee compensation[:\s]*INR\s*([\d,]+)", r"total compensation[:\s]*([^.]+)"]
            },
            "IMP-M14-I04": {
                "name": "Employee Turnover",
                "keywords": ["employee turnover", "attrition", "turnover rate", "voluntary turnover"],
                "patterns": [r"turnover[:\s]*([\d.]+)%", r"attrition[:\s]*([\d.]+)%"]
            },
            "IMP-M14-I05": {
                "name": "New Hires",
                "keywords": ["new hires", "new employees", "fresh recruitment", "hiring"],
                "patterns": [r"new hires[:\s]*([\d,]+)", r"new employees[:\s]*([\d,]+)"]
            },
            "IMP-M14-I06": {
                "name": "Employee Benefits",
                "keywords": ["employee benefits", "health insurance", "medical benefits", "welfare"],
                "patterns": [r"employee benefits[:\s]*([^.]+)", r"health insurance[:\s]*([^.]+)"]
            },
            "IMP-M14-I07": {
                "name": "Temporary/Contract Workers",
                "keywords": ["contract workers", "temporary workers", "contingent workforce"],
                "patterns": [r"contract workers[:\s]*([\d,]+)", r"temporary workers[:\s]*([\d,]+)"]
            },
            "IMP-M14-I08": {
                "name": "Age Diversity",
                "keywords": ["age diversity", "age distribution", "generational diversity"],
                "patterns": [r"age.*?diversity[:\s]*([^.]+)", r"age.*?distribution[:\s]*([^.]+)"]
            },
            "IMP-M14-I09": {
                "name": "Geographic Diversity",
                "keywords": ["geographic diversity", "geographical distribution", "regional presence"],
                "patterns": [r"geographic.*?diversity[:\s]*([^.]+)", r"geographical.*?distribution[:\s]*([^.]+)"]
            },
            "IMP-M14-I10": {
                "name": "Disability Inclusion",
                "keywords": ["disability inclusion", "persons with disabilities", "PWD", "differently abled"],
                "patterns": [r"(\d+).*?persons.*?disabilities", r"disability inclusion[:\s]*([^.]+)"]
            },
            "IMP-M14-I11": {
                "name": "Parental Leave",
                "keywords": ["parental leave", "maternity leave", "paternity leave", "family leave"],
                "patterns": [r"maternity leave[:\s]*([^.]+)", r"parental leave[:\s]*([^.]+)"]
            },
            "IMP-M14-I12": {
                "name": "Work-Life Balance",
                "keywords": ["work life balance", "flexible working", "remote work", "work from home"],
                "patterns": [r"work.?life balance[:\s]*([^.]+)", r"flexible working[:\s]*([^.]+)"]
            },
            "IMP-M14-I13": {
                "name": "Transition Assistance & Career Endings",
                "keywords": ["transition assistance", "outplacement", "career transition", "retirement"],
                "patterns": [r"transition assistance[:\s]*([^.]+)", r"outplacement[:\s]*([^.]+)"]
            },

            # Module 15: Training & Skill Development (10 indicators)
            "IMP-M15-I01": {
                "name": "Training Hours",
                "keywords": ["training hours", "total training", "learning hours", "development hours"],
                "patterns": [r"training hours[:\s]*([\d,]+)", r"total training[:\s]*([\d,]+).*?hours"]
            },
            "IMP-M15-I02": {
                "name": "Skill Development Programs",
                "keywords": ["skill development", "upskilling", "reskilling", "capability building"],
                "patterns": [r"skill development[:\s]*([^.]+)", r"upskilling[:\s]*([^.]+)"]
            },
            "IMP-M15-I03": {
                "name": "Leadership Development",
                "keywords": ["leadership development", "leadership training", "management development"],
                "patterns": [r"leadership development[:\s]*([^.]+)", r"leadership training[:\s]*([^.]+)"]
            },
            "IMP-M15-I04": {
                "name": "Training Investment",
                "keywords": ["training investment", "learning investment", "training spend", "L&D budget"],
                "patterns": [r"training.*?investment[:\s]*INR\s*([\d,]+)", r"learning.*?investment[:\s]*([^.]+)"]
            },
            "IMP-M15-I05": {
                "name": "Training Programs",
                "keywords": ["training programs", "courses offered", "learning programs"],
                "patterns": [r"(\d+).*?training.*?programs", r"(\d+).*?courses.*?offered"]
            },
            "IMP-M15-I06": {
                "name": "E-Learning & Digital Learning",
                "keywords": ["e-learning", "digital learning", "online training", "virtual learning"],
                "patterns": [r"e.?learning[:\s]*([^.]+)", r"digital learning[:\s]*([^.]+)"]
            },
            "IMP-M15-I07": {
                "name": "Professional Development",
                "keywords": ["professional development", "career development", "continuing education"],
                "patterns": [r"professional development[:\s]*([^.]+)", r"career development[:\s]*([^.]+)"]
            },
            "IMP-M15-I08": {
                "name": "Certification Programs",
                "keywords": ["certification programs", "professional certifications", "skill certifications"],
                "patterns": [r"certification programs[:\s]*([^.]+)", r"professional certifications[:\s]*([^.]+)"]
            },
            "IMP-M15-I09": {
                "name": "Knowledge Management",
                "keywords": ["knowledge management", "knowledge sharing", "best practices"],
                "patterns": [r"knowledge management[:\s]*([^.]+)", r"knowledge sharing[:\s]*([^.]+)"]
            },
            "IMP-M15-I10": {
                "name": "Mentoring & Coaching",
                "keywords": ["mentoring", "coaching", "mentorship programs", "peer learning"],
                "patterns": [r"mentoring[:\s]*([^.]+)", r"coaching[:\s]*([^.]+)", r"mentorship programs[:\s]*([^.]+)"]
            },

            # Module 16: Diversity, Equity & Inclusion (6 indicators)
            "IMP-M16-I01": {
                "name": "Women in Leadership",
                "keywords": ["women in leadership", "female leadership", "women executives", "gender leadership"],
                "patterns": [r"women.*?leadership[:\s]*([\d.]+)%", r"female.*?leadership[:\s]*([\d.]+)"]
            },
            "IMP-M16-I02": {
                "name": "Gender Pay Equity",
                "keywords": ["gender pay gap", "pay equity", "equal pay", "compensation equity"],
                "patterns": [r"gender.*?pay.*?gap[:\s]*([\d.]+)%", r"pay equity[:\s]*([^.]+)"]
            },
            "IMP-M16-I03": {
                "name": "Board Diversity",
                "keywords": ["board diversity", "women on board", "independent directors", "board composition"],
                "patterns": [r"women.*?board[:\s]*([\d.]+)%", r"board diversity[:\s]*([^.]+)"]
            },
            "IMP-M16-I04": {
                "name": "Minority Representation",
                "keywords": ["minority representation", "scheduled castes", "scheduled tribes", "ethnic diversity"],
                "patterns": [r"scheduled castes[:\s]*([\d.]+)%", r"scheduled tribes[:\s]*([\d.]+)%"]
            },
            "IMP-M16-I05": {
                "name": "Inclusive Hiring",
                "keywords": ["inclusive hiring", "diversity hiring", "equal opportunity"],
                "patterns": [r"inclusive hiring[:\s]*([^.]+)", r"diversity.*?hiring[:\s]*([^.]+)"]
            },
            "IMP-M16-I06": {
                "name": "Diversity & Inclusion Policy",
                "keywords": ["diversity policy", "inclusion policy", "D&I policy", "equal opportunity policy"],
                "patterns": [r"diversity.*?policy[:\s]*([^.]+)", r"D&I policy[:\s]*([^.]+)"]
            },

            # Module 17: Human Rights (4 indicators)
            "IMP-M17-I01": {
                "name": "Anti-Discrimination Policy",
                "keywords": ["anti-discrimination", "non-discrimination", "equal treatment", "fair treatment"],
                "patterns": [r"anti.?discrimination[:\s]*([^.]+)", r"non.?discrimination[:\s]*([^.]+)"]
            },
            "IMP-M17-I02": {
                "name": "Harassment Prevention",
                "keywords": ["harassment prevention", "anti-harassment", "POSH", "sexual harassment"],
                "patterns": [r"harassment prevention[:\s]*([^.]+)", r"POSH[:\s]*([^.]+)"]
            },
            "IMP-M17-I03": {
                "name": "Grievance Mechanism",
                "keywords": ["grievance mechanism", "complaint system", "whistleblower", "grievance redressal"],
                "patterns": [r"grievance.*?mechanism[:\s]*([^.]+)", r"complaint.*?system[:\s]*([^.]+)"]
            },
            "IMP-M17-I04": {
                "name": "Equal Opportunity",
                "keywords": ["equal opportunity", "equal employment", "fair employment", "non-bias"],
                "patterns": [r"equal opportunity[:\s]*([^.]+)", r"equal employment[:\s]*([^.]+)"]
            },

            # Module 18: Community & Social Impact (7 indicators)
            "IMP-M18-I01": {
                "name": "CSR Expenditure",
                "keywords": ["CSR expenditure", "CSR spend", "CSR investment", "social spending"],
                "patterns": [r"CSR.*?expenditure[:\s]*INR\s*([\d,]+)", r"CSR.*?spend[:\s]*INR\s*([\d,]+)"]
            },
            "IMP-M18-I02": {
                "name": "Education Programs",
                "keywords": ["education programs", "students benefited", "educational initiatives", "learning programs"],
                "patterns": [r"(\d+).*?students.*?benefited", r"education programs[:\s]*([^.]+)"]
            },
            "IMP-M18-I03": {
                "name": "Community Development Projects",
                "keywords": ["community development", "community projects", "social projects", "rural development"],
                "patterns": [r"(\d+).*?community.*?projects", r"community development[:\s]*([^.]+)"]
            },
            "IMP-M18-I04": {
                "name": "CSR Compliance",
                "keywords": ["CSR compliance", "2% spending", "CSR mandatory", "CSR requirement"],
                "patterns": [r"CSR.*?compliance[:\s]*([^.]+)", r"2%.*?spending[:\s]*([^.]+)"]
            },
            "IMP-M18-I05": {
                "name": "Local Community Development",
                "keywords": ["local community", "village development", "local programs", "community engagement"],
                "patterns": [r"(\d+).*?villages", r"local community[:\s]*([^.]+)"]
            },
            "IMP-M18-I06": {
                "name": "Social Programs",
                "keywords": ["healthcare camps", "health programs", "social welfare", "community health"],
                "patterns": [r"(\d+).*?healthcare.*?camps", r"health programs[:\s]*([^.]+)"]
            },
            "IMP-M18-I07": {
                "name": "Traditional Knowledge & Intellectual Property",
                "keywords": ["traditional knowledge", "indigenous knowledge", "local knowledge", "cultural heritage"],
                "patterns": [r"traditional knowledge[:\s]*([^.]+)", r"indigenous knowledge[:\s]*([^.]+)"]
            },

            # Module 19: Customer & Product Responsibility (8 indicators)
            "IMP-M19-I01": {
                "name": "Product Safety & Quality",
                "keywords": ["product safety", "quality standards", "safety standards", "product compliance"],
                "patterns": [r"product safety[:\s]*([^.]+)", r"quality standards[:\s]*([^.]+)"]
            },
            "IMP-M19-I02": {
                "name": "Customer Satisfaction",
                "keywords": ["customer satisfaction", "CSAT", "customer experience", "customer rating"],
                "patterns": [r"customer satisfaction[:\s]*([\d.]+)", r"CSAT[:\s]*([\d.]+)"]
            },
            "IMP-M19-I03": {
                "name": "Product Recalls",
                "keywords": ["product recalls", "recall notices", "product withdrawal", "safety recalls"],
                "patterns": [r"(\d+).*?product.*?recalls", r"product recalls[:\s]*([^.]+)"]
            },
            "IMP-M19-I04": {
                "name": "Consumer Protection",
                "keywords": ["consumer protection", "consumer rights", "customer protection"],
                "patterns": [r"consumer protection[:\s]*([^.]+)", r"consumer rights[:\s]*([^.]+)"]
            },
            "IMP-M19-I05": {
                "name": "Customer Privacy & Data Protection",
                "keywords": ["data privacy", "customer privacy", "data protection", "GDPR"],
                "patterns": [r"data privacy[:\s]*([^.]+)", r"customer privacy[:\s]*([^.]+)"]
            },
            "IMP-M19-I06": {
                "name": "Product Labeling",
                "keywords": ["product labeling", "labelling compliance", "product information"],
                "patterns": [r"product.*?labeling[:\s]*([^.]+)", r"labelling.*?compliance[:\s]*([^.]+)"]
            },
            "IMP-M19-I07": {
                "name": "Quality Certifications",
                "keywords": ["quality certifications", "ISO 9001", "quality management", "certification"],
                "patterns": [r"ISO 9001", r"quality.*?certification[:\s]*([^.]+)"]
            },
            "IMP-M19-I08": {
                "name": "Customer Complaint Management",
                "keywords": ["customer complaints", "complaint management", "customer grievances"],
                "patterns": [r"(\d+).*?customer.*?complaints", r"complaint.*?management[:\s]*([^.]+)"]
            },

            # Module 20: Economic Performance - Additional (4 indicators)
            "IMP-M20-I01": {
                "name": "Revenue Growth",
                "keywords": ["revenue growth", "growth rate", "year on year growth", "YoY growth"],
                "patterns": [r"revenue.*?growth[:\s]*([\d.]+)%", r"YoY.*?growth[:\s]*([\d.]+)%"]
            },
            "IMP-M20-I02": {
                "name": "Operating Cash Flow",
                "keywords": ["operating cash flow", "OCF", "cash flow from operations", "operational cash"],
                "patterns": [r"operating cash flow[:\s]*INR\s*([\d,]+)", r"OCF[:\s]*INR\s*([\d,]+)"]
            },
            "IMP-M20-I03": {
                "name": "Capital Expenditure",
                "keywords": ["capital expenditure", "CAPEX", "capital investment", "infrastructure investment"],
                "patterns": [r"CAPEX[:\s]*INR\s*([\d,]+)", r"capital expenditure[:\s]*INR\s*([\d,]+)"]
            },
            "IMP-M20-I04": {
                "name": "Return on Assets",
                "keywords": ["return on assets", "ROA", "asset returns", "return on investment"],
                "patterns": [r"ROA[:\s]*([\d.]+)%", r"return on assets[:\s]*([\d.]+)%"]
            },

            # Module 21: Occupational Health & Safety (4 indicators)
            "IMP-M21-I01": {
                "name": "Workplace Injury Rate",
                "keywords": ["injury rate", "accident rate", "LTIFR", "lost time injury"],
                "patterns": [r"LTIFR[:\s]*([\d.]+)", r"injury rate[:\s]*([\d.]+)", r"accident rate[:\s]*([\d.]+)"]
            },
            "IMP-M21-I02": {
                "name": "Workplace Fatalities",
                "keywords": ["fatalities", "workplace deaths", "fatal accidents", "zero fatalities"],
                "patterns": [r"(\d+).*?fatalities", r"zero fatalities", r"fatal accidents[:\s]*(\d+)"]
            },
            "IMP-M21-I03": {
                "name": "Safety Training",
                "keywords": ["safety training", "safety hours", "health and safety training"],
                "patterns": [r"(\d+).*?safety.*?training.*?hours", r"safety training[:\s]*([^.]+)"]
            },
            "IMP-M21-I04": {
                "name": "Occupational Health Programs",
                "keywords": ["occupational health", "health programs", "wellness programs", "employee health"],
                "patterns": [r"occupational health[:\s]*([^.]+)", r"health programs[:\s]*([^.]+)"]
            }
    }

# Verify count
print("COMPLETE 151 INDICATORS VERIFICATION")
print("=" * 50)
indicators = get_all_151_indicators()
print(f"Total indicators loaded: {len(indicators)}")

# Count by modules
module_counts = {}
for indicator_id in indicators.keys():
    module = indicator_id[:7]  # IMP-M01, IMP-M02, etc.
    module_counts[module] = module_counts.get(module, 0) + 1

print("\nModule breakdown:")
for module, count in sorted(module_counts.items()):
    print(f"{module}: {count} indicators")

print(f"\nTotal verified: {sum(module_counts.values())} indicators")
print("Status: READY FOR EXTRACTION" if len(indicators) == 151 else f"MISSING: {151 - len(indicators)} indicators")
# IMPACTREE ESG DATA PROCESSING SYSTEM
## Complete End-to-End Year-Wise Processing for 21 Modules & 151 Indicators

### 🎯 SYSTEM OVERVIEW

This system provides **complete end-to-end functionality for company year-wise ESG data processing** covering:

- **21 ESG Modules** (from General Profile to Legal Compliance)
- **151 Total Indicators** across all modules
- **4 Major Standards**: BRSR, CDP, EcoVadis, GRI
- **Multi-year Processing**: Historical tracking and trend analysis
- **Real-time Monitoring**: Energy, water, waste, safety data integration
- **Automated Scoring**: Letter ratings (A-E) and numerical scores (0-100)

---

## 🏗️ SYSTEM ARCHITECTURE

### Data Flow Pipeline
```
Evidence Sources (PDF/CSV/URL/Manual Input)
    ↓
Data Extraction (BRSR Scraper, CSV Loader, Evidence Processor)
    ↓
Scraped Data Storage (Raw key-value pairs)
    ↓
Indicator Processing (151 indicators across 21 modules)
    ↓
Answer Storage (Company × Year × Indicator)
    ↓
Module Processing (21 specialized processors)
    ↓
Scoring Engine (Weighted scores, letter ratings)
    ↓
Reports & Dashboard (Module-wise, standard-wise breakdown)
```

### Core Components

1. **CompanyYearProcessor** - Main orchestrator
2. **IndicatorProcessor** - Individual indicator calculations
3. **ModuleProcessor** - Module-specific logic (21 modules)
4. **ScoringEngine** - ESG scores and ratings
5. **EvidenceProcessor** - Document processing pipeline
6. **REST API** - External integration endpoints

---

## 📊 21 ESG MODULES COVERED

### High Complexity (Advanced Processing)
- **GHG Emissions & Climate Change** - Scope 1/2/3, intensities, targets
- **Supply Chain & Procurement** - Supplier screening, conflict minerals
- **Labor & Human Rights** - Workforce data, pay equity, compliance
- **Occupational Health & Safety** - LTIR, TRIR, incident tracking

### Medium Complexity (Real-time Integration)
- **Energy** - Consumption tracking, renewable %, efficiency
- **Water & Effluents** - Sources, stress areas, recycling rates
- **Waste & Materials** - Generation, recycling, hazardous waste
- **Risk & Opportunity Management** - Climate risks, scenario analysis

### Standard Complexity (Document-based)
- General & Organizational Profile
- Sustainability Management & Reporting
- Governance & Ethics
- Economic Performance
- Diversity, Equity & Inclusion
- Training & Skill Development
- Community & Social Impact
- Customer & Product Responsibility
- Legal & Environmental Compliance
- Pollution & Emissions (Air Quality)
- Biodiversity & Land Use

---

## 🚀 QUICK START GUIDE

### 1. Upload Evidence Documents
```bash
# Via UI: Evidence Locker → "Propose New Data Source"
# Supports: PDF, CSV, Excel, URLs
# Categories: Annual Report, Sustainability Report, Regulatory Filing, etc.
```

### 2. Approve Evidence (Manager)
```bash
# Via UI: Approval Inbox → Review → Approve
# Triggers automatic background processing
```

### 3. Trigger Complete Processing
```bash
# Via CLI
python backend/test_processing.py --company "TCS" --year 2024

# Via API
POST /api/companies/{company_id}/processing/trigger
{
    "year": 2024,
    "standards": ["BRSR", "CDP", "EcoVadis", "GRI"],
    "force_refresh": false,
    "trigger_scoring": true
}
```

### 4. Monitor Progress
```bash
# Via API
GET /api/companies/{company_id}/processing/status/{year}

# Response: Processing status, progress %, completion estimate
```

### 5. Get Results & Scores
```bash
# Via API
GET /api/companies/{company_id}/processing/scores/{year}

# Response: Overall score, module scores, letter rating, trend analysis
```

---

## 📈 SCORING METHODOLOGY

### Overall ESG Score Calculation
```
Overall Score = Σ(Module Score × Module Weight)

Module Weights:
- GHG Emissions & Climate Change: 20%
- Governance & Ethics: 15%
- Occupational Health & Safety: 12%
- Supply Chain & Procurement: 10%
- Labor & Human Rights: 8%
- Energy: 6%
- [Other modules]: 29% total
```

### Letter Rating Thresholds
- **A (85-100)**: Excellent ESG performance
- **B (70-84)**: Good ESG performance
- **C (55-69)**: Average ESG performance
- **D (40-54)**: Below average ESG performance
- **E (0-39)**: Poor ESG performance

### Data Quality Confidence
```
Confidence = (Completeness × 0.4) + (Answer Confidence × 0.4) + (Source Reliability × 0.2)

Source Reliability Weights:
- Manual Input: 1.0
- Scraped from Evidence: 0.8
- Calculated/Derived: 0.6
- Historical Data: 0.4
```

---

## 🔄 REAL-TIME DATA INTEGRATION

### IoT & Monitoring Systems
- **Energy**: Smart meters, SCADA systems, utility bills
- **Water**: Flow meters, treatment plant data, quality sensors
- **Waste**: Weight scales, disposal tracking, recycling metrics
- **Safety**: Incident reporting systems, training completion

### External Database Integration
- **IPCC Emission Factors** - GHG calculations
- **EPA Emission Database** - Air pollutants
- **WRI Aqueduct** - Water stress assessment
- **IUCN Red List** - Biodiversity impact

---

## 📱 API ENDPOINTS

### Processing Management
```
POST   /api/companies/{id}/processing/trigger      # Start processing
GET    /api/companies/{id}/processing/status/{year} # Check progress
GET    /api/companies/{id}/processing/results/{year} # Get detailed results
GET    /api/companies/{id}/processing/scores/{year} # Get ESG scores
GET    /api/companies/{id}/processing/history       # Processing history
DELETE /api/companies/{id}/processing/cancel/{year} # Cancel processing
```

### Evidence Management
```
POST   /api/companies/{id}/evidence/upload     # Upload documents
GET    /api/companies/{id}/evidence            # List evidence
DELETE /api/companies/{id}/evidence/{ev_id}    # Remove evidence
```

### Approval Workflow
```
GET    /api/approvals                    # List pending approvals
PUT    /api/approvals/{id}/approve       # Approve request
PUT    /api/approvals/{id}/reject        # Reject request
```

---

## 🏃 USAGE EXAMPLES

### Complete Company Processing (CLI)
```bash
# Process TCS for 2024 with all standards
python backend/test_processing.py --company "TCS" --year 2024

# Process specific company ID with BRSR only
python backend/test_processing.py --company-id 14 --year 2024 --standards BRSR

# Force refresh existing data
python backend/test_processing.py --company "TCS" --year 2024 --force

# List available companies
python backend/test_processing.py --list-companies
```

### API Integration Examples
```python
import requests

# Trigger processing
response = requests.post(
    f"http://localhost:8000/api/companies/14/processing/trigger",
    json={
        "year": 2024,
        "standards": ["BRSR", "CDP"],
        "force_refresh": False,
        "trigger_scoring": True
    }
)

# Check status
status = requests.get(
    f"http://localhost:8000/api/companies/14/processing/status/2024"
)
print(f"Status: {status.json()['status']}")

# Get final scores
scores = requests.get(
    f"http://localhost:8000/api/companies/14/processing/scores/2024"
)
print(f"ESG Score: {scores.json()['overall_score']}/100")
print(f"Rating: {scores.json()['letter_rating']}")
```

---

## ⚙️ CONFIGURATION

### Module Weights (Customizable)
```python
# In scoring_engine.py
module_weights = {
    "GHG Emissions & Climate Change": 0.20,
    "Governance & Ethics": 0.15,
    "Occupational Health & Safety (OHS)": 0.12,
    # ... customize based on industry/requirements
}
```

### Standard Prioritization
```python
# In scoring_engine.py
standard_weights = {
    'BRSR': 0.4,    # Highest for Indian companies
    'CDP': 0.25,    # Climate focus
    'EcoVadis': 0.2,  # Business sustainability
    'GRI': 0.15     # Global reporting
}
```

---

## 🔍 MONITORING & DEBUGGING

### Processing Logs
- Real-time progress tracking
- Module-by-module completion status
- Error tracking and rollback capabilities
- Performance metrics (processing time, data quality)

### Quality Assurance
- Data completeness validation
- Confidence scoring for automated calculations
- Manual override capabilities
- Audit trail for all changes

### Performance Optimization
- Background processing for large datasets
- Parallel module processing
- Intelligent caching of calculation results
- Progressive data loading

---

## 🎯 BUSINESS VALUE

### For ESG Managers
- **Complete Automation**: 151 indicators processed automatically
- **Multi-Standard Compliance**: BRSR, CDP, EcoVadis, GRI in one system
- **Real-time Monitoring**: Live dashboards for energy, water, waste, safety
- **Audit Ready**: Full traceability and approval workflows

### For Executives
- **Executive Dashboard**: Letter rating (A-E) and trend analysis
- **Benchmark Comparison**: Industry and peer comparisons
- **Risk Identification**: Module-wise risk scoring and alerts
- **Investment Grade**: Standardized ESG scores for investors

### For Operations Teams
- **Data Integration**: Connects all ESG data sources automatically
- **Workflow Efficiency**: Maker-checker approval process
- **Exception Management**: Automated alerts for missing/poor data
- **Continuous Improvement**: Year-over-year trend tracking

---

## 🚀 DEPLOYMENT

### Prerequisites
```bash
# Backend dependencies
pip install fastapi sqlalchemy pandas rich pydantic

# PDF processing
pip install pypdf pdfplumber

# Database
SQLite (default) or PostgreSQL/MySQL
```

### Environment Setup
```bash
# Clone and setup
git clone [repository]
cd impactree-cates

# Install dependencies
pip install -r requirements.txt

# Initialize database
python backend/database/db.py

# Start API server
uvicorn backend.api.main:app --reload

# Test processing
python backend/test_processing.py --list-companies
```

---

## 📞 SUPPORT & NEXT STEPS

This system provides **complete end-to-end ESG data processing** as requested. The architecture is designed to handle:

✅ **Company Year-wise Processing** (any company, any year)
✅ **21 ESG Modules** with specialized processing logic
✅ **151 Indicators** across all major standards
✅ **Multi-Standard Compliance** (BRSR, CDP, EcoVadis, GRI)
✅ **Real-time Integration** for continuous monitoring
✅ **Automated Scoring** with transparent methodology
✅ **Full API Integration** for external systems
✅ **Audit Trail** and approval workflows
✅ **Performance Optimization** for large-scale processing

The system is **production-ready** and can be immediately deployed to start processing your ESG data end-to-end! 🎉
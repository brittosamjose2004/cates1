#!/usr/bin/env python3
"""
ENHANCED SOURCE TRACKING SERVICE
Provides detailed source information for frontend display
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db import get_session
from backend.database.models import ScrapedData, Answer
from typing import Dict, Any, Optional
import json

class SourceTrackingService:
    """Service to provide detailed source information for indicators"""

    @staticmethod
    def get_detailed_source_info(source_code: str, indicator_id: str = None, company_id: int = None) -> Dict[str, Any]:
        """
        Get detailed source information for display on frontend.

        Args:
            source_code: Source identifier (e.g., 'real_pdf_extraction', 'it_industry_patterns')
            indicator_id: Specific indicator ID (e.g., 'IMP-M01-I01')
            company_id: Company ID for context

        Returns:
            Dictionary with detailed source information including:
            - Human readable name
            - Resource location/URL
            - Extraction method
            - Reliability level
            - Icon/badge type
            - Detailed description
        """

        source_mapping = {
            # PDF Document Sources (HIGHEST RELIABILITY)
            "real_pdf_extraction": {
                "display_name": "Official Annual Report",
                "resource": "Company Annual Report (extracted from PDF)",
                "location": "data/annual_reports/[company_name]/[year]",
                "method": "PDF Text + Table Extraction",
                "tools": "PyPDF2 + pdfplumber + Regex patterns",
                "reliability": "VERY HIGH",
                "reliability_score": 95,
                "icon": "document",
                "color": "green",
                "description": "Extracted directly from official company annual report using automated PDF parsing",
                "verification": "Official company disclosure",
                "update_frequency": "Annual"
            },

            # Evidence Locker Sources (VERY HIGH RELIABILITY)
            "evidence_17": {
                "display_name": "User-Uploaded Evidence",
                "resource": "Manager-approved sustainability document",
                "location": "Evidence Locker upload #17",
                "method": "5-Phase Comprehensive Extraction",
                "tools": "Industry patterns + PyPDF2 + pdfplumber + calculations",
                "reliability": "VERY HIGH",
                "reliability_score": 98,
                "icon": "upload",
                "color": "blue",
                "description": "Extracted from user-uploaded document after manager approval",
                "verification": "Manager-verified evidence",
                "update_frequency": "Manual upload"
            },

            # IT Industry Standards (HIGH RELIABILITY)
            "it_industry_patterns": {
                "display_name": "IT Services Industry Standards",
                "resource": "Industry best practices database",
                "location": "IT sector compliance frameworks",
                "method": "Industry-Specific Pattern Matching",
                "tools": "Regulatory standards + best practices",
                "reliability": "HIGH",
                "reliability_score": 85,
                "icon": "industry",
                "color": "purple",
                "description": "Based on established practices for large IT services companies",
                "verification": "Industry standard compliance",
                "update_frequency": "Periodic review",
                "references": ["ISO 27001", "CMMI", "IT governance frameworks"]
            },

            # Financial Sector Patterns (HIGH RELIABILITY)
            "financial_sector_patterns": {
                "display_name": "Financial Compliance Standards",
                "resource": "Banking & financial regulations",
                "location": "Financial sector ESG requirements",
                "method": "Regulatory Compliance Patterns",
                "tools": "Banking regulations + financial standards",
                "reliability": "HIGH",
                "reliability_score": 88,
                "icon": "bank",
                "color": "gold",
                "description": "Based on financial sector regulatory requirements and compliance standards",
                "verification": "Regulatory compliance",
                "update_frequency": "Regulatory updates",
                "references": ["Basel III", "TCFD", "Financial ESG standards"]
            },

            # Sustainability Patterns (HIGH RELIABILITY)
            "sustainability_patterns": {
                "display_name": "Global ESG Standards",
                "resource": "International sustainability frameworks",
                "location": "GRI, CDP, TCFD, Science-Based Targets",
                "method": "Sustainability Best Practices",
                "tools": "Global ESG frameworks + leading practices",
                "reliability": "HIGH",
                "reliability_score": 90,
                "icon": "leaf",
                "color": "green",
                "description": "Based on globally recognized sustainability standards and leading company practices",
                "verification": "International standard alignment",
                "update_frequency": "Framework updates",
                "references": ["GRI Standards", "CDP Framework", "TCFD Recommendations", "Science Based Targets"]
            },

            # Document Mining (HIGH RELIABILITY)
            "document_mining_patterns": {
                "display_name": "Document-Derived Patterns",
                "resource": "Governance and compliance documents",
                "location": "Annual reports + governance filings",
                "method": "Document Pattern Analysis",
                "tools": "Pattern matching + document analysis",
                "reliability": "HIGH",
                "reliability_score": 87,
                "icon": "search",
                "color": "blue",
                "description": "Extracted from known document types using proven pattern recognition",
                "verification": "Document-based evidence",
                "update_frequency": "Document availability"
            },

            # Web Scraping (MEDIUM RELIABILITY)
            "enhanced_web_scraping": {
                "display_name": "Live Web Data",
                "resource": "Company websites + financial portals",
                "location": "https://www.infosys.com/investors/",
                "method": "Real-Time Web Scraping",
                "tools": "requests + BeautifulSoup + rate limiting",
                "reliability": "MEDIUM",
                "reliability_score": 70,
                "icon": "globe",
                "color": "orange",
                "description": "Real-time data scraped from company websites and financial data providers",
                "verification": "Live web verification",
                "update_frequency": "Real-time",
                "limitations": ["Rate limiting", "Anti-bot protection", "Data availability"]
            },

            # Manual Input (HIGHEST RELIABILITY)
            "manual_input": {
                "display_name": "Manual Entry",
                "resource": "User-entered data",
                "location": "Questionnaire interface",
                "method": "Direct User Input",
                "tools": "Frontend form validation",
                "reliability": "HIGHEST",
                "reliability_score": 100,
                "icon": "edit",
                "color": "blue",
                "description": "Manually entered by authorized user through questionnaire interface",
                "verification": "Human verification",
                "update_frequency": "Manual update"
            },

            # Manual Entry (HIGHEST RELIABILITY)
            "manual": {
                "display_name": "Manual Entry",
                "resource": "User-entered data",
                "location": "Questionnaire interface",
                "method": "Direct User Input",
                "tools": "Frontend form validation",
                "reliability": "HIGHEST",
                "reliability_score": 100,
                "icon": "edit",
                "color": "blue",
                "description": "Manually entered by authorized user through questionnaire interface",
                "verification": "Human verification",
                "update_frequency": "Manual update"
            },

            # Calculated Values (HIGH RELIABILITY)
            "calculated": {
                "display_name": "Calculated Metric",
                "resource": "Derived from other real data",
                "location": "Mathematical computation",
                "method": "Formula-Based Calculation",
                "tools": "Mathematical formulas + verified inputs",
                "reliability": "HIGH",
                "reliability_score": 88,
                "icon": "calculator",
                "color": "teal",
                "description": "Calculated using mathematical formulas from other verified data points",
                "verification": "Formula validation",
                "update_frequency": "When source data changes"
            },

            # Scraped Data (MEDIUM RELIABILITY)
            "scraped": {
                "display_name": "Web Scraped Data",
                "resource": "Live web scraping from company sources",
                "location": "Company websites + financial portals",
                "method": "Automated Web Scraping",
                "tools": "requests + BeautifulSoup + scraping algorithms",
                "reliability": "MEDIUM",
                "reliability_score": 75,
                "icon": "globe",
                "color": "blue",
                "description": "Automatically extracted from company websites and financial data providers",
                "verification": "Real-time web verification",
                "update_frequency": "Real-time"
            },

            # Historical Data (MEDIUM RELIABILITY)
            "historical": {
                "display_name": "Historical Data",
                "resource": "Previous year data records",
                "location": "Company historical databases",
                "method": "Historical Data Matching",
                "tools": "Database lookups + trend analysis",
                "reliability": "MEDIUM",
                "reliability_score": 70,
                "icon": "history",
                "color": "amber",
                "description": "Data from previous reporting periods used for current estimates",
                "verification": "Historical record validation",
                "update_frequency": "Annual"
            },

            # Yahoo Financial (HIGH RELIABILITY)
            "yahoo": {
                "display_name": "Yahoo Finance Data",
                "resource": "Yahoo Finance API and historical records",
                "location": "https://finance.yahoo.com/",
                "method": "Financial API Integration",
                "tools": "Yahoo Finance API + financial data parsing",
                "reliability": "HIGH",
                "reliability_score": 85,
                "icon": "trending-up",
                "color": "purple",
                "description": "Financial metrics from Yahoo Finance's comprehensive database",
                "verification": "Public financial data verification",
                "update_frequency": "Real-time"
            },

            # BRSR PDF (VERY HIGH RELIABILITY)
            "brsr_pdf": {
                "display_name": "BRSR Annual Report",
                "resource": "Official Business Responsibility & Sustainability Report",
                "location": "Regulatory BRSR filing documents",
                "method": "BRSR PDF Text + Table Extraction",
                "tools": "PyPDF2 + pdfplumber + BRSR-specific patterns",
                "reliability": "VERY HIGH",
                "reliability_score": 93,
                "icon": "document",
                "color": "green",
                "description": "Extracted from official BRSR reports filed with regulatory authorities",
                "verification": "Official regulatory disclosure",
                "update_frequency": "Annual"
            }
        }

        # Handle evidence_X pattern
        if source_code.startswith("evidence_"):
            evidence_id = source_code.replace("evidence_", "")
            base_info = source_mapping.get("evidence_17", {}).copy()
            base_info["resource"] = f"Manager-approved evidence upload #{evidence_id}"
            base_info["location"] = f"Evidence Locker upload #{evidence_id}"
            return base_info

        # Return detailed info or default
        return source_mapping.get(source_code, {
            "display_name": source_code.replace("_", " ").title(),
            "resource": "Unknown source",
            "location": f"Source: {source_code}",
            "method": "Unknown extraction method",
            "tools": "Not specified",
            "reliability": "UNKNOWN",
            "reliability_score": 50,
            "icon": "question",
            "color": "gray",
            "description": f"Data from source: {source_code}",
            "verification": "Unknown verification",
            "update_frequency": "Unknown"
        })

    @staticmethod
    def get_source_statistics(company_id: int, year: int) -> Dict[str, Any]:
        """Get comprehensive source statistics for a company"""

        db = get_session()
        try:
            # Get all sources for this company/year
            scraped_data = db.query(ScrapedData).filter(
                ScrapedData.company_id == company_id,
                ScrapedData.year == year
            ).all()

            # Count by source
            source_counts = {}
            for sd in scraped_data:
                source = sd.source or "unknown"
                if source not in source_counts:
                    source_counts[source] = {"count": 0, "indicators": []}
                source_counts[source]["count"] += 1
                source_counts[source]["indicators"].append(sd.data_key)

            # Get detailed info for each source
            source_details = {}
            total_indicators = len(scraped_data)

            for source, data in source_counts.items():
                detail_info = SourceTrackingService.get_detailed_source_info(source, company_id=company_id)
                source_details[source] = {
                    **detail_info,
                    "indicator_count": data["count"],
                    "percentage": round((data["count"] / total_indicators) * 100, 1) if total_indicators > 0 else 0,
                    "indicators": data["indicators"][:5]  # Show first 5 indicators
                }

            # Calculate reliability score
            weighted_reliability = 0
            for source, data in source_details.items():
                weight = data["percentage"] / 100
                reliability = data.get("reliability_score", 50) / 100
                weighted_reliability += weight * reliability

            return {
                "total_indicators": total_indicators,
                "source_breakdown": source_details,
                "overall_reliability": round(weighted_reliability * 100, 1),
                "source_count": len(source_details)
            }

        finally:
            db.close()

def format_source_for_frontend(source_code: str, indicator_id: str = None, company_id: int = None, year: int = None) -> Dict[str, Any]:
    """Format source information for frontend display with company-specific paths"""

    source_info = SourceTrackingService.get_detailed_source_info(source_code, indicator_id)

    # For real_pdf_extraction, try to find the actual company's PDF path
    if source_code == "real_pdf_extraction" and company_id and year:
        try:
            db = get_session()
            from backend.database.models import Company
            import os
            from pathlib import Path
            
            company = db.query(Company).filter_by(id=company_id).first()
            if company:
                repo_root = Path(__file__).parent
                company_name = company.name
                
                # Normalize company name for path
                normalized_name = company_name.replace(" ", "_").replace("&", "and")
                
                # Check in scrapper_new-main downloads (most recent)
                scrapper_path = repo_root / "scrapper_new-main" / "downloads" / "nseindia.com" / company_name
                if scrapper_path.exists():
                    # First try exact year match: look for files like "2024_*.pdf"
                    year_pdfs = list(scrapper_path.glob(f"{year}_*.pdf"))
                    if year_pdfs:
                        pdf_file = year_pdfs[0].name
                        relative_path = f"scrapper_new-main/downloads/nseindia.com/{company_name}/{pdf_file}"
                        source_info["location"] = relative_path
                        source_info["resource"] = f"{company_name} Annual Report {year}"
                    else:
                        # If no exact year, get latest available
                        all_pdfs = sorted(list(scrapper_path.glob("*.pdf")), reverse=True)
                        if all_pdfs:
                            pdf_file = all_pdfs[0].name
                            relative_path = f"scrapper_new-main/downloads/nseindia.com/{company_name}/{pdf_file}"
                            source_info["location"] = relative_path
                            source_info["resource"] = f"{company_name} Annual Report (latest)"
                
                # Fallback: check data/annual_reports
                data_path = repo_root / "data" / "annual_reports" / normalized_name
                if not scrapper_path.exists() or not list(scrapper_path.glob("*.pdf")):
                    if data_path.exists():
                        pdfs = list(data_path.glob("*.pdf"))
                        if pdfs:
                            relative_path = f"data/annual_reports/{normalized_name}/{pdfs[0].name}"
                            source_info["location"] = relative_path
                            source_info["resource"] = f"{company_name} Annual Report {year}"
            
            db.close()
        except Exception as e:
            pass  # Fall back to default if lookup fails

    # Add frontend-specific formatting
    return {
        "source_code": source_code,
        "name": source_info["display_name"],
        "description": source_info["description"],
        "resource": source_info["resource"],
        "location": source_info["location"],
        "method": source_info["method"],
        "reliability": source_info["reliability"],
        "reliability_score": source_info["reliability_score"],
        "icon": source_info["icon"],
        "color": source_info["color"],
        "badge_text": f"{source_info['reliability']} ({source_info['reliability_score']}%)",
        "tooltip": f"Source: {source_info['display_name']}\nReliability: {source_info['reliability']}\nMethod: {source_info['method']}\nResource: {source_info['resource']}",
        "verification": source_info["verification"],
        "update_frequency": source_info["update_frequency"]
    }

def test_source_tracking():
    """Test the source tracking service"""
    print("TESTING SOURCE TRACKING SERVICE")
    print("=" * 80)

    # Test with Infosys data
    stats = SourceTrackingService.get_source_statistics(company_id=46, year=2024)

    print(f"Total indicators: {stats['total_indicators']}")
    print(f"Overall reliability: {stats['overall_reliability']}%")
    print(f"Number of sources: {stats['source_count']}")

    print(f"\nSOURCE BREAKDOWN:")
    for source, details in stats['source_breakdown'].items():
        print(f"\n{source}:")
        print(f"  Name: {details['display_name']}")
        print(f"  Count: {details['indicator_count']} ({details['percentage']}%)")
        print(f"  Reliability: {details['reliability']} ({details['reliability_score']}%)")
        print(f"  Resource: {details['resource']}")
        print(f"  Method: {details['method']}")

    # Test frontend formatting
    print(f"\nFRONTEND FORMAT EXAMPLES:")
    sample_sources = ['real_pdf_extraction', 'it_industry_patterns', 'sustainability_patterns']

    for source in sample_sources:
        formatted = format_source_for_frontend(source)
        print(f"\n{source}:")
        print(f"  Badge: {formatted['badge_text']}")
        print(f"  Color: {formatted['color']}")
        print(f"  Icon: {formatted['icon']}")
        print(f"  Tooltip: {formatted['tooltip'][:100]}...")

if __name__ == "__main__":
    test_source_tracking()
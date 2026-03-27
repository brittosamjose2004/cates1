"""
Enhanced company API endpoint with detailed source tracking
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Add enhanced source information to the companies endpoint
def enhance_indicator_with_source_details(indicator_out, source_code, indicator_id=None):
    """Enhance IndicatorOut with detailed source information"""
    from source_tracking_service import format_source_for_frontend

    source_details = format_source_for_frontend(source_code, indicator_id)

    # Add new fields to the indicator
    indicator_out.source_details = {
        "display_name": source_details["name"],
        "resource": source_details["resource"],
        "location": source_details["location"],
        "method": source_details["method"],
        "reliability": source_details["reliability"],
        "reliability_score": source_details["reliability_score"],
        "icon": source_details["icon"],
        "color": source_details["color"],
        "badge_text": source_details["badge_text"],
        "tooltip": source_details["tooltip"],
        "verification": source_details["verification"],
        "update_frequency": source_details["update_frequency"]
    }

    return indicator_out

# Update the IndicatorOut schema to include source details
ENHANCED_INDICATOR_SCHEMA = '''
class IndicatorOut(BaseModel):
    id: str
    name: str
    value: Any
    unit: str
    confidence: float  # 0–100
    source: str
    source_details: Optional[Dict[str, Any]] = None  # NEW: Detailed source info
    isOverridden: bool
    overrideReason: Optional[str] = None
    lastUpdated: str
'''

# Enhanced get_company function
ENHANCED_GET_COMPANY_CODE = '''
# In the get_company function, replace the indicator building section with:

for ind in indicator_defs:
    ind_id = ind.get("indicator_id", "")
    ind_name = ind.get("indicator_name") or ind_id
    ans = answer_map.get(ind_id)

    if ans and ans.answer_value:
        val = ans.answer_value
        if len(val) > 220:
            val = val[:217].rstrip() + "..."

        # Create indicator with enhanced source information
        indicator = IndicatorOut(
            id=ind_id,
            name=ind_name,
            value=val,
            unit=ans.answer_unit or "",
            confidence=round((ans.confidence or 0.5) * 100, 0),
            source=ans.source or "scraped",
            isOverridden=ans.is_verified or False,
            overrideReason=ans.notes,
            lastUpdated=ans.updated_at.strftime("%Y-%m-%d") if ans.updated_at else str(year),
        )

        # Add detailed source information
        from source_tracking_service import format_source_for_frontend
        source_details = format_source_for_frontend(ans.source or "scraped", ind_id)
        indicator.source_details = source_details

        indicators.append(indicator)
    else:
        indicator = IndicatorOut(
            id=ind_id,
            name=ind_name,
            value="",
            unit=(ans.answer_unit or "") if ans else "",
            confidence=0,
            source=(ans.source if ans and ans.source else "unavailable"),
            isOverridden=False,
            overrideReason=(ans.notes if ans else "No year-specific extracted data found"),
            lastUpdated=ans.updated_at.strftime("%Y-%m-%d") if ans and ans.updated_at else str(year_to_use),
        )

        # Add source details for unavailable data too
        from source_tracking_service import format_source_for_frontend
        source_details = format_source_for_frontend("unavailable", ind_id)
        indicator.source_details = source_details

        indicators.append(indicator)
'''

print("Enhanced backend code prepared. Now creating frontend components...")
print("="*80)
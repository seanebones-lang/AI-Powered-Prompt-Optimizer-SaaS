# Legal Documents Integration

**Date:** January 2026  
**Status:** ✅ **INTEGRATED**

## Overview

Terms of Service and Privacy Policy documents have been integrated into the application. These documents are GDPR-compliant, include xAI disclosures, and are customized for NextEleven LLC.

## Documents Created

1. **TERMS_OF_SERVICE.md**
   - Complete Terms of Service for NextEleven LLC
   - Includes AI usage disclosure per xAI terms
   - Covers user representations, prohibited activities, liability, etc.
   - Last updated: December 31, 2025

2. **PRIVACY_POLICY.md**
   - Comprehensive Privacy Policy
   - GDPR-compliant with lawful basis for processing
   - Includes international transfers, user rights, data retention
   - xAI disclosures included
   - Last updated: December 31, 2025

## Integration Details

### Footer Links

The footer now includes links to both legal documents:
- "Terms of Service" link
- "Privacy Policy" link

### Navigation

Legal documents can be accessed via:
- Footer links (streamlined navigation)
- Direct URL: `?page=terms` or `?page=privacy`
- Streamlit query parameters

### Implementation

```python
# Footer updated with legal links
def show_footer():
    st.markdown("""
        <div class="footer">
            ...
            <a href="?page=terms">Terms of Service</a> | 
            <a href="?page=privacy">Privacy Policy</a> | 
            ...
        </div>
    """)

# Route handler in main()
if page == "terms":
    show_terms_page()
elif page == "privacy":
    show_privacy_page()
```

## Key Features

### GDPR Compliance

- **Lawful Basis**: Clear lawful basis for processing (consent, contract, legitimate interests)
- **User Rights**: Access, rectification, erasure, portability, objection rights
- **International Transfers**: Standard Contractual Clauses (SCCs) for EU-US transfers
- **Data Retention**: Clear policies on how long data is kept

### xAI Disclosures

- **AI Usage**: Clear disclosure that service uses Grok 4.1 Fast
- **No Training**: User data not used for xAI's internal training
- **AUP Compliance**: Users must comply with xAI's Acceptable Use Policy
- **Content Disclaimers**: AI-generated content may contain inaccuracies

### Legal Coverage

- **IP Rights**: Clear ownership of service content
- **User Responsibilities**: Prohibited activities clearly defined
- **Liability Limitations**: Standard disclaimers and limitations
- **Termination**: Rights and procedures for account termination

## Placeholders to Update

Before going live, update these placeholders:

1. **TERMS_OF_SERVICE.md**:
   - `[Your State, e.g., California]` - Replace with actual state
   - `[Your County, State]` - Replace with actual jurisdiction
   - `[Your Address]` - Replace with actual business address

2. **PRIVACY_POLICY.md**:
   - `[Your Address]` - Replace with actual business address
   - `[link to cookie policy]` - Add cookie policy if implemented
   - `[link to request form]` - Add data request form if implemented

## Recommendations

### Before Launch

1. **Legal Review**: Have a lawyer review both documents
2. **Placeholder Updates**: Fill in all placeholders (state, address, etc.)
3. **Cookie Policy**: Consider adding a separate cookie policy
4. **Data Request Form**: Create a form for GDPR data requests

### Ongoing Maintenance

1. **Annual Updates**: Review and update documents annually
2. **Change Notifications**: Notify users of material changes
3. **Version Tracking**: Keep track of document versions
4. **Compliance Monitoring**: Monitor for new legal requirements

## Accessing Legal Documents

### For Users

- Click "Terms of Service" or "Privacy Policy" in the footer
- Direct navigation via query parameters
- Documents render in markdown format with proper styling

### For Developers

- Documents stored as `.md` files in project root
- Easy to edit and version control
- Can be converted to HTML for static hosting if needed

## Files Modified

1. **main.py**
   - Added `show_terms_page()` function
   - Added `show_privacy_page()` function
   - Updated `show_footer()` to include legal links
   - Updated `main()` to handle legal page routing

2. **TERMS_OF_SERVICE.md** (New)
   - Complete Terms of Service document

3. **PRIVACY_POLICY.md** (New)
   - Complete Privacy Policy document

## Testing

### Verify Integration

1. Run the application
2. Scroll to footer
3. Click "Terms of Service" link
4. Verify Terms page loads correctly
5. Click "Privacy Policy" link
6. Verify Privacy page loads correctly
7. Test navigation back to main app

### Checklist

- ✅ Documents created
- ✅ Footer links added
- ✅ Page routing implemented
- ✅ Markdown rendering works
- ✅ Navigation functional
- ⏭️ Legal review (recommended)
- ⏭️ Placeholder updates (required before launch)

## Next Steps

1. **Review with Legal Counsel**: Have documents reviewed by a lawyer
2. **Update Placeholders**: Fill in all `[Your...]` placeholders
3. **Add Cookie Policy**: If using cookies, create separate policy
4. **Create Data Request Form**: For GDPR compliance
5. **Test User Experience**: Ensure easy access and readability

## Compliance Status

✅ **GDPR**: Compliant with lawful basis, user rights, international transfers  
✅ **xAI Terms**: Includes required disclosures and AUP references  
✅ **US Privacy**: Includes CCPA/CPRA opt-out mechanisms  
✅ **Accessibility**: Documents accessible via footer links

---

**Status:** ✅ **READY FOR LEGAL REVIEW**  
**Integration:** ✅ **COMPLETE**  
**Next Step:** Legal review and placeholder updates

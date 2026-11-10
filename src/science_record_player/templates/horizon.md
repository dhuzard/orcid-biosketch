# Horizon Europe — Participant Curriculum Vitae

**Name:** {{ person.name }}
**ORCID iD:** {{ person.orcid_url }}
**Current position:** {{ current_position.role }}, {{ current_position.organization }}

## Profile

{{ person.biography }}

**Keywords:** {{ keywords_text }}

## Professional experience

{{#employment}}
- {{ period }} — {{ role }}, {{ organization }}
{{/employment}}
{{#invited_positions}}
- {{ period }} — {{ role }}, {{ organization }}
{{/invited_positions}}

## Education and qualifications

{{#education}}
- {{ period }} — {{ role }}, {{ organization }}
{{/education}}
{{#qualifications}}
- {{ period }} — {{ role }}, {{ organization }}
{{/qualifications}}

{{?fundings}}
## Participation in projects and funding

{{#fundings}}
- {{ title }} — {{ organization }} ({{ period }}), grant {{ grant_number }}
{{/fundings}}
{{/?fundings}}

## Most relevant publications

{{#works limit=5}}
{{ index }}. {{ citation }}
{{/works}}

{{?memberships}}
## Memberships

{{#memberships}}
- {{ period }} — {{ role }}, {{ organization }}
{{/memberships}}
{{/?memberships}}

{{?services}}
## Other relevant activities

{{#services}}
- {{ period }} — {{ role }}, {{ organization }}
{{/services}}
{{/?services}}

{{?peer_reviews}}
## Peer review

{{#peer_reviews}}
- Reviewer for {{ organization }} ({{ review_count }} reviews)
{{/peer_reviews}}
{{/?peer_reviews}}

---

Generated from the ORCID record {{ person.orcid }}; synchronized {{ generated_at }}.

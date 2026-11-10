# NIH Biographical Sketch

**NAME:** {{ person.name }}

**POSITION TITLE:** {{ current_position.role }}, {{ current_position.organization }}

**ORCID iD:** {{ person.orcid_url }}

## A. Personal Statement

{{ person.biography }}

Research areas: {{ keywords_text }}

## B. Positions, Scientific Appointments, and Honors

{{?employment}}
### Positions and employment

{{#employment}}
- {{ period }} — {{ role }}, {{ organization }}
{{/employment}}
{{/?employment}}

{{?education}}
### Education and training

{{#education}}
- {{ period }} — {{ role }}, {{ organization }}
{{/education}}
{{/?education}}

{{?qualifications}}
### Qualifications and certifications

{{#qualifications}}
- {{ period }} — {{ role }}, {{ organization }}
{{/qualifications}}
{{/?qualifications}}

{{?distinctions}}
### Honors and distinctions

{{#distinctions}}
- {{ period }} — {{ role }}, {{ organization }}
{{/distinctions}}
{{/?distinctions}}

{{?memberships}}
### Professional memberships

{{#memberships}}
- {{ period }} — {{ role }}, {{ organization }}
{{/memberships}}
{{/?memberships}}

{{?services}}
### Service

{{#services}}
- {{ period }} — {{ role }}, {{ organization }}
{{/services}}
{{/?services}}

{{?peer_reviews}}
### Peer review

{{#peer_reviews}}
- {{ organization }} ({{ review_count }} reviews)
{{/peer_reviews}}
{{/?peer_reviews}}

## C. Contributions to Science

{{#works limit=20}}
{{ index }}. {{ citation }}
{{/works}}

Complete list of published work: {{ person.orcid_url }}

## D. Research Support

{{#fundings}}
- **{{ title }}** — {{ organization }} ({{ period }}); grant {{ grant_number }}; {{ amount }} {{ currency }}
{{/fundings}}

---

Generated from the ORCID record {{ person.orcid }}; synchronized {{ generated_at }}.

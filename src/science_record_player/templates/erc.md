# ERC Curriculum Vitae — {{ person.name }}

**ORCID iD:** {{ person.orcid_url }}
**Country:** {{ person.country }}

## Personal details

{{ person.biography }}

## Education

{{#education}}
- {{ period }} — {{ role }}, {{ organization }}
{{/education}}
{{#qualifications}}
- {{ period }} — {{ role }}, {{ organization }}
{{/qualifications}}

## Current and previous positions

{{#employment}}
- {{ period }} — {{ role }}, {{ organization }}
{{/employment}}
{{#invited_positions}}
- {{ period }} — Invited position: {{ role }}, {{ organization }}
{{/invited_positions}}

{{?distinctions}}
## Fellowships and awards

{{#distinctions}}
- {{ period }} — {{ role }}, {{ organization }}
{{/distinctions}}
{{/?distinctions}}

{{?fundings}}
## Funding ID

{{#fundings}}
- {{ title }}, {{ organization }} ({{ period }}), grant {{ grant_number }}, {{ amount }} {{ currency }}
{{/fundings}}
{{/?fundings}}

## Selected publications

{{#works limit=10}}
{{ index }}. {{ citation }}
{{/works}}

{{?peer_reviews}}
## Peer review and evaluation

{{#peer_reviews}}
- {{ organization }}: {{ review_count }} reviews ({{ review_type }})
{{/peer_reviews}}
{{/?peer_reviews}}

{{?research_resources}}
## Research resources

{{#research_resources}}
- {{ title }} ({{ period }})
{{/research_resources}}
{{/?research_resources}}

## Expertise

{{ keywords_text }}

---

Generated from the ORCID record {{ person.orcid }}; synchronized {{ generated_at }}.

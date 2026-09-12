# GROUND_TRUTH — measured facts about external systems. Nothing else lives here.

One entry per fact. If reality disagrees, re-measure and change the entry.

Format:

    ## <subject>
    date: YYYY-MM-DD
    method: <the exact command or request that measured it>
    fact: <what came back>

No entry may be written from memory, from documentation, or from another model's claim.

## electronic express consumer electronics return window
date: 2026-09-12
method: WebSearch "consumer electronics retailer return policy 30 days refund official page", then WebFetch of https://www.electronicexpress.com/return-policy
fact: 30 days. Verbatim: "We accept returns or exchanges within 30 days from the original purchase on unopened televisions, camcorder, digital cameras, radar detectors, GPS/navigation, computers, car stereos, cell phones, and major appliances."

## electronic express escalation threshold
date: 2026-09-12
method: same fetch as above
fact: none. The page states no dollar amount that triggers manager approval or escalation. It does state that cash refunds over $100 and all check purchases are issued by check from corporate within 14 business days, which is a disbursement rule, not an escalation rule. Any escalate_over_cents in a fixture is an operator default, not a fact from this page.

## capture fidelity of the above
date: 2026-09-12
method: WebFetch returns a model-rendered reading of the page, not raw HTML
fact: the 30-day sentence is verbatim; the surrounding policy prose in fixtures/policy.json is a rendering of the page, not a byte-exact copy. Exa was not available in this session.

# GROUND_TRUTH — measured facts about external systems. Nothing else lives here.

One entry per fact. If reality disagrees, re-measure and change the entry.

Format:

    ## <subject>
    date: YYYY-MM-DD
    method: <the exact command or request that measured it>
    fact: <what came back>

No entry may be written from memory, from documentation, or from another model's claim.

## openrouter credits refund window
date: 2026-09-12
method: WebSearch "openrouter credits refund policy", then WebFetch of https://openrouter.zendesk.com/hc/en-us/articles/40858600529307-Refunds-and-Payment-Information
fact: 24 hours. Verbatim: "Credits must be unused. Refund requests must be made within 24 hours of purchase. Self-service refunds are available for any amount within the 24-hour window using the refund button."

## openrouter escalation threshold
date: 2026-09-12
method: same fetch as above
fact: none. "any amount" is self-service inside the window. Any escalate_over_cents in a fixture is an operator default, not a fact from this page.

## openrouter platform fee on refund
date: 2026-09-12
method: same fetch as above
fact: "Platform fees are not refunded." Refund amount is credits purchased minus the platform fee. The fee percentage is not stated on this page; measure it separately before any fixture uses it.

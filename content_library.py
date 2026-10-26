"""PropReport Instagram content library.

Original, CTA-free education for Melbourne property buyers. The editorial
style uses strong hooks, local situations and practical decision rules without
copying any creator's wording or personal style.

Time-sensitive claims in this edition were checked against Consumer Affairs
Victoria, the State Revenue Office, Victorian planning and education sources,
and the REIV in October 2026.

Increment CONTENT_VERSION whenever the whole library is replaced. The posting
agent uses it to begin the new series at its first post instead of carrying an
index across from a retired library.
"""

CONTENT_VERSION = "melbourne_buyer_field_notes_v2_2026_10"


POSTS = [
    {
        "id": "mb01",
        "style": "dark_statement",
        "tag": "Price Reality",
        "headline": "Seven days before auction,\nthe pricing conversation changes.",
        "caption": (
            "Victorian auction campaigns now have a new checkpoint. The seller's reserve price must be published at least seven days before the auction or fixed-date sale.\n\n"
            "Compare the latest Property Price Statement with the original advertised range and its comparable sales.\n\n"
            "The reserve tells you the seller's minimum. It does not tell you the home's market value, or what it is worth to you."
        ),
    },
    {
        "id": "mb02",
        "style": "light_statement",
        "tag": "Auction Week",
        "headline": "Your Saturday bid is only as good\nas your Friday due diligence.",
        "caption": (
            "Before auction day, a prepared Melbourne buyer has already:\n\n"
            "• Confirmed finance and the deposit process\n"
            "• Had the contract and Section 32 reviewed\n"
            "• Completed the right property inspections\n"
            "• Read the current Property Price Statement\n"
            "• Set a walk-away price from comparable sales\n\n"
            "At auction, most of the important decisions should already be finished."
        ),
    },
    {
        "id": "mb03",
        "style": "stat",
        "tag": None,
        "big_number": "48 days",
        "sub_line": "was Victoria's median private-sale time in September 2026.",
        "dark_bg": False,
        "caption": (
            "A slower campaign can give buyers more time to compare, investigate and negotiate. It does not make every vendor distressed or every property good value.\n\n"
            "Read days on market beside price changes, open-home activity, competing stock and the quality of the property itself.\n\n"
            "Market context: REIV reported a 48-day median for Victorian private sales in September 2026."
        ),
    },
    {
        "id": "mb04",
        "style": "dark_statement",
        "tag": "Current Market",
        "headline": "More choice is permission to be patient.\nNot permission to be careless.",
        "caption": (
            "Melbourne buyers currently have more stock and less competition in many segments than they did a year ago. That improves selection; it does not remove property-specific risk.\n\n"
            "Use the extra time to reject compromised floor plans, investigate defects and compare similar sales.\n\n"
            "A softer market rewards standards more than urgency."
        ),
    },
    {
        "id": "mb05",
        "style": "light_statement",
        "tag": "Market Data",
        "headline": "A city-wide clearance rate cannot\nprice one home on one street.",
        "caption": (
            "Victoria recorded a 70.1% auction clearance rate in September 2026. Useful context, but a weak valuation tool on its own.\n\n"
            "Separate the market by suburb, property type, land size, condition and price bracket. Then inspect the passed-in results as carefully as the sales.\n\n"
            "A headline describes the crowd. Comparable sales describe the property."
        ),
    },
    {
        "id": "mb06",
        "style": "stat",
        "tag": None,
        "big_number": "3 prices",
        "sub_line": "matter on auction week — and only one protects the buyer.",
        "dark_bg": True,
        "caption": (
            "1. The advertised estimate frames the campaign.\n"
            "2. The disclosed reserve sets the seller's minimum.\n"
            "3. Your walk-away price protects your finances.\n\n"
            "Build the third price from comparable sales, property condition, ownership costs and borrowing comfort.\n\n"
            "More transparent pricing is useful. Independent judgment is still essential."
        ),
    },
    {
        "id": "mb07",
        "style": "dark_statement",
        "tag": "Auction Language",
        "headline": "A vendor bid is not\nanother buyer valuing the home.",
        "caption": (
            "In Victoria, a vendor bid is made by the auctioneer on the seller's behalf to advance the bidding. It must be identified as a vendor bid.\n\n"
            "It is not evidence that another buyer will pay that amount.\n\n"
            "Separate auction theatre from market evidence. Your limit should move only when the evidence changes."
        ),
    },
    {
        "id": "mb08",
        "style": "light_statement",
        "tag": "Passed In",
        "headline": "Highest bidder gets the first conversation.\nNot an automatic bargain.",
        "caption": (
            "When a Victorian property passes in below reserve, the highest bidder must be invited to negotiate with the seller first.\n\n"
            "That position has value, but the reserve may still sit above the evidence. Keep the same walk-away number, ask for the contract changes in writing and use silence carefully.\n\n"
            "First access to the negotiation is leverage. It is not an obligation to close the gap."
        ),
    },
    {
        "id": "mb09",
        "style": "stat",
        "tag": None,
        "big_number": "0 days",
        "sub_line": "of cooling-off protection when the hammer falls.",
        "dark_bg": False,
        "caption": (
            "A residential property bought at public auction in Victoria has no cooling-off period. The usual private-sale cooling-off right also has important auction-related exceptions.\n\n"
            "Finance, legal review and inspections belong before bidding.\n\n"
            "The auction lasts minutes. The contract can shape decades of cash flow."
        ),
    },
    {
        "id": "mb10",
        "style": "dark_statement",
        "tag": "Section 32",
        "headline": "Disclosure is not the same thing\nas due diligence.",
        "caption": (
            "A Section 32 can disclose title details, outgoings, planning information and owners-corporation material. It is not a building inspection, a valuation or a promise that the property suits your plans.\n\n"
            "Have the contract and Section 32 reviewed before signing or bidding. Match the documents against the physical property and your intended use.\n\n"
            "A document can be complete and still leave important questions unanswered."
        ),
    },
    {
        "id": "mb11",
        "style": "light_statement",
        "tag": "Apartment Check",
        "headline": "Low owners-corporation fees can be\na warning disguised as a saving.",
        "caption": (
            "The quarterly fee is only the visible number. Read it beside:\n\n"
            "• The maintenance fund and budget\n"
            "• Recent meeting minutes and resolutions\n"
            "• Approved or proposed special levies\n"
            "• Building insurance and claims\n"
            "• Defects, disputes and major works\n\n"
            "A building that collects too little today may ask owners for much more tomorrow."
        ),
    },
    {
        "id": "mb12",
        "style": "stat",
        "tag": None,
        "big_number": "12 months",
        "sub_line": "is how old a prepared Section 32 may already be.",
        "dark_bg": True,
        "caption": (
            "Consumer Affairs Victoria notes that Section 32 statements are sometimes prepared up to 12 months before a property sells.\n\n"
            "For an owners-corporation property, ask whether the certificate is current and inspect the register for newer minutes, levies, repairs, insurance changes or disputes.\n\n"
            "The date on the information matters as much as the information itself."
        ),
    },
    {
        "id": "mb13",
        "style": "dark_statement",
        "tag": "Period Homes",
        "headline": "Melbourne charm comes\nwith a maintenance history.",
        "caption": (
            "Decorative ceilings, fireplaces and original boards create character. They do not reveal what is happening under the floor or behind the walls.\n\n"
            "For an older home, investigate drainage, subfloor moisture, stumps, roof, wiring, plumbing, cracking and past extensions. Check permits where work has changed the structure.\n\n"
            "Character is visible. Condition needs evidence."
        ),
    },
    {
        "id": "mb14",
        "style": "light_statement",
        "tag": "Renovation Plans",
        "headline": "The renovation idea starts with\nthe overlay, not the floor plan.",
        "caption": (
            "Before pricing an extension or knockdown-rebuild, search the exact address in VicPlan. Review the zone, heritage controls, flooding overlays, vegetation controls and bushfire information.\n\n"
            "Then check the local council record for permits and nearby applications.\n\n"
            "A property can suit the life you have and still resist the renovation you imagined."
        ),
    },
    {
        "id": "mb15",
        "style": "stat",
        "tag": None,
        "big_number": "1 address",
        "sub_line": "can tell three different stories across three official maps.",
        "dark_bg": False,
        "caption": (
            "Search the exact property, not just the suburb:\n\n"
            "1. VicPlan for zones, overlays and planning controls\n"
            "2. The local council portal for applications and permits\n"
            "3. Find my School for the current government-school zone\n\n"
            "Suburb-level assumptions disappear when the decision becomes address-specific."
        ),
    },
    {
        "id": "mb16",
        "style": "dark_statement",
        "tag": "Micro Location",
        "headline": "Near the station is a map claim.\nQuiet near the station is a site visit.",
        "caption": (
            "A short walk to transport can improve daily life and resale appeal. The same location may bring crossing bells, platform announcements, commuter parking or train noise.\n\n"
            "Visit during the morning peak, evening peak and late evening. Stand in the quietest bedroom with the windows open.\n\n"
            "Convenience is measured in minutes. Liveability is measured at the property."
        ),
    },
    {
        "id": "mb17",
        "style": "light_statement",
        "tag": "Apartment Reality",
        "headline": "North-facing matters less on paper\nthan it does inside the room.",
        "caption": (
            "Orientation is only the start. A neighbouring tower, deep balcony, small window or future development can change the light completely.\n\n"
            "Visit at the time of day you expect to use the room. Check winter sun angles, privacy, cross-ventilation and nearby planning applications.\n\n"
            "The compass direction is a feature. Usable light is the outcome."
        ),
    },
    {
        "id": "mb18",
        "style": "stat",
        "tag": None,
        "big_number": "$600k",
        "sub_line": "is a Victorian duty threshold — not a buying strategy.",
        "dark_bg": True,
        "caption": (
            "Eligible Victorian first-home buyers currently pay no land transfer duty on homes up to $600,000, with a concession from $600,001 to $750,000. Conditions apply.\n\n"
            "A concession can improve the upfront budget. It cannot make the wrong location, weak building or unsuitable floor plan a better purchase.\n\n"
            "Calculate the benefit. Judge the property separately."
        ),
    },
    {
        "id": "mb19",
        "style": "dark_statement",
        "tag": "Comparable Sales",
        "headline": "Price per square metre can create\nprecision without accuracy.",
        "caption": (
            "Two Melbourne properties can share a postcode and a price-per-square-metre figure while differing in orientation, land shape, renovation quality, parking, street position and planning constraints.\n\n"
            "For apartments, confirm whether the quoted area includes balconies, car spaces or storage. For houses, separate land value from building condition.\n\n"
            "A ratio is a clue. The comparable still needs to be comparable."
        ),
    },
    {
        "id": "mb20",
        "style": "light_statement",
        "tag": "Off Market",
        "headline": "Off-market changes the audience.\nIt does not prove the value.",
        "caption": (
            "Less public competition can help a buyer. Less public testing can also make the asking price harder to assess.\n\n"
            "Use recent settled sales, inspect the contract, investigate the property and set a walk-away price exactly as you would for a listed home.\n\n"
            "Access describes how you found the property. Evidence decides whether it is worth buying."
        ),
    },
    {
        "id": "mb21",
        "style": "stat",
        "tag": None,
        "big_number": "+2%",
        "sub_line": "is a useful repayment test, not an interest-rate prediction.",
        "dark_bg": False,
        "caption": (
            "Calculate the proposed loan at today's offered rate and again two percentage points higher. Add council rates, insurance, owners-corporation fees and a realistic maintenance allowance.\n\n"
            "Then test the same budget against parental leave, reduced overtime or one large repair.\n\n"
            "A resilient purchase has room for more than one version of the future."
        ),
    },
    {
        "id": "mb22",
        "style": "dark_statement",
        "tag": "Negotiation",
        "headline": "A longer campaign changes leverage.\nIt does not prove desperation.",
        "caption": (
            "Days on market can signal a price mismatch, a failed campaign, a difficult property or simply a patient seller. Find out which.\n\n"
            "Track guide changes, prior offers, auction history, contract changes and competing listings. Ask what settlement timing matters to the vendor.\n\n"
            "Time creates questions. Answers create negotiating power."
        ),
    },
    {
        "id": "mb23",
        "style": "light_statement",
        "tag": "Offer Strategy",
        "headline": "The strongest offer is a package.\nPrice is only one term.",
        "caption": (
            "A seller may weigh certainty and timing beside the dollar amount. Before offering, decide what can safely move:\n\n"
            "• Settlement date\n"
            "• Deposit amount and timing\n"
            "• Finance or inspection conditions\n"
            "• Included fixtures and contract changes\n\n"
            "Improve terms only after understanding the risk. A cleaner offer is not better if it removes protection you need."
        ),
    },
    {
        "id": "mb24",
        "style": "stat",
        "tag": None,
        "big_number": "1 page",
        "sub_line": "is enough to expose an emotional property decision.",
        "dark_bg": True,
        "caption": (
            "Before an offer or auction, write a one-page buyer brief:\n\n"
            "• Three reasons the property fits\n"
            "• Three risks or compromises\n"
            "• Three closest settled sales\n"
            "• Immediate costs after settlement\n"
            "• Fair-value range and walk-away price\n\n"
            "If the numbers change in the room but the evidence has not, emotion is doing the bidding."
        ),
    },
]

"""
PropReport Instagram content library.
Each entry: id, style (dark_statement | light_statement | stat), headline/number/sub, tag, caption.
Educational/value-led, Dan Koe voice: short, declarative, principle-driven, quiet CTA.

Add new posts to this list to expand the rotation. The pipeline cycles through
them in order and loops back to the start when it reaches the end.
"""

POSTS = [
    {
        "id": "p01",
        "style": "dark_statement",
        "tag": "Property Truths",
        "headline": "Most buyers research the house.\nFew research the suburb.",
        "caption": (
            "Most people spend weeks comparing kitchens.\n\n"
            "Zero minutes comparing flood maps, crime stats, and school catchments.\n\n"
            "The house is temporary. The suburb is permanent.\n\n"
            "Know both before you offer.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p02",
        "style": "light_statement",
        "tag": "Property Truths",
        "headline": "The comparable sales matter more\nthan the listing photos.",
        "caption": (
            "Anyone can stage a listing.\n\n"
            "Nobody can stage a suburb's last 12 months of actual sales.\n\n"
            "That's the number that sets your ceiling.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p03",
        "style": "stat",
        "tag": None,
        "big_number": "5km",
        "sub_line": "is the radius that decides your school catchment\u2014and your resale value.",
        "dark_bg": True,
        "caption": (
            "5km decides your school catchment.\n\n"
            "It also decides your resale value in 10 years.\n\n"
            "Most buyers never check it.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p04",
        "style": "light_statement",
        "tag": "Risk Check",
        "headline": "Flood zones don't show up\non a real estate listing.\nThey show up on your insurance bill.",
        "caption": (
            "A real estate listing sells you a feeling.\n\n"
            "A flood overlay tells you the truth.\n\n"
            "Check both before you sign.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p05",
        "style": "dark_statement",
        "tag": "Try This",
        "headline": "You can inspect a house in 20 minutes.\nA suburb takes hours of research.\n\nUnless you automate it.",
        "caption": (
            "You can inspect a house in 20 minutes.\n\n"
            "A suburb takes hours of research most buyers never do.\n\n"
            "Unless you automate it.\n\n"
            "Get a full property report in minutes \u2014 propreport.com.au"
        ),
    },
    {
        "id": "p06",
        "style": "stat",
        "tag": None,
        "big_number": "$9.99",
        "sub_line": "is cheaper than one bad property decision.",
        "dark_bg": False,
        "caption": (
            "A building inspection costs hundreds.\n\n"
            "A conveyancer costs thousands.\n\n"
            "Knowing which suburb to even look in costs $9.99.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p07",
        "style": "light_statement",
        "tag": "Property Truths",
        "headline": "Days on market tells you\nmore than the asking price.",
        "caption": (
            "A high asking price means nothing.\n\n"
            "A property sitting for 90 days tells you the market already said no.\n\n"
            "Read the signal, not the sign.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p08",
        "style": "dark_statement",
        "tag": "Infrastructure",
        "headline": "A rail extension announced today\nis a price rise in three years.",
        "caption": (
            "Infrastructure moves before prices do.\n\n"
            "Rail lines. Road upgrades. Rezoning.\n\n"
            "The buyers who check council plans get there first.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p09",
        "style": "light_statement",
        "tag": "Property Truths",
        "headline": "Auction clearance rate is a\nsuburb's mood, not its value.",
        "caption": (
            "A 90% clearance rate means buyers are confident.\n\n"
            "It doesn't mean you should be.\n\n"
            "Confidence and value are different numbers. Check both.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p10",
        "style": "stat",
        "tag": None,
        "big_number": "0",
        "sub_line": "is how much personal data we store after your report is sent.",
        "dark_bg": True,
        "caption": (
            "Your email delivers the report. That's all it does.\n\n"
            "No storing. No selling. No follow-up calls.\n\n"
            "Property research shouldn't cost your privacy.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p11",
        "style": "dark_statement",
        "tag": "Try This",
        "headline": "Before you fall in love with a house, check if you'd fall in love with the commute.",
        "caption": (
            "Peak hour to the CBD is a number.\n\n"
            "It's also two hours of your life, every day, for as long as you live there.\n\n"
            "Check it before the open home, not after settlement.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p12",
        "style": "light_statement",
        "tag": "Property Truths",
        "headline": "A good school zone is worth more than a good kitchen.",
        "caption": (
            "Kitchens get renovated.\n\n"
            "School catchments don't move.\n\n"
            "One of these is a permanent asset. Choose accordingly.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p13",
        "style": "dark_statement",
        "tag": "Property Truths",
        "headline": "A high rental yield and high capital growth\nrarely live in the same suburb.",
        "caption": (
            "Investors chase yield.\n\n"
            "Homeowners chase growth.\n\n"
            "Few suburbs deliver both at once — know which trade-off you're making before you buy.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p14",
        "style": "light_statement",
        "tag": "Risk Check",
        "headline": "No listing history means\nno comparable sales to check it against.",
        "caption": (
            "Off-market feels exclusive.\n\n"
            "It also means the price was never tested by other buyers.\n\n"
            "Run the comparables yourself before you trust the exclusivity.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p15",
        "style": "stat",
        "tag": None,
        "big_number": "1%",
        "sub_line": "vacancy rate is the line between a landlord's market and a tenant's market.",
        "dark_bg": True,
        "caption": (
            "Below 1% vacancy, tenants compete for you.\n\n"
            "Above 3%, you compete for tenants.\n\n"
            "Check the number before you buy for yield.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p16",
        "style": "dark_statement",
        "tag": "Property Truths",
        "headline": "Waiting for the 'right' rate\nhas cost more buyers than the rate itself.",
        "caption": (
            "Nobody times the bottom.\n\n"
            "The suburb you can afford today is worth more than the rate cut you're waiting for.\n\n"
            "Buy the right property. Refinance the rate later.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p17",
        "style": "light_statement",
        "tag": "Try This",
        "headline": "A new kitchen sells the house.\nIt rarely returns its cost at resale.",
        "caption": (
            "Cosmetic renovations sell to emotion.\n\n"
            "Structural fixes protect value.\n\n"
            "Know which one you're actually paying for.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p18",
        "style": "stat",
        "tag": None,
        "big_number": "70%",
        "sub_line": "of a property's long-term value sits in the land, not the build.",
        "dark_bg": False,
        "caption": (
            "Buildings depreciate.\n\n"
            "Land — in the right suburb — doesn't.\n\n"
            "Check the land-to-asset ratio before you fall for the finishes.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p19",
        "style": "dark_statement",
        "tag": "Risk Check",
        "headline": "The body corporate fee is a mortgage\nyou didn't know you signed up for.",
        "caption": (
            "$150 a month feels small on the listing.\n\n"
            "Over a 30-year loan it's tens of thousands.\n\n"
            "Check the strata report, not just the price.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p20",
        "style": "light_statement",
        "tag": "Property Truths",
        "headline": "Falling in love at the open home\nis how you overpay at the auction.",
        "caption": (
            "Auctions are built to move fast on emotion.\n\n"
            "The suburb data doesn't move at all.\n\n"
            "Know your ceiling before you walk in.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p21",
        "style": "stat",
        "tag": None,
        "big_number": "+2.1%",
        "sub_line": "annual population growth is a better price predictor than last year's headlines.",
        "dark_bg": True,
        "caption": (
            "Prices follow people.\n\n"
            "Population growth shows you where demand is heading before the headlines catch up.\n\n"
            "propreport.com.au"
        ),
    },
    {
        "id": "p22",
        "style": "dark_statement",
        "tag": "Risk Check",
        "headline": "The valuation at settlement\ncan be lower than the price you signed for.",
        "caption": (
            "Off-the-plan locks in today's price for a property built years from now.\n\n"
            "The market — and the bank's valuer — might disagree by settlement.\n\n"
            "Know the gap before you sign.\n\n"
            "propreport.com.au"
        ),
    },
]

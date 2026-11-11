
TEST_SCENARIOS = [

    # 1. Card-not-present fraud
    {
        "id": 1,
        "description": "An unknown online card purchase appeared on my statement.",
        "expected": "Card-not-present fraud"
    },
    {
        "id": 2,
        "description": "My credit card was used online without my permission.",
        "expected": "Card-not-present fraud"
    },
    {
        "id": 3,
        "description": "Someone made an unauthorised online card transaction.",
        "expected": "Card-not-present fraud"
    },
    {
        "id": 4,
        "description": "My card details were used without my physical card.",
        "expected": "Card-not-present fraud"
    },

    # 2. Skimming
    {
        "id": 5,
        "description": "Someone used an ATM skimmer to copy my card details.",
        "expected": "Skimming"
    },
    {
        "id": 6,
        "description": "My debit card was cloned at an ATM.",
        "expected": "Skimming"
    },
    {
        "id": 7,
        "description": "My card data was copied using a skimming device.",
        "expected": "Skimming"
    },
    {
        "id": 8,
        "description": "My card was cloned after using a compromised ATM.",
        "expected": "Skimming"
    },

    # 3. UPI social engineering
    {
        "id": 9,
        "description": "A caller impersonating my bank asked me to share my OTP through UPI.",
        "expected": "UPI social engineering"
    },
    {
        "id": 10,
        "description": "I received a fake UPI collect request and lost money.",
        "expected": "UPI social engineering"
    },
    {
        "id": 11,
        "description": "A person pretending to be a bank employee tricked me into sharing my OTP.",
        "expected": "UPI social engineering"
    },
    {
        "id": 12,
        "description": "I scanned a fraudulent QR code during a UPI transaction.",
        "expected": "UPI social engineering"
    },

    # 4. Merchant dispute
    {
        "id": 13,
        "description": "I paid for a product but never received my product.",
        "expected": "Merchant dispute"
    },
    {
        "id": 14,
        "description": "The merchant charged me but my order was cancelled.",
        "expected": "Merchant dispute"
    },
    {
        "id": 15,
        "description": "I received the wrong product and want a refund.",
        "expected": "Merchant dispute"
    },
    {
        "id": 16,
        "description": "The service I paid for was not received.",
        "expected": "Merchant dispute"
    },

    # 5. Duplicate charge
    {
        "id": 17,
        "description": "I was charged twice for the same transaction.",
        "expected": "Duplicate charge"
    },
    {
        "id": 18,
        "description": "My bank account was debited twice for one purchase.",
        "expected": "Duplicate charge"
    },
    {
        "id": 19,
        "description": "The same transaction appeared twice on my statement.",
        "expected": "Duplicate charge"
    },
    {
        "id": 20,
        "description": "There are two charges for one payment.",
        "expected": "Duplicate charge"
    }
]

print("20 evaluation scenarios created successfully!")
print("Total scenarios:", len(TEST_SCENARIOS))

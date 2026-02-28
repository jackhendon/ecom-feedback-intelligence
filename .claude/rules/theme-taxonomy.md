# Theme Taxonomy

These are the only valid themes. Use exact slugs. Do not create new themes.

---

## `packaging`
Physical packaging of the product: box quality, tissue paper, ribbon, presentation, unboxing experience, environmental concerns about packaging waste or plastic.

**Include**: wrapping, presentation box, gift bag, tissue paper, bubble wrap, "beautifully presented", "excessive plastic", "sustainable packaging"
**Exclude**: product itself (→ `product_quality`), delivery condition damage (→ `delivery`)

---

## `personalisation`
Customisation of the product: name printing, monogram, photo upload, custom text, engraving, colour choices, font choices.

**Include**: "personalised", "my name on it", "gold foil lettering", "custom photo", "bespoke", "initials"
**Exclude**: generic product choice (→ `product_quality`), website customisation tool (→ `website_ux`)

---

## `delivery`
Speed, reliability, and communication of shipping. Includes tracking, carrier experience, missed deadlines, guaranteed delivery failures.

**Include**: "arrived late", "no tracking updates", "Royal Mail", "DPD", "guaranteed by Christmas", "delivery estimate", "dispatch notification"
**Exclude**: product damaged on arrival where packaging is blamed (→ `packaging`), returns process (→ `customer_service`)

---

## `product_quality`
Physical quality of the finished product: print quality, paper weight, binding, colour accuracy, durability, construction.

**Include**: "paper feels premium", "vibrant colours", "binding fell apart", "print quality", "smudged ink", "sturdy cover"
**Exclude**: personalisation accuracy (→ `personalisation`), product design/style choices

---

## `website_ux`
Experience of using the website or app: navigation, personalisation tool UX, checkout flow, account management, mobile experience, error states.

**Include**: "hard to navigate", "customisation tool crashed", "checkout took forever", "couldn't find", "website glitch", "mobile app"
**Exclude**: product images that don't match reality (→ `product_quality`)

---

## `customer_service`
Human interactions with Papier's support team: response time, quality of resolution, tone, refund handling, complaint handling.

**Include**: "4 days to respond", "generic apology", "full refund", "helpful agent", "live chat", "email support", "no response"
**Exclude**: automated emails like dispatch notifications (→ `delivery`)

---

## `pricing`
Perceived value for money, price changes, discount codes, comparison to competitors.

**Include**: "too expensive", "price has gone up", "used to be cheaper", "worth the money", "good value", "competitor is cheaper"
**Exclude**: postage/shipping costs (→ `delivery`)

---

## `gifting_experience`
The experience of giving or receiving a Papier product as a gift, including emotional resonance, gift wrap options, gift messaging, recipient reaction.

**Include**: "perfect gift", "she loved it", "gift message", "anniversary present", "birthday present", "gift wrapping"
**Exclude**: delivery timing that affected a gift (→ `delivery` as primary, `gifting_experience` as secondary if emotional impact is described)

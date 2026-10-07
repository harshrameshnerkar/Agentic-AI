"""
DATASET MODULE: 50 Diverse Sentences Across 5 Thematic Clusters
Includes deliberate negation traps and antonym contradictions to test embedding limitations.
"""

SENTENCES = [
    # --- Category 1: Technology & Software (10 sentences) ---
    "Artificial intelligence models are rapidly transforming software development workflows.",
    "Python is one of the most widely used languages for data science and machine learning.",
    "The new GPU cluster accelerates transformer training by more than four hundred percent.",
    "Containerization with Docker simplifies deploying microservices across distributed clouds.",
    "I absolutely love this smartphone, the camera takes breathtaking photos in low light.",
    "I do NOT like this smartphone, the camera is terrible, blurry, and completely useless.",  # Negation Trap
    "Debugging concurrency issues in asynchronous code can be challenging for junior engineers.",
    "Version control using Git is an essential prerequisite for collaborative engineering.",
    "Open-source large language models are becoming increasingly competitive with closed proprietary APIs.",
    "The operating system crashed with a blue screen kernel panic after the driver update.",

    # --- Category 2: Food & Culinary (10 sentences) ---
    "The Italian chef prepared fresh handmade tagliatelle pasta with aromatic white truffles.",
    "Slow-cooking beef brisket over hickory smoke creates incredible tenderness and rich flavor.",
    "The restaurant served an exquisite, steaming hot bowl of spicy ramen soup.",
    "The restaurant served a freezing cold, unappetizing, stale bowl of vegetable soup.",  # Antonym Trap
    "Artisan sourdough bread requires a healthy fermentation starter and high-hydration dough.",
    "Consuming high amounts of processed refined sugar has been linked to chronic metabolic diseases.",
    "A freshly brewed cup of Ethiopian light-roast coffee features delicate floral and citrus notes.",
    "Adding a pinch of kosher salt to chocolate desserts enhances their deep cocoa sweetness.",
    "Sushi chefs train for years to master slicing sashimi with razor-sharp Japanese knives.",
    "Vegetarian Mediterranean diets emphasize fresh olive oil, crisp vegetables, and legumes.",

    # --- Category 3: Finance & Business (10 sentences) ---
    "The central bank voted to lower benchmark interest rates to stimulate economic lending.",
    "Diversifying your investment portfolio across asset classes mitigates systematic market risk.",
    "The enterprise software startup announced a series B funding round of forty million dollars.",
    "High inflation erodes purchasing power, forcing consumers to cut discretionary spending.",
    "The company declared bankruptcy after severe financial losses and mounting debts.",
    "The company avoided bankruptcy and recorded record-breaking quarterly profits.",  # Financial Polarity Trap
    "Venture capital firms evaluate revenue growth, customer retention, and unit economics.",
    "Corporate bond yields increased following rumors of credit rating downgrades.",
    "Automated algorithmic high-frequency trading accounts for significant stock exchange liquidity.",
    "Filing corporate tax returns accurately avoids expensive IRS audit penalties.",

    # --- Category 4: Travel & Geography (10 sentences) ---
    "The historic city of Kyoto is renowned for serene Buddhist temples and cherry blossoms.",
    "Hiking across the Swiss Alps provides majestic panoramic views of glacier-capped peaks.",
    "The passenger booked a round-trip transatlantic flight departing from New York to London.",
    "Coral reefs in tropical oceans host some of the most biodiverse aquatic ecosystems on Earth.",
    "The remote Himalayan village is accessible only by narrow unpaved mountain footpaths.",
    "Exploring ancient Mayan stone pyramids in the dense Guatemalan jungle requires sturdy boots.",
    "The Sahara desert features vast undulating sand dunes that stretch across northern Africa.",
    "Scuba diving alongside sea turtles in the Great Barrier Reef is an unforgettable adventure.",
    "Severe winter blizzards shut down international airports across northern Europe.",
    "The tranquil coastal village boasts charming cobblestone alleyways and sea-facing cafes.",

    # --- Category 5: Health & Fitness (10 sentences) ---
    "Consistent resistance training promotes muscular hypertrophy and enhances bone mineral density.",
    "Prioritizing eight hours of quality sleep every night is vital for cognitive memory consolidation.",
    "High-intensity interval training burns substantial calories in compact twenty-minute sessions.",
    "Maintaining proper hydration during distance marathon running prevents debilitating muscle cramps.",
    "The marathon runner suffered an acute hamstring tear and was unable to finish the race.",
    "The marathon runner recovered from an acute hamstring tear and went on to win the race.",  # Antonym Recovery Trap
    "Practicing mindfulness meditation significantly reduces salivary cortisol stress hormones.",
    "Physical therapy exercises help restore full joint mobility after knee replacement surgery.",
    "Aerobic cardiovascular conditioning enhances maximal oxygen consumption and lung capacity.",
    "Daily stretching routines improve muscular flexibility and alleviate lower back discomfort."
]

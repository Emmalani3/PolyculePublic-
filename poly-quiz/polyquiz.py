class PolyamoryTypeIdentifier:
    def __init__(self):
        self.responses = {}

    def ask_question(self, question_id, question):
        response = input(f"{question} (yes/no): ").strip().lower()
        while response not in ["yes", "no"]:
            response = input("Please answer 'yes' or 'no': ").strip().lower()
        self.responses[question_id] = response == "yes"

    def evaluate(self):
        # Step 1: Check for Hierarchical Polyamory
        if self.responses.get("Q1", False) or self.responses.get("Q2", False):
            if self.responses.get("Q18", False) and self.responses.get("Q3", False):
                return "Hierarchical Polyamory"

        # Step 2: Check for Parallel Polyamory
        if self.responses.get("Q4", False):
            if not self.responses.get("Q7", True) and not self.responses.get("Q9", True):
                return "Parallel Polyamory"

        # Step 3: Check for Solo Polyamory
        if self.responses.get("Q5", False) and self.responses.get("Q6", False):
            if self.responses.get("Q7", False) and not self.responses.get("Q24", True):
                return "Solo Polyamory"

        # Step 4: Check for Kitchen Table Polyamory
        if self.responses.get("Q7", False) and self.responses.get("Q9", False):
            if self.responses.get("Q10", False) and not self.responses.get("Q23", True):
                return "Kitchen Table Polyamory"

        # Step 5: Check for Non-Hierarchical Polyamory
        if not self.responses.get("Q2", True) and self.responses.get("Q10", False):
            if self.responses.get("Q19", False):
                return "Non-Hierarchical Polyamory"

        # Step 6: Check for Relationship Anarchy
        if not self.responses.get("Q19", True) and self.responses.get("Q15", False):
            if not self.responses.get("Q18", True) and self.responses.get("Q6", False):
                return "Relationship Anarchy"

        return "Undetermined Polyamory Style"

# Define questions based on schema
questions = {
    "Q1": "Do you find it easier to focus on one partner as your primary source of support, even if you have others?",
    "Q2": "In your relationships, do you tend to naturally prioritize some connections over others?",
    "Q3": "If one of your partners needed extra time or attention, would you feel comfortable adjusting the balance with other partners?",
    "Q4": "Do you feel it’s important for your partners to keep their relationships with others separate from yours?",
    "Q5": "When making major life decisions (e.g., moving, finances), do you prefer handle these on your own?",
    "Q6": "Do you often structure your daily life around your relationships?",
    "Q7": "Do you value having personal space or privacy, even when in committed relationships?",
    "Q9": "Would you feel comfortable inviting all of your partners to the same social event?",
    "Q10": "If two of your partners wanted to meet or spend time together, would you encourage it?",
    "Q15": "Would you be comfortable if a partner pursued a sexual connection without discussing it with you first?",
    "Q18": "Do you usually feel the need to discuss major relationship changes (like starting a new relationship) with your current partners beforehand?",
    "Q19": "Do you believe that shared agreements or guidelines are essential for maintaining harmony in your relationships?",
    "Q23": "Do you generally prefer to keep your relationships private from the public or social circles?",
    "Q24": "If you imagine your ideal future, does it include a shared household with multiple partners?",
}

# Create an instance of the identifier
identifier = PolyamoryTypeIdentifier()

# Ask questions
for question_id, question in questions.items():
    identifier.ask_question(question_id, question)

# Determine polyamorous style
result = identifier.evaluate()
print(f"Your polyamorous style is: {result}")

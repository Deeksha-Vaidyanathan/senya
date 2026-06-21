# 150 highest-value ASL signs for the hackathon demo
# Trimmed from 300 to fit within 5000 Pika credits
# (~25 credits/clip × 150 = 3750, leaving ~1250 for avatar + runtime demos)

WORD_LIST = [
    # Greetings / social (high demo value)
    "hello", "goodbye", "please", "thank-you", "sorry", "excuse-me", "yes", "no",

    # Core verbs (most common in any sentence)
    "go", "come", "see", "know", "want", "need", "help", "work",
    "eat", "drink", "sleep", "walk", "run", "stop", "start", "finish",
    "sit", "stand", "give", "take", "like", "love", "understand",
    "learn", "ask", "tell", "show", "find", "call", "meet", "think",
    "wait", "open", "close", "read", "write", "play", "buy",

    # Pronouns (essential for any sentence)
    "i", "you", "he", "she", "we", "they", "me",
    "my", "your", "this", "that", "here", "there",

    # Common nouns (broad coverage)
    "person", "man", "woman", "family", "friend",
    "mother", "father", "sister", "brother",
    "home", "school", "store", "car", "food", "water",
    "money", "time", "day", "week", "year", "morning", "night",
    "dog", "cat", "book", "phone", "doctor",

    # Adjectives (most expressive)
    "good", "bad", "big", "small", "hot", "cold", "fast", "slow",
    "happy", "sad", "angry", "sick", "tired", "hungry",
    "old", "new", "easy", "hard", "right", "wrong", "late", "early",

    # Numbers (1-10 only)
    "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten",

    # Colors (most common)
    "red", "blue", "green", "yellow", "black", "white",

    # Time (high utility)
    "today", "tomorrow", "yesterday", "now", "later", "always", "never", "before", "after",

    # Question words (critical for any conversation)
    "what", "where", "when", "who", "why", "how",

    # Useful standalone signs
    "maybe", "again", "more", "enough", "all", "nothing", "because", "but",
]

# Deduplicated and lowercased
WORD_LIST = sorted(set(w.lower() for w in WORD_LIST))

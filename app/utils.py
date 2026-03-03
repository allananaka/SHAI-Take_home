from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def is_follow_up_question(user_input: str, history: List[Dict], threshold: float = 0.3) -> bool:
    """
    Checks if the user input is a semantic follow-up to the conversation history.

    This function uses TF-IDF to vectorize the user's input and the entire
    conversation history. It then calculates the cosine similarity between them.

    Args:
        user_input: The user's latest message.
        history: A list of previous messages in the conversation (user and bot).
        threshold: The similarity score above which the input is considered a follow-up.
                   This value may require tuning based on observed performance.

    Returns:
        True if the similarity score is above the threshold, False otherwise.
    """
    # If there's no history, it cannot be a follow-up.
    if not history:
        return False

    # Short inputs with pronouns are very likely follow-ups. This handles cases
    # like "Who is it for?"
    words = user_input.lower().split()
    contextual_words = {'it', 'they', 'them', 'that', 'those', 'this', 'his', 'her', 'their'}
    if len(words) <= 15 and any(word.strip(".,?!") in contextual_words for word in words):
        return True

    # Join the list of historical messages into a single string.
    history_text = " ".join([msg.get("content", "") for msg in history])

    # Create a TF-IDF Vectorizer.
    vectorizer = TfidfVectorizer(stop_words='english')

    # Generate TF-IDF vectors for the history and the new user input.
    try:
        tfidf_matrix = vectorizer.fit_transform([history_text, user_input])
    except ValueError:
        # This can happen if the vocabulary is empty (e.g., all stop words).
        return False

    # Calculate the cosine similarity between the history vector and the input vector.
    similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    # Return True if the similarity score exceeds our defined threshold.
    return similarity_score > threshold


def trim_history_to_last_n_turns(history: List[Dict], n: int = 5) -> List[Dict]:
    """
    Reduces history to the last n complete turns. A turn is: one "user" message
    through the next "assistant" message (including any "Edited user" / "Matched FAQ" in between).
    """
    if n <= 0 or not history:
        return []
    # Collect (start_index, end_index) for each turn
    turns: List[tuple] = []
    i = 0
    while i < len(history):
        if history[i].get("role") == "user":
            start = i
            i += 1
            while i < len(history):
                if history[i].get("role") == "assistant":
                    turns.append((start, i))
                    i += 1
                    break
                i += 1
        else:
            i += 1
    if not turns:
        return history
    keep = turns[-n:]
    start_idx = keep[0][0]
    return history[start_idx:]

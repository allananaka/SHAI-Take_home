from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def is_follow_up_question(user_input: str, history: List[Dict], threshold: float = 0.2) -> bool:
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

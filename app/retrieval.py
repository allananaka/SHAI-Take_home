from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Optional

class FAQRetriever:
    """
    A class to handle FAQ retrieval using a pre-computed TF-IDF model.
    The vectorizer is fitted once during initialization for efficiency.
    """
    def __init__(self, faq_data: List[Dict]):
        """
        Initializes the retriever, fits the TF-IDF vectorizer, and stores the data.
        """
        self.faq_data = faq_data
        self.questions = [faq.get("question", "") for faq in self.faq_data]
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.vectorizer.fit_transform(self.questions)

    def find_best_match(self, query: str) -> Optional[Dict]:
        """
        Finds the best FAQ match for a user query using the pre-fitted model.

        Args:
            query: The user's input string.

        Returns:
            The FAQ dictionary with the highest similarity score, or None if no
            suitable match is found above a certain threshold.
        """
        if not self.faq_data:
            return None

        # Transform the user query using the pre-fitted vectorizer
        query_vector = self.vectorizer.transform([query])

        # Calculate cosine similarity
        cosine_similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        best_match_index = cosine_similarities.argmax()
        max_similarity = cosine_similarities[best_match_index]

        similarity_threshold = 0.1
        if max_similarity > similarity_threshold:
            return self.faq_data[best_match_index]
        else:
            return None

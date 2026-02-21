from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
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

        # Create a custom stop word list that preserves question words
        # This helps distinguish "Who is..." from "What is..."
        question_words = {'who', 'what', 'where', 'when', 'why', 'how', 'which', 'whom', 'whose'}
        custom_stop_words = list(ENGLISH_STOP_WORDS - question_words)

        # 1. Vectorizer for Questions (High priority)
        self.questions = [faq.get('question', '') for faq in self.faq_data]
        self.question_vectorizer = TfidfVectorizer(stop_words=custom_stop_words)
        self.question_matrix = self.question_vectorizer.fit_transform(self.questions)

        # 2. Vectorizer for Answers (Fallback)
        self.answers = [faq.get('answer', '') for faq in self.faq_data]
        self.answer_vectorizer = TfidfVectorizer(stop_words='english')
        self.answer_matrix = self.answer_vectorizer.fit_transform(self.answers)

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

        # Step 1: Search Questions
        q_vector = self.question_vectorizer.transform([query])
        q_similarities = cosine_similarity(q_vector, self.question_matrix).flatten()
        best_q_index = q_similarities.argmax()
        max_q_sim = q_similarities[best_q_index]

        # Threshold for questions (higher confidence required for title match)
        if max_q_sim > 0.3:
            return self.faq_data[best_q_index]

        # Step 2: Search Answers (Fallback)
        a_vector = self.answer_vectorizer.transform([query])
        a_similarities = cosine_similarity(a_vector, self.answer_matrix).flatten()
        best_a_index = a_similarities.argmax()
        max_a_sim = a_similarities[best_a_index]

        # Threshold for answers (can be lower as it's a broader search)
        if max_a_sim > 0.1:
            return self.faq_data[best_a_index]
        
        return None

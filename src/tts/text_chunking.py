import re
from typing import List

def chunk_text(text: str, max_chars: int = 400) -> List[str]:
    """
    Splits input text into chunks respecting sentence boundaries and character limits.
    
    Args:
        text: The input text to chunk.
        max_chars: Maximum characters allowed per chunk.
        
    Returns:
        A list of clean text chunks.
    """
    if not text or not text.strip():
        return []
        
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split text into sentences using common sentence boundary punctuation (. ! ?) followed by a space
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_endings.split(text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # If a single sentence is larger than max_chars, split by clause punctuation or words
        if len(sentence) > max_chars:
            # Flush current chunk if it has content
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_length = 0
                
            # Split the long sentence by clause markers (comma, semi-colon, colon)
            clauses = re.split(r'(?<=[,;:—])\s+', sentence)
            for clause in clauses:
                clause = clause.strip()
                if not clause:
                    continue
                    
                # If clause is still too long, split by words
                if len(clause) > max_chars:
                    words = clause.split(' ')
                    temp_chunk = []
                    temp_len = 0
                    for word in words:
                        if temp_len + len(word) + (1 if temp_chunk else 0) > max_chars:
                            if temp_chunk:
                                chunks.append(" ".join(temp_chunk))
                            temp_chunk = [word]
                            temp_len = len(word)
                        else:
                            temp_chunk.append(word)
                            temp_len += len(word) + 1
                    if temp_chunk:
                        chunks.append(" ".join(temp_chunk))
                else:
                    chunks.append(clause)
        else:
            # Check if adding the sentence fits in the current chunk
            added_length = len(sentence) + (1 if current_chunk else 0)
            if current_length + added_length <= max_chars:
                current_chunk.append(sentence)
                current_length += added_length
            else:
                # Flush current and start a new one
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence)
                
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return [c.strip() for c in chunks if c.strip()]

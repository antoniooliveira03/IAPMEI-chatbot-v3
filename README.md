# Chatbot Focused on Providing Information about PT2030 Incentives to SMEs

Folder Structure:
- /data - stores all data used by the chatbot
- /botscraper - web crawling and scraping code (using scrapy library)
- /models  - stores a fasttext model used to filter out non-portuguese text

File Structure
- 00_master - runs all knowledge base files 
- 01_cleaning - cleans extracted files
- 02_preprocessing - chunks, filters irrelevant chunks and creates metadata for each chunk
- 03_vectorize - transforms the chunks into vectors and creates the final FAISS index
- website - allows the use of the chatbot from a user-friendly interface
- file_patterns - contains text patterns to be removed from the text (helper file used in 01_cleaning)
- Text Stats - compares basic statistics before and after cleaning techniques are applied to the extracted files
- Evaluation - evaluates the chatbot's performance

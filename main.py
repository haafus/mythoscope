from UI import start_home_page
from corpus_builder.build_corpus import build_and_save_corpus
from embedding_analyzer import analyze_embeddings
from embeddings_builder import build_embeddings
from embeddings_clustering.run_clustering import build_clusters

if __name__ == "__main__":
    #build_and_save_corpus() #Функция создает корпус
    #build_embeddings() #Функция строит эмбеддинги
    #analyze_embeddings() #Функция анализирует эмбеддинги
    #build_clusters()
    start_home_page() # Запускает home page с UI (Долго запускается)

import threading
import socket
import time
import os
import json
import http.server
import socketserver
import webbrowser
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Any

import numpy as np
from sklearn.metrics.pairwise import cosine_distances

from embedding_analyzer.analyzer import EmbeddingAnalyzer

html_dir = os.path.dirname(os.path.abspath(__file__))
PORT = 8000
_server_running = False


def find_free_port(start_port=8000, max_port=9000):
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found")


class Handler(http.server.SimpleHTTPRequestHandler):
    _analyzers = {}
    _search_models = {}  # Кэш для моделей sentence-transformers
    _embeddings_cache = {}  # Кэш для эмбеддингов точек

    @staticmethod
    def normalize_model_name(model_name: str) -> str:
        if not model_name:
            return model_name
        if '_' in model_name and '/' not in model_name:
            return model_name.replace('_', '/')
        return model_name

    def get_analyzer(self, model_name: str) -> EmbeddingAnalyzer:
        normalized_name = self.normalize_model_name(model_name)

        if normalized_name not in self._analyzers:
            self._analyzers[normalized_name] = EmbeddingAnalyzer(
                collection_name="corpus",
                model_name=normalized_name
            )
        return self._analyzers[normalized_name]

    def get_all_data_with_embeddings(self, model_name: str) -> List[Dict[str, Any]]:
        """Получает все данные с эмбеддингами для модели"""
        cache_key = f"{model_name}_data"
        if cache_key in self._embeddings_cache:
            return self._embeddings_cache[cache_key]

        analyzer = self.get_analyzer(model_name)
        data = analyzer.filter_by_model()
        self._embeddings_cache[cache_key] = data
        return data

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # API endpoints
        if path == '/api/get_details' or path.endswith('/api/get_details'):
            self._handle_api_get_details(parsed_url)
            return

        if path == '/api/search' or path.endswith('/api/search'):
            self._handle_api_search(parsed_url)
            return

        if path == '/api/get_neighbors' or path.endswith('/api/get_neighbors'):
            self._handle_api_get_neighbors(parsed_url)
            return

        if path == '/api/get_point_info' or path.endswith('/api/get_point_info'):
            self._handle_api_get_point_info(parsed_url)
            return

        if path == '/api/get_models' or path.endswith('/api/get_models'):
            self._handle_api_get_models()
            return

        if path == '/api/get_plot_data' or path.endswith('/api/get_plot_data'):
            self._handle_api_get_plot_data(parsed_url)
            return

        if 'scan_graph.php' in path:
            self._handle_scan_graph()
            return

        # Статические файлы
        super().do_GET()

    def _send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode('utf-8'))

    def _send_error_response(self, message, status=400):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        error_data = {"error": message}
        self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))

    def _handle_api_get_models(self):
        """Возвращает список доступных моделей"""
        try:
            models_path = os.path.join(html_dir, 'analysis', 'models.json')
            if os.path.exists(models_path):
                with open(models_path, 'r', encoding='utf-8') as f:
                    models = json.load(f)
                    self._send_json_response({"models": models})
                    return

            # Fallback: пробуем получить через analyzer
            analyzer = EmbeddingAnalyzer(collection_name="corpus")
            self._send_json_response({"models": analyzer.available_models})
        except Exception as e:
            self._send_error_response(f"Failed to get models: {str(e)}", 500)

    def _handle_api_get_point_info(self, parsed_url):
        """Возвращает информацию о точке без соседей (быстрый запрос)"""
        query = parse_qs(parsed_url.query)
        point_id = query.get('id', [None])[0]
        model_name = query.get('model', [None])[0]

        if not point_id:
            self._send_error_response("Missing id parameter", 400)
            return

        if not model_name:
            self._send_error_response("Missing model parameter", 400)
            return

        normalized_model = self.normalize_model_name(model_name)

        try:
            data = self.get_all_data_with_embeddings(normalized_model)
            target_item = self._find_item_by_id(data, point_id)

            if not target_item:
                self._send_error_response(f"Point {point_id} not found", 404)
                return

            response_data = {
                "id": str(target_item.get('id')),
                "text": target_item.get('text', 'Текст отсутствует'),
                "tradition": target_item.get('tradition', 'Неизвестно'),
                "chunk_index": target_item.get('chunk_index', 0),
                "model": target_item.get('model', normalized_model)
            }
            self._send_json_response(response_data)

        except Exception as e:
            print(f"Error in get_point_info: {e}")
            import traceback
            traceback.print_exc()
            self._send_error_response(f"Internal Server Error: {str(e)}", 500)

    def _handle_api_get_neighbors(self, parsed_url):
        """Возвращает соседей для точки (вычисления на бэке)"""
        query = parse_qs(parsed_url.query)
        point_id = query.get('id', [None])[0]
        model_name = query.get('model', [None])[0]
        n_neighbors = int(query.get('n', [10])[0])

        if not point_id:
            self._send_error_response("Missing id parameter", 400)
            return

        if not model_name:
            self._send_error_response("Missing model parameter", 400)
            return

        normalized_model = self.normalize_model_name(model_name)

        try:
            data = self.get_all_data_with_embeddings(normalized_model)
            target_item = self._find_item_by_id(data, point_id)

            if not target_item:
                self._send_error_response(f"Point {point_id} not found", 404)
                return

            neighbors = self._compute_neighbors(data, target_item, n_neighbors)

            self._send_json_response({
                "point_id": point_id,
                "neighbors": neighbors
            })

        except Exception as e:
            print(f"Error in get_neighbors: {e}")
            import traceback
            traceback.print_exc()
            self._send_error_response(f"Internal Server Error: {str(e)}", 500)

    def _handle_api_get_details(self, parsed_url):
        """Возвращает полную информацию о точке с соседями"""
        query = parse_qs(parsed_url.query)
        point_id = query.get('id', [None])[0]
        model_name = query.get('model', [None])[0]
        include_neighbors = 'include_neighbors' in query
        n_neighbors = int(query.get('n_neighbors', [10])[0])

        if not point_id:
            self._send_error_response("Missing id parameter", 400)
            return

        if not model_name:
            self._send_error_response("Missing model parameter", 400)
            return

        normalized_model = self.normalize_model_name(model_name)

        try:
            data = self.get_all_data_with_embeddings(normalized_model)
            target_item = self._find_item_by_id(data, point_id)

            if not target_item:
                self._send_error_response(f"Point {point_id} not found", 404)
                return

            response_data = {
                "id": str(target_item.get('id')),
                "text": target_item.get('text', 'Текст отсутствует'),
                "tradition": target_item.get('tradition', 'Неизвестно'),
                "chunk_index": target_item.get('chunk_index', 0),
                "model": target_item.get('model', normalized_model)
            }

            if include_neighbors:
                neighbors = self._compute_neighbors(data, target_item, n_neighbors)
                response_data["neighbors"] = neighbors

            self._send_json_response(response_data)

        except Exception as e:
            print(f"Error in get_details: {e}")
            import traceback
            traceback.print_exc()
            self._send_error_response(f"Internal Server Error: {str(e)}", 500)

    def _handle_api_search(self, parsed_url):
        """Поиск по тексту с вычислением эмбеддинга на бэке"""
        query = parse_qs(parsed_url.query)
        search_text = query.get('q', [None])[0]
        model_name = query.get('model', [None])[0]
        top_k = int(query.get('top_k', [10])[0])

        if not search_text:
            self._send_error_response("Missing q parameter", 400)
            return

        if not model_name:
            self._send_error_response("Missing model parameter", 400)
            return

        normalized_model = self.normalize_model_name(model_name)

        try:
            # Получаем все данные для модели
            data = self.get_all_data_with_embeddings(normalized_model)

            # Генерируем эмбеддинг для запроса
            query_embedding = self._get_query_embedding(normalized_model, search_text)
            if query_embedding is None:
                self._send_error_response("Failed to generate query embedding", 500)
                return

            # Вычисляем косинусное расстояние до всех точек
            results = self._search_by_embedding(data, query_embedding, top_k)

            self._send_json_response({
                "query": search_text,
                "model": normalized_model,
                "results": results,
                "total": len(results)
            })

        except Exception as e:
            print(f"Error in search API: {e}")
            import traceback
            traceback.print_exc()
            self._send_error_response(f"Internal Server Error: {str(e)}", 500)

    def _handle_api_get_plot_data(self, parsed_url):
        """Возвращает данные для построения графика (координаты и метки)"""
        query = parse_qs(parsed_url.query)
        model_name = query.get('model', [None])[0]
        method = query.get('method', ['umap'])[0]

        if not model_name:
            self._send_error_response("Missing model parameter", 400)
            return

        normalized_model = self.normalize_model_name(model_name)

        try:
            # Пытаемся загрузить предварительно вычисленные координаты
            output_dir = os.path.join(html_dir, 'analysis', normalized_model.replace('/', '_'))
            coord_file = os.path.join(output_dir, f'{method}_2d_coords.json')

            if os.path.exists(coord_file):
                with open(coord_file, 'r', encoding='utf-8') as f:
                    coords_data = json.load(f)
                    self._send_json_response(coords_data)
                    return

            # Если нет, вычисляем на лету (медленнее, но работает)
            data = self.get_all_data_with_embeddings(normalized_model)

            if not data:
                self._send_error_response("No data available", 404)
                return

            embeddings = np.stack([item["embedding"] for item in data])

            # Редукция размерности
            from embedding_analyzer.utils import reduce_dimensions
            coords = reduce_dimensions(embeddings, method=method, n_components=2)

            # Формируем ответ
            response_data = {
                "method": method,
                "points": [
                    {
                        "x": float(coords[i, 0]),
                        "y": float(coords[i, 1]),
                        "id": str(data[i].get('id')),
                        "tradition": data[i].get('tradition', 'unknown'),
                        "chunk_index": data[i].get('chunk_index', 0),
                        "text": data[i].get('text', '')[:200]
                    }
                    for i in range(len(data))
                ]
            }

            self._send_json_response(response_data)

        except Exception as e:
            print(f"Error in get_plot_data: {e}")
            import traceback
            traceback.print_exc()
            self._send_error_response(f"Internal Server Error: {str(e)}", 500)

    def _find_item_by_id(self, data: List[Dict], point_id: str) -> Dict:
        """Находит элемент по ID"""
        for item in data:
            if str(item.get('id')) == str(point_id):
                return item
        return None

    def _compute_neighbors(self, data: List[Dict], target_item: Dict, n_neighbors: int = 10) -> List[Dict]:
        """Вычисляет соседей на основе косинусного расстояния"""
        target_emb = np.array(target_item['embedding']).reshape(1, -1)
        embeddings = np.array([item['embedding'] for item in data])

        distances = cosine_distances(target_emb, embeddings)[0]
        nearest_indices = np.argsort(distances)[1:n_neighbors + 1]

        neighbors = []
        for idx in nearest_indices:
            item = data[idx]
            neighbors.append({
                "id": str(item.get('id')),
                "tradition": item.get('tradition', 'Unknown'),
                "distance": float(distances[idx]),
                "similarity_score": 1 - float(distances[idx]),
                "chunk_index": item.get('chunk_index', 0),
                "text_preview": item.get('text', '')[:100]
            })
        return neighbors

    def _search_by_embedding(self, data: List[Dict], query_embedding: List[float], top_k: int = 10) -> List[Dict]:
        """Поиск ближайших точек по эмбеддингу"""
        query_emb = np.array(query_embedding).reshape(1, -1)
        embeddings = np.array([item['embedding'] for item in data])

        distances = cosine_distances(query_emb, embeddings)[0]
        nearest_indices = np.argsort(distances)[:top_k]

        results = []
        for idx in nearest_indices:
            item = data[idx]
            results.append({
                "id": str(item.get('id')),
                "text": item.get('text', ''),
                "tradition": item.get('tradition', 'Unknown'),
                "chunk_index": item.get('chunk_index', 0),
                "similarity_score": 1 - float(distances[idx]),
                "distance": float(distances[idx])
            })

        # Сортируем по убыванию схожести
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results

    def _get_query_embedding(self, model_name: str, text: str) -> List[float]:
        """Генерирует эмбеддинг для текста запроса"""
        try:
            from sentence_transformers import SentenceTransformer
            from embeddings_builder.models_repository import MODELS

            # Используем кэш моделей
            if model_name not in self._search_models:
                if model_name in MODELS:
                    model_path = MODELS[model_name]["path"]
                else:
                    model_path = model_name

                self._search_models[model_name] = SentenceTransformer(model_path)

            model = self._search_models[model_name]
            embedding = model.encode([text], normalize_embeddings=True)[0]
            return embedding.tolist()

        except Exception as e:
            print(f"Error generating query embedding: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _handle_scan_graph(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        graphs_dir = os.path.join(html_dir, 'graphs')
        if not os.path.exists(graphs_dir):
            self.wfile.write(json.dumps([]).encode('utf-8'))
            return

        files = [f for f in os.listdir(graphs_dir) if f.endswith('.html')]
        self.wfile.write(json.dumps(files).encode('utf-8'))


def start_server(port):
    global _server_running
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), Handler) as httpd:
        httpd.request_queue_size = 10
        _server_running = True
        print(f"Server started at http://localhost:{port}")
        print(f"Home page: http://localhost:{port}/template/home.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")
            _server_running = False


def start_home_page():
    global PORT, _server_running
    if _server_running:
        url = f'http://localhost:{PORT}/template/home.html'
        webbrowser.open(url)
        return

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", PORT))
    except OSError:
        PORT = find_free_port(PORT + 1)

    server_thread = threading.Thread(target=start_server, args=(PORT,), daemon=True)
    server_thread.start()
    time.sleep(1.5)

    url = f'http://localhost:{PORT}/template/home.html'
    print(f"Opening: {url}")
    webbrowser.open(url)

    try:
        while _server_running:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
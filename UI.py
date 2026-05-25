import threading
import socket
import time
import os
import json
import csv
import io
import zipfile
import http.server
import socketserver
import webbrowser
import re
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Any

import numpy as np
from sklearn.metrics.pairwise import cosine_distances

from embedding_analyzer.analyzer import EmbeddingAnalyzer

html_dir = os.path.dirname(os.path.abspath(__file__))
PORT = 8000
_server_running = False
NAVBAR_PAGES = {
    os.path.normcase(os.path.normpath(os.path.join('template', page)))
    for page in (
        'home.html',
        'corpus.html',
        'geography.html',
        'embeddings_analysis.html',
        'cluster_analysis.html',
    )
}


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
    _search_models = {}
    _embeddings_cache = {}

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
                model_name=normalized_name
            )
        return self._analyzers[normalized_name]

    def get_all_data_with_embeddings(self, model_name: str) -> List[Dict[str, Any]]:
        cache_key = f"{model_name}_data"
        if cache_key in self._embeddings_cache:
            return self._embeddings_cache[cache_key]

        analyzer = self.get_analyzer(model_name)
        data = analyzer.filter_by_model()
        self._embeddings_cache[cache_key] = data
        return data

    @staticmethod
    def _add_body_class(content: str, class_name: str) -> str:
        def replace_body_tag(match):
            attrs = match.group(1)
            class_attr = re.search(r'class=(["\'])(.*?)\1', attrs, flags=re.IGNORECASE)

            if class_attr:
                classes = class_attr.group(2).split()
                if class_name not in classes:
                    classes.append(class_name)
                    attrs = attrs[:class_attr.start(2)] + ' '.join(classes) + attrs[class_attr.end(2):]
                return f'<body{attrs}>'

            return f'<body{attrs} class="{class_name}">'

        return re.sub(r'<body([^>]*)>', replace_body_tag, content, count=1, flags=re.IGNORECASE)

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

        
        if path.endswith('.html'):
            self._handle_html_template(path)
            return

        if path == '/api/get_corpus_tree':
            self._handle_api_get_corpus_tree()
            return

        if path == '/api/get_corpus_catalog':
            self._handle_api_get_corpus_catalog()
            return

        if path == '/api/get_corpus_document' or path.endswith('/api/get_corpus_document'):
            self._handle_api_get_corpus_document(parsed_url)
            return

        if path == '/api/get_book_content':
            self._handle_api_get_book_content(parsed_url)
            return

        if path == '/api/download_corpus_archive':
            self._handle_api_download_corpus_archive()
            return

        super().do_GET()

    
    def _handle_html_template(self, path):
        
        safe_path = os.path.normpath(path.lstrip('/'))
        file_path = os.path.join(html_dir, safe_path)
        should_inject_navbar = os.path.normcase(safe_path) in NAVBAR_PAGES

        
        if not os.path.abspath(file_path).startswith(os.path.abspath(html_dir)):
            self.send_error(403, "Access denied")
            return

        if not os.path.exists(file_path):
            self.send_error(404, "File not found")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            
            navbar_path = os.path.join(html_dir, 'template', 'navbar.html')

            
            if should_inject_navbar and os.path.exists(navbar_path):
                with open(navbar_path, 'r', encoding='utf-8') as nav_f:
                    navbar_content = nav_f.read()

                style_block = ''
                style_match = re.search(r'\s*<style\b[^>]*>.*?</style>\s*', navbar_content, flags=re.IGNORECASE | re.DOTALL)
                if style_match:
                    style_block = style_match.group(0).strip()
                    navbar_content = navbar_content[:style_match.start()] + navbar_content[style_match.end():]

                if style_block:
                    content, head_replacements = re.subn(
                        r'</head\s*>',
                        lambda match: style_block + '\n' + match.group(0),
                        content,
                        count=1,
                        flags=re.IGNORECASE
                    )
                    if head_replacements == 0:
                        navbar_content = style_block + '\n' + navbar_content

                content = self._add_body_class(content, 'has-main-navbar')
                
                content = re.sub(
                    r'(<body[^>]*>)',
                    lambda match: match.group(1) + '\n' + navbar_content.strip(),
                    content,
                    count=1,
                    flags=re.IGNORECASE
                )

            
            encoded_content = content.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(encoded_content)))
            self.end_headers()
            self.wfile.write(encoded_content)

        except Exception as e:
            print(f"Template Error: {e}")
            self.send_error(500, f"Server Error: {str(e)}")

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
        try:
            models_path = os.path.join(html_dir, 'analysis', 'models.json')
            if os.path.exists(models_path):
                with open(models_path, 'r', encoding='utf-8') as f:
                    models = json.load(f)
                    self._send_json_response({"models": models})
                    return

            analyzer = EmbeddingAnalyzer()
            self._send_json_response({"models": analyzer.available_models})
        except Exception as e:
            self._send_error_response(f"Failed to get models: {str(e)}", 500)

    def _handle_api_get_point_info(self, parsed_url):
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
                "text": target_item.get('text', 'No text available'),
                "tradition": target_item.get('tradition', 'Unknown'),
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
                "text": target_item.get('text', 'No text available'),
                "tradition": target_item.get('tradition', 'Unknown'),
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
            data = self.get_all_data_with_embeddings(normalized_model)

            query_embedding = self._get_query_embedding(normalized_model, search_text)
            if query_embedding is None:
                self._send_error_response("Failed to generate query embedding", 500)
                return

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
        query = parse_qs(parsed_url.query)
        model_name = query.get('model', [None])[0]
        method = query.get('method', ['umap'])[0]

        if not model_name:
            self._send_error_response("Missing model parameter", 400)
            return

        normalized_model = self.normalize_model_name(model_name)

        try:
            output_dir = os.path.join(html_dir, 'analysis', normalized_model.replace('/', '_'))
            coord_file = os.path.join(output_dir, f'{method}_2d_coords.json')

            if os.path.exists(coord_file):
                with open(coord_file, 'r', encoding='utf-8') as f:
                    coords_data = json.load(f)
                    self._send_json_response(coords_data)
                    return

            data = self.get_all_data_with_embeddings(normalized_model)

            if not data:
                self._send_error_response("No data available", 404)
                return

            embeddings = np.stack([item["embedding"] for item in data])

            from embedding_analyzer.utils import reduce_dimensions
            coords = reduce_dimensions(embeddings, method=method, n_components=2)

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
        for item in data:
            if str(item.get('id')) == str(point_id):
                return item
        return None

    def _compute_neighbors(self, data: List[Dict], target_item: Dict, n_neighbors: int = 10) -> List[Dict]:
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
        
        if not data:
            return []

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

        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results

    def _get_query_embedding(self, model_name: str, text: str) -> List[float]:
        try:
            from sentence_transformers import SentenceTransformer
            from embeddings_builder.models_repository import MODELS

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
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()

        graphs_dir = os.path.join(html_dir, 'graphs')
        response_data = {"folders": [], "files": {}}

        if not os.path.exists(graphs_dir):
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        valid_exts = ('.html', '.htm', '.png', '.jpg', '.jpeg', '.svg', '.gif')

        for item in os.listdir(graphs_dir):
            item_path = os.path.join(graphs_dir, item)
            if os.path.isdir(item_path):
                files = [
                    f for f in os.listdir(item_path)
                    if os.path.isfile(os.path.join(item_path, f)) and f.lower().endswith(valid_exts)
                ]
                response_data["folders"].append(item)
                response_data["files"][item] = files

        response_data["folders"].sort()

        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

    def _handle_api_get_corpus_tree(self):
        """Scan corpus_chunked and return its JSON tree."""
        import traceback
        corpus_path = os.path.join(html_dir, 'corpus_chunked')

        if not os.path.exists(corpus_path):
            self._send_error_response(f"Directory not found at {corpus_path}", 404)
            return

        def build_tree(current_path):
            nodes = []
            try:
                entries = sorted([e for e in os.scandir(current_path) if not e.name.startswith('.')],
                                key=lambda e: e.name)
            except Exception:
                return []

            for entry in entries:
                if entry.is_dir():
                    nodes.append({
                        "name": entry.name,
                        "type": "folder",
                        "children": build_tree(entry.path)
                    })
                elif entry.is_file() and entry.name.endswith('.txt'):
                    rel_path = os.path.relpath(entry.path, corpus_path)
                    nodes.append({
                        "name": entry.name,
                        "type": "file",
                        "path": rel_path.replace("\\", "/")
                    })
            return nodes

        try:
            tree_data = build_tree(corpus_path)
            self._send_json_response(tree_data)
        except Exception as e:
            traceback.print_exc()
            self._send_error_response(str(e), 500)

    def _handle_api_get_book_content(self, parsed_url):
        """Return text file contents."""
        query = parse_qs(parsed_url.query)
        rel_path = query.get('path', [None])[0]

        if not rel_path:
            self._send_error_response("Missing path", 400)
            return

        corpus_root = os.path.join(html_dir, 'corpus_chunked')
        safe_path = os.path.normpath(os.path.join(corpus_root, rel_path))

        if not safe_path.startswith(os.path.abspath(corpus_root)):
            self._send_error_response("Access denied", 403)
            return

        try:
            if os.path.exists(safe_path):
                with open(safe_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            else:
                self._send_error_response("File not found", 404)
        except Exception as e:
            self._send_error_response(str(e), 500)


    @staticmethod
    def _sanitize_corpus_path_part(value: str) -> str:
        value = (value or '').replace('/', '_').replace(' ', '_')
        return re.sub(r'[\\/*?:"<>|]', '_', value).strip()

    def _resolve_corpus_document_path(self, doc_id: str, major_tradition: str, tradition: str):
        corpus_root = os.path.abspath(os.path.join(html_dir, 'corpus'))
        major_path = self._sanitize_corpus_path_part(major_tradition)
        tradition_path = self._sanitize_corpus_path_part(tradition)
        title_path = self._sanitize_corpus_path_part(doc_id)
        file_path = os.path.abspath(os.path.join(
            corpus_root,
            major_path,
            tradition_path,
            title_path,
            f'{title_path}.txt'
        ))

        if not file_path.startswith(corpus_root + os.sep):
            return corpus_root, None, title_path

        return corpus_root, file_path, title_path

    @staticmethod
    def _to_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _get_corpus_catalog_documents(self):
        metadata_path = os.path.join(html_dir, 'corpus', 'corpus_metadata.json')
        catalog_path = os.path.join(html_dir, 'corpus', 'corpus_catalog.csv')

        catalog_by_key = {}
        if os.path.exists(catalog_path):
            with open(catalog_path, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = (
                        row.get('id', ''),
                        row.get('major_tradition', ''),
                        row.get('tradition', '')
                    )
                    catalog_by_key[key] = row

        documents = []
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_rows = json.load(f)
        else:
            metadata_rows = []

        source_rows = metadata_rows
        if not source_rows:
            source_rows = list(catalog_by_key.values())

        for row in source_rows:
            key = (
                row.get('id', ''),
                row.get('major_tradition', ''),
                row.get('tradition', '')
            )
            catalog_row = catalog_by_key.get(key, {})
            description = catalog_row.get('description') or row.get('description') or ''

            documents.append({
                "id": row.get('id', ''),
                "major_tradition": row.get('major_tradition', ''),
                "tradition": row.get('tradition', ''),
                "language": row.get('language', ''),
                "type": row.get('type', ''),
                "url": row.get('url', ''),
                "word_count": self._to_int(row.get('word_count', catalog_row.get('word_count'))),
                "sentence_count": self._to_int(row.get('sentence_count', catalog_row.get('sentence_count'))),
                "char_count": self._to_int(row.get('char_count')),
                "color": row.get('color') or catalog_row.get('color') or '#6b7280',
                "description": description,
            })

        documents.sort(key=lambda item: (
            item.get('major_tradition', ''),
            item.get('tradition', ''),
            item.get('id', '')
        ))
        return documents

    def _handle_api_get_corpus_catalog(self):
        try:
            documents = self._get_corpus_catalog_documents()
            self._send_json_response({
                "documents": documents,
                "total": len(documents)
            })
        except Exception as e:
            self._send_error_response(str(e), 500)

    def _handle_api_get_corpus_document(self, parsed_url):
        query = parse_qs(parsed_url.query)
        doc_id = query.get('id', [None])[0]
        major_tradition = query.get('major_tradition', [None])[0]
        tradition = query.get('tradition', [None])[0]
        download = query.get('download', ['0'])[0].lower() in {'1', 'true', 'yes'}

        if not doc_id or not major_tradition or not tradition:
            self._send_error_response("Missing id, major_tradition, or tradition parameter", 400)
            return

        corpus_root, file_path, title_path = self._resolve_corpus_document_path(doc_id, major_tradition, tradition)

        if not file_path:
            self._send_error_response("Access denied", 403)
            return

        if not os.path.exists(file_path):
            self._send_error_response(f"File not found: {os.path.relpath(file_path, html_dir)}", 404)
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            encoded_content = content.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(encoded_content)))
            if download:
                self.send_header('Content-Disposition', f'attachment; filename="{title_path}.txt"')
            self.end_headers()
            self.wfile.write(encoded_content)
        except Exception as e:
            self._send_error_response(str(e), 500)

    def _handle_api_download_corpus_archive(self):
        try:
            documents = self._get_corpus_catalog_documents()
            archive_buffer = io.BytesIO()

            with zipfile.ZipFile(archive_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for doc in documents:
                    corpus_root, file_path, title_path = self._resolve_corpus_document_path(
                        doc.get('id', ''),
                        doc.get('major_tradition', ''),
                        doc.get('tradition', '')
                    )

                    if not file_path or not os.path.exists(file_path):
                        continue

                    archive_name = os.path.join(
                        self._sanitize_corpus_path_part(doc.get('major_tradition', 'Unknown')),
                        self._sanitize_corpus_path_part(doc.get('tradition', 'Unknown')),
                        f'{title_path}.txt'
                    ).replace('\\', '/')
                    archive.write(file_path, archive_name)

            archive_data = archive_buffer.getvalue()
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Length', str(len(archive_data)))
            self.send_header('Content-Disposition', 'attachment; filename="mythoscope_corpus.zip"')
            self.end_headers()
            self.wfile.write(archive_data)
        except Exception as e:
            self._send_error_response(str(e), 500)


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

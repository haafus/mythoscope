import pandas as pd
import networkx as nx
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def create_webpage(nodes_for_js, edges_for_js, output_html_path: Path):
    nodes_json = json.dumps(nodes_for_js, ensure_ascii=False, indent=2)
    edges_json = json.dumps(edges_for_js, ensure_ascii=False, indent=2)

    html_template = """<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Graph</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; overflow: hidden; height: 100vh; display: flex; flex-direction: column; }
            #cy { flex: 1; background-color: #fafafa; }
            #info-panel { position: absolute; bottom: 20px; right: 20px; width: 320px; max-height: 80%; overflow-y: auto; background: rgba(255, 255, 255, 0.95); border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); padding: 16px; font-size: 13px; border: 1px solid #ddd; backdrop-filter: blur(4px); transition: opacity 0.2s; user-select: text; }
            #info-panel table { width: 100%; border-collapse: collapse; }
            #info-panel th, #info-panel td { text-align: left; padding: 6px 4px; border-bottom: 1px solid #f0f0f0; vertical-align: top; }
            #info-panel th { font-weight: 600; color: #4a4a4a; width: 35%; }
            #info-panel td { color: #2c3e50; width: 65%; }
            .close-btn { position: absolute; top: 8px; right: 12px; background: none; border: none; font-size: 18px; cursor: pointer; pointer-events: auto; color: #888; }
            .close-btn:hover { color: #000; }
            h4 { margin: 0 0 8px 0; color: #5e4b8b; }
        </style>
    </head>
    <body>
        <div id="cy"></div>
        <div id="info-panel" style="display: none;">
            <button class="close-btn" id="close-panel">&times;</button>
            <div id="info-content"></div>
        </div>

        <script>
            const nodesData = {nodes_json};
            const edgesData = {edges_json};

            const elements = [
                ...nodesData.map(node => ({ data: node })),
                ...edgesData.map(edge => ({ data: edge }))
            ];

            const categoryColors = {
                'Character': '#dcd0ff',
                'Group': '#cccccc'
            };
            const defaultColor = '#aaaaaa';

            const cy = cytoscape({
                container: document.getElementById('cy'),
                elements: elements,
                style: [
                    {
                        selector: 'node',
                        style: {
                            'background-color': function(ele) { return categoryColors[ele.data('Category')] || defaultColor; },
                            'width': function(ele) { return ele.data('size') || 3; },
                            'height': function(ele) { return ele.data('size') || 3; },
                            'label': function(ele) { return ele.data('display_name') || ele.data('Name') || ele.data('id'); },
                            'font-size': '2.2px',
                            'text-valign': 'bottom',
                            'text-halign': 'center',
                            'text-margin-y': 1,
                            'border-width': 0.2,
                            'border-color': '#555'
                        }
                    },
                    {
                        selector: 'edge',
                        style: {
                            'width': 0.2,
                            'line-color': '#aaa',
                            'target-arrow-color': '#aaa',
                            'target-arrow-shape': 'triangle',
                            'target-arrow-scale': 0.1,
                            'arrow-scale': 0.1,
                            'curve-style': 'bezier',
                            'label': 'data(relation)',
                            'font-size': '1.5px',
                            'text-rotation': 'autorotate',
                            'text-margin-y': -1,
                            'text-background-opacity': 0.7,
                            'text-background-color': '#ffffff'
                        }
                    },
                    {
                        selector: 'node.hover-highlight',
                        style: { 'border-width': 0.3, 'border-color': '#ffaa00', 'overlay-opacity': 0.3, 'overlay-color': '#ffaa00', 'overlay-padding': '1px' }
                    },
                    {
                        selector: 'edge.hover-highlight',
                        style: { 'width': 0.4, 'line-color': '#ffaa00', 'target-arrow-color': '#ffaa00' }
                    },
                    {
                        selector: '.faded',
                        style: { 'opacity': 0.1 }
                    }
                ],
                layout: { name: 'cose', idealEdgeLength: 5, padding: 50, spacingFactor: 5, nodeRepulsion: 40000, gravity: 0.0005, numIter: 10000 },
                wheelSensitivity: 0.5
            });

            let hoveredNode = null;
            function fadeOthers(node) {
                const highlightSet = node.union(node.neighborhood().nodes()).union(node.connectedEdges());
                cy.elements().not(highlightSet).addClass('faded');
                highlightSet.addClass('hover-highlight');
            }
            function restoreAll() { cy.elements().removeClass('faded hover-highlight'); }

            cy.on('mouseover', 'node', function(evt) {
                if (hoveredNode === evt.target) return;
                hoveredNode = evt.target;
                fadeOthers(hoveredNode);
            });
            cy.on('mouseout', 'node', function() {
                hoveredNode = null;
                restoreAll();
            });

            const tooltipDiv = document.createElement('div');
            tooltipDiv.style.cssText = 'position: absolute; background-color: rgba(0,0,0,0.7); color: #fff; padding: 4px 8px; border-radius: 6px; font-size: 12px; pointer-events: none; z-index: 1000; display: none;';
            document.body.appendChild(tooltipDiv);

            const updateTooltip = (evt) => {
                const edge = evt.target;
                const sourceNode = cy.getElementById(edge.data('source'));
                const targetNode = cy.getElementById(edge.data('target'));
                const sName = sourceNode.data('display_name') || edge.data('source');
                const tName = targetNode.data('display_name') || edge.data('target');

                tooltipDiv.innerHTML = `${sName} → ${tName}<br><strong>${edge.data('relation') || ''}</strong>`;
                tooltipDiv.style.left = (evt.originalEvent.clientX + 10) + 'px';
                tooltipDiv.style.top = (evt.originalEvent.clientY + 10) + 'px';
            };

            cy.on('mouseover', 'edge', (evt) => { updateTooltip(evt); tooltipDiv.style.display = 'block'; });
            cy.on('mousemove', 'edge', updateTooltip);
            cy.on('mouseout', 'edge', () => { tooltipDiv.style.display = 'none'; });

            const infoPanel = document.getElementById('info-panel');
            const infoContent = document.getElementById('info-content');

            document.getElementById('close-panel').addEventListener('click', () => infoPanel.style.display = 'none');

            function formatNodeInfo(data) {
                const fieldsOrder = [
                    'Name', 'Category', 'Description', 'Roles', 'Epithets', 'Attributes', 'Actions',
                    'Degree', 'BetweennessCentrality'
                ];
                let html = `<h4>${data.display_name || data.Name || data.id}</h4><table>`;
                fieldsOrder.forEach(f => {
                    if(data[f] !== undefined && data[f] !== null && data[f] !== '') {
                        let value = typeof data[f] === 'object' ? JSON.stringify(data[f]) : data[f];
                        html += `<tr><th>${f}</th><td>${value}</td></tr>`;
                    }
                });
                return html + '</table>';
            }

            cy.on('tap', 'node', (evt) => {
                infoContent.innerHTML = formatNodeInfo(evt.target.data());
                infoPanel.style.display = 'block';
            });
            document.addEventListener('click', (e) => {
                if (!infoPanel.contains(e.target) && e.target !== infoPanel && !cy.getElementById(e.target.id).length) infoPanel.style.display = 'none';
            });
            window.addEventListener('resize', () => cy.resize());
        </script>
    </body>
    </html>"""

    html_content = html_template.replace("{nodes_json}", nodes_json).replace("{edges_json}", edges_json)

    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


def generate_and_save_graph(personas_data: list, relations_data: list, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    personas = pd.DataFrame(personas_data)
    relations = pd.DataFrame(relations_data)

    if not personas.empty:
        personas.rename(columns=lambda x: str(x).strip().title(), inplace=True)
    if not relations.empty:
        relations.rename(columns=lambda x: str(x).strip().title(), inplace=True)

    G = nx.DiGraph()
    node_metadata = {}

    
    persona_names = set(personas['Name'].dropna().astype(
        str).str.strip()) if not personas.empty and 'Name' in personas.columns else set()

    if not personas.empty and 'Name' in personas.columns:
        for _, row in personas.iterrows():
            name = str(row['Name']).strip()
            if not name: continue

            
            meta = {}
            for col, val in row.items():
                if isinstance(val, list):
                    meta[col] = ', '.join(map(str, val))
                else:
                    meta[col] = val

            node_metadata[name] = meta

    if not relations.empty and 'Subject' in relations.columns and 'Object' in relations.columns:
        relations = relations.dropna(subset=['Subject', 'Object'])
        relations = relations[(relations['Subject'] != '') & (relations['Object'] != '')]

        for _, row in relations.iterrows():
            subj = str(row['Subject']).strip()
            obj = str(row['Object']).strip()
            relation_val = row.get('Relation', row.get('relation', ''))

            if subj not in G: G.add_node(subj)
            if obj not in G: G.add_node(obj)
            G.add_edge(subj, obj, relation=relation_val)
    else:
        logger.warning(f"No valid relations. The graph will consist of isolated nodes.")
        
        for name in persona_names:
            if name not in G: G.add_node(name)

    degrees = dict(G.degree())
    betweenness = nx.betweenness_centrality(G)

    min_deg = min(degrees.values()) if degrees else 0
    max_deg = max(degrees.values()) if degrees else 0

    
    def map_size(d):
        if max_deg == min_deg:
            return 4
        return 2 + (d - min_deg) * (6 / (max_deg - min_deg))

    nodes_for_js = []

    for node_id in G.nodes():
        node_id_str = str(node_id)
        meta = node_metadata.get(node_id_str, {})

        node_data = {
            'id': node_id_str,
            'display_name': node_id_str,
            'Category': 'Character' if node_id_str in persona_names else 'Group',
            'Degree': degrees.get(node_id_str, 0),
            'BetweennessCentrality': betweenness.get(node_id_str, 0.0),
            'size': map_size(degrees.get(node_id_str, 0))
        }

        
        for k, v in meta.items():
            if k not in node_data:
                if v not in [None, "", [], "nan", "NaN"] and str(v).lower() != 'nan':
                    node_data[k] = v

        nodes_for_js.append(node_data)

    edges_for_js = [{'source': str(u), 'target': str(v), 'relation': d.get('relation', '')} for u, v, d in
                    G.edges(data=True)]

    
    html_target = output_dir / "characters.html"
    create_webpage(nodes_for_js, edges_for_js, html_target)
    logger.info(f"Character graph saved successfully: {html_target}")

PROJECTION_METHODS = [
    {"key": "umap",                      "label": "UMAP 2D",                   "chart_type": "scatter"},
    {"key": "residual_umap",             "label": "Residual UMAP",             "chart_type": "scatter"},
    {"key": "rlace_umap",                "label": "RLACE UMAP",                "chart_type": "scatter"},
    {"key": "distance_heatmap",          "label": "Tradition similarity",      "chart_type": "heatmap"},
]

PROJECTION_KEYS = {m["key"] for m in PROJECTION_METHODS}

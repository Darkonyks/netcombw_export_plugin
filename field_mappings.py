# -*- coding: utf-8 -*-
"""
Field mappings between QGIS layers and ArcGIS Geodatabase feature classes
"""

# Mapping: PUNKT (QGIS) → COM_DOKU_PUNKT (GDB)
PUNKT_TO_COM_DOKU_PUNKT = {
    'id': 'ID',
    'ART': 'ART',
    'BA_BEZ_COM': 'BA_BEZ_COM',
    'BAUJAHR': 'BAUJAHR',
    'EIGENTUM': 'EIGENTUM',
    'ZV': 'ZWECKVERBAND',
    'FOERDERUNG': 'FOERDERUNG',
    'FOERD_VERS': 'GIS_NB_VERSION',
    'QUELLE': 'ERSTELLER',
    'LQ': 'LAGEQUALITAET',
    'BEMERKUNG': 'BEMERKUNG',
    'GEBIET_ID': 'GEBIET_ID',
}

# Mapping: ROHRMUFFE (QGIS) → COM_DOKU_PUNKT (GDB)
ROHRMUFFE_TO_COM_DOKU_PUNKT = {
    'id': 'ID',
    'ART': 'ART',
    'BAUJAHR': 'BAUJAHR',
    'BEMERKUNG': 'BEMERKUNG',
    'KLASSE': 'KLASSE',
    'GEBIET_ID': 'GEBIET_ID',
}

# Mapping: MESSPUNKT (QGIS) → COM_DOKU_PUNKT (GDB)
MESSPUNKT_TO_COM_DOKU_PUNKT = {
    'id': 'ID',
    'ART': 'ART',
    'BEMERKUNG': 'BEMERKUNG',
    'VERL_TIEF': 'VERLEGETIEFE',
    'DATEIPFAD': 'DATEIPFAD',
    'KLASSE': 'KLASSE',
    'DATUM_EINSPIELUNG': 'DATUM_EINSPIELUNG',
    'GEBIET_ID': 'GEBIET_ID',
}

# Mapping: BAUTEN (QGIS) → COM_DOKU_PUNKT (GDB)
# Note: ART has special logic - if ART='Sonstiges', use ART_SONST value
BAUTEN_TO_COM_DOKU_PUNKT = {
    'id': 'ID',
    'ART': 'ART',
    'BEZEICHNER': 'BEZEICHNUNG',
    'BA_BEZ_COM': 'BA_BEZ_COM',
    'BAUJAHR': 'BAUJAHR',
    'EIGENTUM': 'EIGENTUM',
    'ZWECKVERBAND': 'ZWECKVERBAND',
    'FOERDERUNG': 'FOERDERUNG',
    'FOERD_VERS': 'GIS_NB_VERSION',
    'QUELLE': 'ERSTELLER',
    'LAGEQUALITAET': 'LAGEQUALITAET',
    'BEMERKUNG': 'BEMERKUNG',
    'KLASSE': 'KLASSE',
    'X_WGS': 'X_COORD',
    'Y_WGS': 'Y_COORD',
    'GEBIET_ID': 'GEBIET_ID',
}

# Mapping: NETZTECHNIK (QGIS) → COM_DOKU_PUNKT (GDB)
# Note: ART has special logic - if ART='Sonstige', use ART_SONST value
NETZTECHNIK_TO_COM_DOKU_PUNKT = {
    'id': 'ID',
    'ART': 'ART',
    'BEZEICHNER': 'BEZEICHNUNG',
    'BA_BEZ_COM': 'BA_BEZ_COM',
    'BAUJAHR': 'BAUJAHR',
    'EIGENTUM': 'EIGENTUM',
    'ZWECKVERBAND': 'ZWECKVERBAND',
    'FOERDERUNG': 'FOERDERUNG',
    'FOERD_VERS': 'GIS_NB_VERSION',
    'QUELLE': 'ERSTELLER',
    'LAGEQUALITAET': 'LAGEQUALITAET',
    'BEMERKUNG': 'BEMERKUNG',
    'KLASSE': 'KLASSE',
    'GEBIET_ID': 'GEBIET_ID',
}

# Mapping: ENDVERBRAUCHER (QGIS) → COM_DOKU_PUNKT (GDB)
ENDVERBRAUCHER_TO_COM_DOKU_PUNKT = {
    'id': 'ID',
    'KUNDENTYP': 'KUNDENTYP',
    'KLASSE': 'KLASSE',
    'GEBIET_ID': 'GEBIET_ID',
}

# Mapping: Leerrohre (QGIS) → COM_DOKU_ROHR (GDB)
# Note: LR_FARBE has special logic based on TYP value
# - If TYP contains "Schutzrohr" or "Rohrverband" → use M_FARB
# - If TYP contains "Einzelrohr" → use ER_FARB
LEERROHRE_TO_COM_DOKU_ROHR = {
    'id': 'ID',
    'TYP': 'TYP',
    'LR_RESERV': 'LR_ANZ_FREI',
    'EIGENTUM': 'EIGENTUM',
    # 'LR_FARBE' is handled separately with special logic
    'LR_HERST': 'LR_HERST',
    'LR_VERLMET': 'LR_VERL_METHODE',
    'ID_EINZUG': 'ID_EINZUG',
    'LABEL': 'LABEL',
    'BAUJAHR': 'BAUJAHR',
    'ZV': 'ZWECKVERBAND',
    'QUELLE': 'ERSTELLER',
    'FOERDERUNG': 'FOERDERUNG',
    'FOERD_VERS': 'GIS_NB_VERSION',
    'LQ': 'LAGEQUALITAET',
    'BEMERKUNG': 'BEMERKUNG',
    'GEBIET_ID': 'GEBIET_ID',
    'ROHR_ID': 'ROHR_ID',
}

# Mapping: Verbindungen (QGIS) → COM_DOKU_KABEL (GDB)
# Note: LR_FARBE uses ER_FARB, but if Sonstige use ER_FARB_SON
# Note: ART (VERB_ART) - if Sonstige use V_A_SONST
VERBINDUNGEN_TO_COM_DOKU_KABEL = {
    'id': 'ID',
    'VERB_ART': 'ART',
    'LAE_KABEL': 'LAENGE',
    'TYP': 'TYP',
    # 'LR_FARBE' is handled separately (ER_FARB or ER_FARB_SON)
    'ID_EINZUG': 'ID_EINZUG',
    'LABEL': 'LABEL',
    'BAUJAHR': 'BAUJAHR',
    'EIGENTUM': 'EIGENTUM',
    'ZWECKVERBAND': 'ZWECKVERBAND',
    'FOERDERUNG': 'FOERDERUNG',
    'FOERD_VERS': 'GIS_NB_VERSION',
    'QUELLE': 'ERSTELLER',
    'LQ': 'LAGEQUALITAET',
    'BEMERKUNG': 'BEMERKUNG',
    'GEBIET_ID': 'GEBIET_ID',
    'KABEL_ID': 'KABEL_ID',
}

# Template geodatabase name
TEMPLATE_GDB_NAME = 'GIS_Nebenstimungen_501_geodatabase.gdb'

# Feature class names in geodatabase
GDB_FEATURE_CLASSES = {
    'punkt': 'COM_DOKU_PUNKT',
    'kabel': 'COM_DOKU_KABEL',
    'rohr': 'COM_DOKU_ROHR',
    'rel_kabel_rohr': 'REL_KABEL_ROHR',
}

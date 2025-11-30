# -*- coding: utf-8 -*-
"""
Export functions for ArcGIS File Geodatabase (.gdb)
"""

import os
import shutil
from osgeo import ogr
from qgis.core import QgsProject, QgsFeatureRequest

from .field_mappings import (
    PUNKT_TO_COM_DOKU_PUNKT,
    ROHRMUFFE_TO_COM_DOKU_PUNKT,
    MESSPUNKT_TO_COM_DOKU_PUNKT,
    BAUTEN_TO_COM_DOKU_PUNKT,
    NETZTECHNIK_TO_COM_DOKU_PUNKT,
    ENDVERBRAUCHER_TO_COM_DOKU_PUNKT,
    LEERROHRE_TO_COM_DOKU_ROHR,
    VERBINDUNGEN_TO_COM_DOKU_KABEL,
    TEMPLATE_GDB_NAME,
    GDB_FEATURE_CLASSES,
)


class GDBExporter:
    """Handles export to ArcGIS File Geodatabase"""
    
    def __init__(self, plugin_dir):
        self.plugin_dir = plugin_dir
        self.template_gdb_path = os.path.join(plugin_dir, TEMPLATE_GDB_NAME)
        self.lookup_cache = {}
    
    def copy_template_gdb(self, output_folder, job_id):
        """Copy template geodatabase to output folder with job-specific name"""
        output_gdb_name = f'Job_{job_id}.gdb'
        output_gdb_path = os.path.join(output_folder, output_gdb_name)
        
        # Remove existing if present
        if os.path.exists(output_gdb_path):
            shutil.rmtree(output_gdb_path)
        
        # Copy template
        shutil.copytree(self.template_gdb_path, output_gdb_path)
        
        return output_gdb_path
    
    def build_lookup_cache(self, layer):
        """Build lookup cache for ValueRelation fields"""
        cache = {}
        for field in layer.fields():
            field_idx = layer.fields().indexFromName(field.name())
            widget_setup = layer.editorWidgetSetup(field_idx)
            if widget_setup.type() == 'ValueRelation':
                config = widget_setup.config()
                related_layer_name = config.get('Layer')
                key_field = config.get('Key')
                value_field = config.get('Value')
                
                # Find related layer
                related_layer = None
                for lyr in QgsProject.instance().mapLayers().values():
                    if lyr.id() == related_layer_name or lyr.name() == related_layer_name:
                        related_layer = lyr
                        break
                
                if related_layer:
                    lookup = {}
                    for feat in related_layer.getFeatures():
                        key = feat[key_field]
                        value = feat[value_field]
                        lookup[str(key)] = value
                    cache[field.name()] = lookup
        return cache
    
    def get_display_value(self, feature, field_name, cache):
        """Get display value for a field using cache"""
        raw_value = feature[field_name]
        if field_name in cache and raw_value is not None:
            return cache[field_name].get(str(raw_value), raw_value)
        return raw_value
    
    def export_punkt_to_gdb(self, job_id, gdb_path):
        """Export PUNKT layer to COM_DOKU_PUNKT feature class in geodatabase"""
        try:
            from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext
            from qgis.PyQt.QtCore import QVariant
            
            # Find PUNKT layer in QGIS
            target_layer = None
            for layer in QgsProject.instance().mapLayers().values():
                if layer.name().upper() == 'PUNKT':
                    target_layer = layer
                    break
            
            if not target_layer or not target_layer.isValid():
                return {'layer': 'PUNKT→GDB', 'success': False, 'error': 'PUNKT layer not found'}
            
            # Build lookup cache for display values
            cache = self.build_lookup_cache(target_layer)
            
            # Create a temporary memory layer with mapped field names
            fc_name = GDB_FEATURE_CLASSES['punkt']
            
            # Build fields for the output layer (using GDB field names)
            from qgis.core import QgsFields
            output_fields = QgsFields()
            for qgis_field_name, gdb_field_name in PUNKT_TO_COM_DOKU_PUNKT.items():
                # Find original field to get its type
                original_field_idx = target_layer.fields().indexFromName(qgis_field_name)
                if original_field_idx >= 0:
                    original_field = target_layer.fields().field(original_field_idx)
                    # Check if it's a ValueRelation - make it string
                    widget_setup = target_layer.editorWidgetSetup(original_field_idx)
                    if widget_setup.type() == 'ValueRelation':
                        new_field = QgsField(gdb_field_name, QVariant.String, 'String', 254)
                    else:
                        new_field = QgsField(gdb_field_name, original_field.type(), original_field.typeName(), original_field.length(), original_field.precision())
                    output_fields.append(new_field)
            
            # Create memory layer
            mem_layer = QgsVectorLayer(f"Point?crs={target_layer.crs().authid()}", "temp_punkt_gdb", "memory")
            mem_layer.dataProvider().addAttributes(output_fields)
            mem_layer.updateFields()
            mem_layer.startEditing()
            
            # Get features filtered by job_id
            request = QgsFeatureRequest().setFilterExpression(f'job_id = {job_id}')
            feature_count = 0
            
            for qgis_feature in target_layer.getFeatures(request):
                new_feature = QgsFeature(mem_layer.fields())
                new_feature.setGeometry(qgis_feature.geometry())
                
                # Map fields with display values
                for qgis_field_name, gdb_field_name in PUNKT_TO_COM_DOKU_PUNKT.items():
                    try:
                        value = self.get_display_value(qgis_feature, qgis_field_name, cache)
                        if value is not None:
                            new_feature[gdb_field_name] = value
                    except:
                        pass
                
                mem_layer.addFeature(new_feature)
                feature_count += 1
            
            mem_layer.commitChanges()
            
            # Write to geodatabase using append mode
            output_path = f"{gdb_path}|layername={fc_name}"
            
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'OpenFileGDB'
            options.layerName = fc_name
            options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                mem_layer,
                gdb_path,
                QgsCoordinateTransformContext(),
                options
            )
            
            if error[0] == QgsVectorFileWriter.NoError:
                return {
                    'layer': 'PUNKT→GDB',
                    'count': feature_count,
                    'file': f'{gdb_path}\\{fc_name}',
                    'success': True
                }
            else:
                return {'layer': 'PUNKT→GDB', 'success': False, 'error': f'Write error: {error[1]}'}
            
        except Exception as e:
            return {'layer': 'PUNKT→GDB', 'success': False, 'error': str(e)}
    
    def export_rohrmuffe_to_gdb(self, job_id, gdb_path):
        """Export ROHRMUFFE layer to COM_DOKU_PUNKT feature class in geodatabase"""
        try:
            from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsFields
            from qgis.PyQt.QtCore import QVariant
            
            # Find ROHRMUFFE layer in QGIS
            target_layer = None
            for layer in QgsProject.instance().mapLayers().values():
                if layer.name().upper() == 'ROHRMUFFE':
                    target_layer = layer
                    break
            
            if not target_layer or not target_layer.isValid():
                return {'layer': 'ROHRMUFFE→GDB', 'success': False, 'error': 'ROHRMUFFE layer not found'}
            
            # Build lookup cache for display values
            cache = self.build_lookup_cache(target_layer)
            
            fc_name = GDB_FEATURE_CLASSES['punkt']  # Goes to COM_DOKU_PUNKT
            
            # Build fields for the output layer (using GDB field names)
            output_fields = QgsFields()
            for qgis_field_name, gdb_field_name in ROHRMUFFE_TO_COM_DOKU_PUNKT.items():
                original_field_idx = target_layer.fields().indexFromName(qgis_field_name)
                if original_field_idx >= 0:
                    original_field = target_layer.fields().field(original_field_idx)
                    widget_setup = target_layer.editorWidgetSetup(original_field_idx)
                    if widget_setup.type() == 'ValueRelation':
                        new_field = QgsField(gdb_field_name, QVariant.String, 'String', 254)
                    else:
                        new_field = QgsField(gdb_field_name, original_field.type(), original_field.typeName(), original_field.length(), original_field.precision())
                    output_fields.append(new_field)
            
            # Create memory layer
            mem_layer = QgsVectorLayer(f"Point?crs={target_layer.crs().authid()}", "temp_rohrmuffe_gdb", "memory")
            mem_layer.dataProvider().addAttributes(output_fields)
            mem_layer.updateFields()
            mem_layer.startEditing()
            
            # Get features filtered by job_id
            request = QgsFeatureRequest().setFilterExpression(f'job_id = {job_id}')
            feature_count = 0
            
            for qgis_feature in target_layer.getFeatures(request):
                new_feature = QgsFeature(mem_layer.fields())
                new_feature.setGeometry(qgis_feature.geometry())
                
                for qgis_field_name, gdb_field_name in ROHRMUFFE_TO_COM_DOKU_PUNKT.items():
                    try:
                        value = self.get_display_value(qgis_feature, qgis_field_name, cache)
                        if value is not None:
                            new_feature[gdb_field_name] = value
                    except:
                        pass
                
                mem_layer.addFeature(new_feature)
                feature_count += 1
            
            mem_layer.commitChanges()
            
            # Write to geodatabase using append mode
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'OpenFileGDB'
            options.layerName = fc_name
            options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                mem_layer,
                gdb_path,
                QgsCoordinateTransformContext(),
                options
            )
            
            if error[0] == QgsVectorFileWriter.NoError:
                return {
                    'layer': 'ROHRMUFFE→GDB',
                    'count': feature_count,
                    'file': f'{gdb_path}\\{fc_name}',
                    'success': True
                }
            else:
                return {'layer': 'ROHRMUFFE→GDB', 'success': False, 'error': f'Write error: {error[1]}'}
            
        except Exception as e:
            return {'layer': 'ROHRMUFFE→GDB', 'success': False, 'error': str(e)}
    
    def export_messpunkt_to_gdb(self, job_id, gdb_path):
        """Export MESSPUNKT layer to COM_DOKU_PUNKT feature class in geodatabase"""
        try:
            from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsFields
            from qgis.PyQt.QtCore import QVariant
            
            target_layer = None
            for layer in QgsProject.instance().mapLayers().values():
                if layer.name().upper() == 'MESSPUNKT':
                    target_layer = layer
                    break
            
            if not target_layer or not target_layer.isValid():
                return {'layer': 'MESSPUNKT→GDB', 'success': False, 'error': 'MESSPUNKT layer not found'}
            
            cache = self.build_lookup_cache(target_layer)
            fc_name = GDB_FEATURE_CLASSES['punkt']
            
            output_fields = QgsFields()
            for qgis_field_name, gdb_field_name in MESSPUNKT_TO_COM_DOKU_PUNKT.items():
                original_field_idx = target_layer.fields().indexFromName(qgis_field_name)
                if original_field_idx >= 0:
                    original_field = target_layer.fields().field(original_field_idx)
                    widget_setup = target_layer.editorWidgetSetup(original_field_idx)
                    if widget_setup.type() == 'ValueRelation':
                        new_field = QgsField(gdb_field_name, QVariant.String, 'String', 254)
                    else:
                        new_field = QgsField(gdb_field_name, original_field.type(), original_field.typeName(), original_field.length(), original_field.precision())
                    output_fields.append(new_field)
            
            mem_layer = QgsVectorLayer(f"Point?crs={target_layer.crs().authid()}", "temp_messpunkt_gdb", "memory")
            mem_layer.dataProvider().addAttributes(output_fields)
            mem_layer.updateFields()
            mem_layer.startEditing()
            
            request = QgsFeatureRequest().setFilterExpression(f'job_id = {job_id}')
            feature_count = 0
            
            for qgis_feature in target_layer.getFeatures(request):
                new_feature = QgsFeature(mem_layer.fields())
                new_feature.setGeometry(qgis_feature.geometry())
                
                for qgis_field_name, gdb_field_name in MESSPUNKT_TO_COM_DOKU_PUNKT.items():
                    try:
                        value = self.get_display_value(qgis_feature, qgis_field_name, cache)
                        if value is not None:
                            new_feature[gdb_field_name] = value
                    except:
                        pass
                
                mem_layer.addFeature(new_feature)
                feature_count += 1
            
            mem_layer.commitChanges()
            
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'OpenFileGDB'
            options.layerName = fc_name
            options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(mem_layer, gdb_path, QgsCoordinateTransformContext(), options)
            
            if error[0] == QgsVectorFileWriter.NoError:
                return {'layer': 'MESSPUNKT→GDB', 'count': feature_count, 'file': f'{gdb_path}\\{fc_name}', 'success': True}
            else:
                return {'layer': 'MESSPUNKT→GDB', 'success': False, 'error': f'Write error: {error[1]}'}
            
        except Exception as e:
            return {'layer': 'MESSPUNKT→GDB', 'success': False, 'error': str(e)}
    
    def export_bauten_to_gdb(self, job_id, gdb_path):
        """Export BAUTEN layer to COM_DOKU_PUNKT feature class in geodatabase"""
        try:
            from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsFields
            from qgis.PyQt.QtCore import QVariant
            
            target_layer = None
            for layer in QgsProject.instance().mapLayers().values():
                if layer.name().upper() == 'BAUTEN':
                    target_layer = layer
                    break
            
            if not target_layer or not target_layer.isValid():
                return {'layer': 'BAUTEN→GDB', 'success': False, 'error': 'BAUTEN layer not found'}
            
            cache = self.build_lookup_cache(target_layer)
            fc_name = GDB_FEATURE_CLASSES['punkt']
            
            output_fields = QgsFields()
            for qgis_field_name, gdb_field_name in BAUTEN_TO_COM_DOKU_PUNKT.items():
                original_field_idx = target_layer.fields().indexFromName(qgis_field_name)
                if original_field_idx >= 0:
                    original_field = target_layer.fields().field(original_field_idx)
                    widget_setup = target_layer.editorWidgetSetup(original_field_idx)
                    if widget_setup.type() == 'ValueRelation':
                        new_field = QgsField(gdb_field_name, QVariant.String, 'String', 254)
                    else:
                        new_field = QgsField(gdb_field_name, original_field.type(), original_field.typeName(), original_field.length(), original_field.precision())
                    output_fields.append(new_field)
            
            mem_layer = QgsVectorLayer(f"Point?crs={target_layer.crs().authid()}", "temp_bauten_gdb", "memory")
            mem_layer.dataProvider().addAttributes(output_fields)
            mem_layer.updateFields()
            mem_layer.startEditing()
            
            request = QgsFeatureRequest().setFilterExpression(f'job_id = {job_id}')
            feature_count = 0
            
            for qgis_feature in target_layer.getFeatures(request):
                new_feature = QgsFeature(mem_layer.fields())
                new_feature.setGeometry(qgis_feature.geometry())
                
                for qgis_field_name, gdb_field_name in BAUTEN_TO_COM_DOKU_PUNKT.items():
                    try:
                        value = self.get_display_value(qgis_feature, qgis_field_name, cache)
                        if value is not None:
                            new_feature[gdb_field_name] = value
                    except:
                        pass
                
                # Special logic: if ART='Sonstiges', use ART_SONST value
                art_value = new_feature['ART']
                if art_value and art_value in ('Sonstiges', 'Sonstige'):
                    art_sonst = qgis_feature['ART_SONST']
                    if art_sonst:
                        new_feature['ART'] = art_sonst
                
                mem_layer.addFeature(new_feature)
                feature_count += 1
            
            mem_layer.commitChanges()
            
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'OpenFileGDB'
            options.layerName = fc_name
            options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(mem_layer, gdb_path, QgsCoordinateTransformContext(), options)
            
            if error[0] == QgsVectorFileWriter.NoError:
                return {'layer': 'BAUTEN→GDB', 'count': feature_count, 'file': f'{gdb_path}\\{fc_name}', 'success': True}
            else:
                return {'layer': 'BAUTEN→GDB', 'success': False, 'error': f'Write error: {error[1]}'}
            
        except Exception as e:
            return {'layer': 'BAUTEN→GDB', 'success': False, 'error': str(e)}
    
    def export_netztechnik_to_gdb(self, job_id, gdb_path):
        """Export NETZTECHNIK layer to COM_DOKU_PUNKT feature class in geodatabase"""
        try:
            from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsFields
            from qgis.PyQt.QtCore import QVariant
            
            target_layer = None
            for layer in QgsProject.instance().mapLayers().values():
                if layer.name().upper() == 'NETZTECHNIK':
                    target_layer = layer
                    break
            
            if not target_layer or not target_layer.isValid():
                return {'layer': 'NETZTECHNIK→GDB', 'success': False, 'error': 'NETZTECHNIK layer not found'}
            
            cache = self.build_lookup_cache(target_layer)
            fc_name = GDB_FEATURE_CLASSES['punkt']
            
            output_fields = QgsFields()
            for qgis_field_name, gdb_field_name in NETZTECHNIK_TO_COM_DOKU_PUNKT.items():
                original_field_idx = target_layer.fields().indexFromName(qgis_field_name)
                if original_field_idx >= 0:
                    original_field = target_layer.fields().field(original_field_idx)
                    widget_setup = target_layer.editorWidgetSetup(original_field_idx)
                    if widget_setup.type() == 'ValueRelation':
                        new_field = QgsField(gdb_field_name, QVariant.String, 'String', 254)
                    else:
                        new_field = QgsField(gdb_field_name, original_field.type(), original_field.typeName(), original_field.length(), original_field.precision())
                    output_fields.append(new_field)
            
            mem_layer = QgsVectorLayer(f"Point?crs={target_layer.crs().authid()}", "temp_netztechnik_gdb", "memory")
            mem_layer.dataProvider().addAttributes(output_fields)
            mem_layer.updateFields()
            mem_layer.startEditing()
            
            request = QgsFeatureRequest().setFilterExpression(f'job_id = {job_id}')
            feature_count = 0
            
            for qgis_feature in target_layer.getFeatures(request):
                new_feature = QgsFeature(mem_layer.fields())
                new_feature.setGeometry(qgis_feature.geometry())
                
                for qgis_field_name, gdb_field_name in NETZTECHNIK_TO_COM_DOKU_PUNKT.items():
                    try:
                        value = self.get_display_value(qgis_feature, qgis_field_name, cache)
                        if value is not None:
                            new_feature[gdb_field_name] = value
                    except:
                        pass
                
                # Special logic: if ART='Sonstige', use ART_SONST value
                art_value = new_feature['ART']
                if art_value and art_value in ('Sonstiges', 'Sonstige'):
                    art_sonst = qgis_feature['ART_SONST']
                    if art_sonst:
                        new_feature['ART'] = art_sonst
                
                mem_layer.addFeature(new_feature)
                feature_count += 1
            
            mem_layer.commitChanges()
            
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'OpenFileGDB'
            options.layerName = fc_name
            options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(mem_layer, gdb_path, QgsCoordinateTransformContext(), options)
            
            if error[0] == QgsVectorFileWriter.NoError:
                return {'layer': 'NETZTECHNIK→GDB', 'count': feature_count, 'file': f'{gdb_path}\\{fc_name}', 'success': True}
            else:
                return {'layer': 'NETZTECHNIK→GDB', 'success': False, 'error': f'Write error: {error[1]}'}
            
        except Exception as e:
            return {'layer': 'NETZTECHNIK→GDB', 'success': False, 'error': str(e)}
    
    def export_endverbraucher_to_gdb(self, job_id, gdb_path):
        """Export ENDVERBRAUCHER layer to COM_DOKU_PUNKT feature class in geodatabase"""
        try:
            from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsFields
            from qgis.PyQt.QtCore import QVariant
            
            target_layer = None
            for layer in QgsProject.instance().mapLayers().values():
                if layer.name().upper() == 'ENDVERBRAUCHER':
                    target_layer = layer
                    break
            
            if not target_layer or not target_layer.isValid():
                return {'layer': 'ENDVERBRAUCHER→GDB', 'success': False, 'error': 'ENDVERBRAUCHER layer not found'}
            
            cache = self.build_lookup_cache(target_layer)
            fc_name = GDB_FEATURE_CLASSES['punkt']
            
            output_fields = QgsFields()
            for qgis_field_name, gdb_field_name in ENDVERBRAUCHER_TO_COM_DOKU_PUNKT.items():
                original_field_idx = target_layer.fields().indexFromName(qgis_field_name)
                if original_field_idx >= 0:
                    original_field = target_layer.fields().field(original_field_idx)
                    widget_setup = target_layer.editorWidgetSetup(original_field_idx)
                    if widget_setup.type() == 'ValueRelation':
                        new_field = QgsField(gdb_field_name, QVariant.String, 'String', 254)
                    else:
                        new_field = QgsField(gdb_field_name, original_field.type(), original_field.typeName(), original_field.length(), original_field.precision())
                    output_fields.append(new_field)
            
            mem_layer = QgsVectorLayer(f"Point?crs={target_layer.crs().authid()}", "temp_endverbraucher_gdb", "memory")
            mem_layer.dataProvider().addAttributes(output_fields)
            mem_layer.updateFields()
            mem_layer.startEditing()
            
            request = QgsFeatureRequest().setFilterExpression(f'job_id = {job_id}')
            feature_count = 0
            
            for qgis_feature in target_layer.getFeatures(request):
                new_feature = QgsFeature(mem_layer.fields())
                new_feature.setGeometry(qgis_feature.geometry())
                
                for qgis_field_name, gdb_field_name in ENDVERBRAUCHER_TO_COM_DOKU_PUNKT.items():
                    try:
                        value = self.get_display_value(qgis_feature, qgis_field_name, cache)
                        if value is not None:
                            new_feature[gdb_field_name] = value
                    except:
                        pass
                
                mem_layer.addFeature(new_feature)
                feature_count += 1
            
            mem_layer.commitChanges()
            
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'OpenFileGDB'
            options.layerName = fc_name
            options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(mem_layer, gdb_path, QgsCoordinateTransformContext(), options)
            
            if error[0] == QgsVectorFileWriter.NoError:
                return {'layer': 'ENDVERBRAUCHER→GDB', 'count': feature_count, 'file': f'{gdb_path}\\{fc_name}', 'success': True}
            else:
                return {'layer': 'ENDVERBRAUCHER→GDB', 'success': False, 'error': f'Write error: {error[1]}'}
            
        except Exception as e:
            return {'layer': 'ENDVERBRAUCHER→GDB', 'success': False, 'error': str(e)}
    
    def export_leerrohre_to_gdb(self, job_id, gdb_path):
        """Export Leerrohre layer to COM_DOKU_ROHR feature class in geodatabase"""
        try:
            from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsFields
            from qgis.PyQt.QtCore import QVariant
            
            target_layer = None
            for layer in QgsProject.instance().mapLayers().values():
                if 'leerrohr' in layer.name().lower():
                    target_layer = layer
                    break
            
            if not target_layer or not target_layer.isValid():
                return {'layer': 'Leerrohre→GDB', 'success': False, 'error': 'Leerrohre layer not found'}
            
            cache = self.build_lookup_cache(target_layer)
            fc_name = GDB_FEATURE_CLASSES['rohr']
            
            # Build output fields
            output_fields = QgsFields()
            for qgis_field_name, gdb_field_name in LEERROHRE_TO_COM_DOKU_ROHR.items():
                original_field_idx = target_layer.fields().indexFromName(qgis_field_name)
                if original_field_idx >= 0:
                    original_field = target_layer.fields().field(original_field_idx)
                    widget_setup = target_layer.editorWidgetSetup(original_field_idx)
                    if widget_setup.type() == 'ValueRelation':
                        new_field = QgsField(gdb_field_name, QVariant.String, 'String', 254)
                    else:
                        new_field = QgsField(gdb_field_name, original_field.type(), original_field.typeName(), original_field.length(), original_field.precision())
                    output_fields.append(new_field)
            
            # Add LR_FARBE field (handled separately)
            output_fields.append(QgsField('LR_FARBE', QVariant.String, 'String', 254))
            
            # Create memory layer (LineString)
            mem_layer = QgsVectorLayer(f"LineString?crs={target_layer.crs().authid()}", "temp_leerrohre_gdb", "memory")
            mem_layer.dataProvider().addAttributes(output_fields)
            mem_layer.updateFields()
            mem_layer.startEditing()
            
            request = QgsFeatureRequest().setFilterExpression(f'job_id = {job_id}')
            feature_count = 0
            
            for qgis_feature in target_layer.getFeatures(request):
                new_feature = QgsFeature(mem_layer.fields())
                new_feature.setGeometry(qgis_feature.geometry())
                
                # First calculate LR_FARBE based on TYP
                typ_value = self.get_display_value(qgis_feature, 'TYP', cache)
                lr_farbe_value = None
                if typ_value:
                    typ_str = str(typ_value).lower()
                    if 'schutzrohr' in typ_str or 'rohrverband' in typ_str:
                        # Use M_FARB, but if Sonstige use M_FARB_SON
                        lr_farbe_value = self.get_display_value(qgis_feature, 'M_FARB', cache)
                        if lr_farbe_value and str(lr_farbe_value) in ('Sonstige', 'Sonstiges'):
                            lr_farbe_value = qgis_feature['M_FARB_SON']
                    elif 'einzelrohr' in typ_str:
                        # Use ER_FARB, but if Sonstige use ER_FARB_SON
                        lr_farbe_value = self.get_display_value(qgis_feature, 'ER_FARB', cache)
                        if lr_farbe_value and str(lr_farbe_value) in ('Sonstige', 'Sonstiges'):
                            lr_farbe_value = qgis_feature['ER_FARB_SON']
                
                # Map regular fields
                for qgis_field_name, gdb_field_name in LEERROHRE_TO_COM_DOKU_ROHR.items():
                    try:
                        value = self.get_display_value(qgis_feature, qgis_field_name, cache)
                        if value is not None:
                            new_feature[gdb_field_name] = value
                    except:
                        pass
                
                # Special logic for LR_HERST - if Sonstige, use LR_HER_SON
                lr_herst_value = new_feature['LR_HERST'] if 'LR_HERST' in [f.name() for f in mem_layer.fields()] else None
                if lr_herst_value and str(lr_herst_value) in ('Sonstige', 'Sonstiges'):
                    new_feature['LR_HERST'] = qgis_feature['LR_HER_SON']
                
                # Set LR_FARBE
                if lr_farbe_value:
                    new_feature['LR_FARBE'] = lr_farbe_value
                
                mem_layer.addFeature(new_feature)
                feature_count += 1
            
            mem_layer.commitChanges()
            
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'OpenFileGDB'
            options.layerName = fc_name
            options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(mem_layer, gdb_path, QgsCoordinateTransformContext(), options)
            
            if error[0] == QgsVectorFileWriter.NoError:
                return {'layer': 'Leerrohre→GDB', 'count': feature_count, 'file': f'{gdb_path}\\{fc_name}', 'success': True}
            else:
                return {'layer': 'Leerrohre→GDB', 'success': False, 'error': f'Write error: {error[1]}'}
            
        except Exception as e:
            return {'layer': 'Leerrohre→GDB', 'success': False, 'error': str(e)}
    
    def export_verbindungen_to_gdb(self, job_id, gdb_path):
        """Export Verbindungen layer to COM_DOKU_KABEL feature class in geodatabase"""
        try:
            from qgis.core import QgsVectorLayer, QgsFeature, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsFields
            from qgis.PyQt.QtCore import QVariant
            
            target_layer = None
            for layer in QgsProject.instance().mapLayers().values():
                if 'verbindung' in layer.name().lower():
                    target_layer = layer
                    break
            
            if not target_layer or not target_layer.isValid():
                return {'layer': 'Verbindungen→GDB', 'success': False, 'error': 'Verbindungen layer not found'}
            
            cache = self.build_lookup_cache(target_layer)
            fc_name = GDB_FEATURE_CLASSES['kabel']
            
            # Build output fields
            output_fields = QgsFields()
            for qgis_field_name, gdb_field_name in VERBINDUNGEN_TO_COM_DOKU_KABEL.items():
                original_field_idx = target_layer.fields().indexFromName(qgis_field_name)
                if original_field_idx >= 0:
                    original_field = target_layer.fields().field(original_field_idx)
                    widget_setup = target_layer.editorWidgetSetup(original_field_idx)
                    if widget_setup.type() == 'ValueRelation':
                        new_field = QgsField(gdb_field_name, QVariant.String, 'String', 254)
                    else:
                        new_field = QgsField(gdb_field_name, original_field.type(), original_field.typeName(), original_field.length(), original_field.precision())
                    output_fields.append(new_field)
            
            # Add LR_FARBE field (handled separately)
            output_fields.append(QgsField('LR_FARBE', QVariant.String, 'String', 254))
            
            # Create memory layer (LineString)
            mem_layer = QgsVectorLayer(f"LineString?crs={target_layer.crs().authid()}", "temp_verbindungen_gdb", "memory")
            mem_layer.dataProvider().addAttributes(output_fields)
            mem_layer.updateFields()
            mem_layer.startEditing()
            
            request = QgsFeatureRequest().setFilterExpression(f'job_id = {job_id}')
            feature_count = 0
            
            for qgis_feature in target_layer.getFeatures(request):
                new_feature = QgsFeature(mem_layer.fields())
                new_feature.setGeometry(qgis_feature.geometry())
                
                # Map regular fields
                for qgis_field_name, gdb_field_name in VERBINDUNGEN_TO_COM_DOKU_KABEL.items():
                    try:
                        value = self.get_display_value(qgis_feature, qgis_field_name, cache)
                        if value is not None:
                            new_feature[gdb_field_name] = value
                    except:
                        pass
                
                # Special logic for ART (VERB_ART) - if Sonstige use V_A_SONST
                art_value = new_feature['ART'] if 'ART' in [f.name() for f in mem_layer.fields()] else None
                if art_value and str(art_value) in ('Sonstige', 'Sonstiges'):
                    new_feature['ART'] = qgis_feature['V_A_SONST']
                
                # Special logic for LR_FARBE - use ER_FARB, if Sonstige use ER_FARB_SON
                lr_farbe_value = self.get_display_value(qgis_feature, 'ER_FARB', cache)
                if lr_farbe_value and str(lr_farbe_value) in ('Sonstige', 'Sonstiges'):
                    lr_farbe_value = qgis_feature['ER_FARB_SON']
                if lr_farbe_value:
                    new_feature['LR_FARBE'] = lr_farbe_value
                
                mem_layer.addFeature(new_feature)
                feature_count += 1
            
            mem_layer.commitChanges()
            
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = 'OpenFileGDB'
            options.layerName = fc_name
            options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(mem_layer, gdb_path, QgsCoordinateTransformContext(), options)
            
            if error[0] == QgsVectorFileWriter.NoError:
                return {'layer': 'Verbindungen→GDB', 'count': feature_count, 'file': f'{gdb_path}\\{fc_name}', 'success': True}
            else:
                return {'layer': 'Verbindungen→GDB', 'success': False, 'error': f'Write error: {error[1]}'}
            
        except Exception as e:
            return {'layer': 'Verbindungen→GDB', 'success': False, 'error': str(e)}

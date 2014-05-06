__all__ = ['compile', 'dumps']

import xml.etree.ElementTree as ET
from xml.dom import minidom
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from .models import Document, Reference, Collection


def compile(obj, xml_tag=None):
    """Compile obj into an ElementTree.
    """

    root = ET.Element(xml_tag or obj.xml_tag)
    for key, value in obj.children():
        if isinstance(value, Reference):
            node = ET.SubElement(root, key)
            for k, v in value.get_reference().items():
                ET.SubElement(node, k).text = str(v)
        elif isinstance(value, (Collection, set, list, tuple)):
            if len(value) or getattr(value, 'allow_empty', False):
                node = ET.SubElement(root, key)
                try:
                    sub_xml_tag = obj._fields[key].xml_tag
                except KeyError:
                    sub_xml_tag = None
                for element in value:
                    node.append(compile(element, sub_xml_tag))
        elif value is not None or getattr(value, 'allow_empty', False):
            node = ET.SubElement(root, key)
            node.text = str(value)
    return root


def dumps(obj):
    """Convert obj into an xml string.
    """

    root = compile(obj)
    document = ET.ElementTree(root)
    flow = StringIO()
    document.write(flow, encoding='utf-8', xml_declaration=True)
    contents = flow.getvalue()
    flow.close()

    return minidom.parseString(contents).toprettyxml(indent="  ")

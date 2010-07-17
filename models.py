#!/usr/bin/python
# -*- coding: utf-8 -*-

import pycurl
from StringIO import StringIO
from xml.dom import minidom
from django.conf import settings
from django.db import models
from django import forms
from django.utils.encoding import smart_str

class NuxeoConnection(models.Model):
    """
    """
    URL_BASE = settings.NUXEO_BASE
    LOGIN_URL = URL_BASE + 'nxstartup.faces'
    
    def __init__(self):
        self.curl = pycurl.Curl()
    
    def login(self,username,pwd):
        """
        Metodo para hacer login en Nuxeo
        """
        self.curl.setopt(pycurl.URL, self.LOGIN_URL)
        self.curl.setopt(pycurl.VERBOSE,1)
        self.curl.setopt(pycurl.POST, 1)
        self.curl.setopt(pycurl.POSTFIELDS,"user_name=%s&user_password=%s&form_submitted_marker=1" % (username,pwd))
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)  
        self.curl.setopt(pycurl.COOKIEJAR, "nuxeo_connect.txt")
        self.curl.setopt(pycurl.COOKIEFILE, "nuxeo_connect.txt")
        try:
           self.curl.perform()
        except:
           if not settings.DEBUG:
              raise
        self.user = username
    
    def get_xml(self,url):
        """
        """
        file = StringIO()
        self.curl.setopt(pycurl.WRITEFUNCTION, file.write)
        self.curl.setopt(pycurl.URL, url)
        self.curl.perform()
        file2 = StringIO(file.getvalue().replace('\n','').replace("UTF-8", "iso-8859-1"))
        file.close()
        
        return file2
    
    def get_by_attr(self,attrs):
        """
        Se obtine un fichero xml con los objetos en los
        que coincida el valor de un atributo determinado
        Lista de posibles atributos: fulltext_all, fulltext_phrase, fulltext_one_of,
        fulltext_none, isCheckedInVersion, searchpath, title, description, rights,
        source, coverage, created_min, created_max, modified_min, modified_max,
        issued_min, issued_max, valid_min, valid_max, expired_min, expired_max,
        format, language, currentLifeCycleStates 
        """
        import urllib
        from django.utils.encoding import smart_str
        
        url = self.URL_BASE + "restAPI/execQueryModel/ADVANCED_SEARCH?format=XML&"
        for attr,value in attrs:
            value_url = urllib.quote_plus(smart_str(value))
            param = "&advanced_search:%s=%s" % (attr,value_url)
            url += param
            
        file = self.get_xml(url)
        
        return file
    
    def get_nodos(self,file):
        """
        Devuelve los nodos de un archivo XML
        """
        res = []
        if file.getvalue():            
            docxml =  minidom.parse(file)
            nodes = docxml.childNodes
        
            for child in nodes:
               childs = child.childNodes
               for child2 in childs:
                   if child2.nodeName != 'document':
                       continue
                   res.append(child2)
        
        file.close()
        return res
    
    def get_url_nodo(self,nodo):
        """
        Devuelve la url de un nodo. Si es un fichero se devuelve
        la url de descarga, si no lo es la url de visualización
        """
        from django.core.urlresolvers import reverse
        
        tipo = nodo.getAttribute('type')
        id_nodo = nodo.getAttribute('id')
        urlview = self.URL_BASE + "nxdoc%s/view_documents?tabId=&conversationId=0NXMAIN&conversationIsLongRunning=true"
        url = urlview % nodo.getAttribute('url')
        
        if tipo == 'File':
            #url = self.URL_BASE + "restAPI/default/%s/downloadFile" % id_nodo      
            url = "/descarga_imagen/" + str(id_nodo) #reverse('descarga_imagen',args=[id_nodo])
        
        return url
   
    def get_title(self, id):
        """
        Devuelve el titulo de un documento o carpeta.
        """
        export_url = self.URL_BASE + "restAPI/default/%s/browse" % str(id)
        file = self.get_xml(export_url)
        docxml =  minidom.parse(file)
        title = docxml.childNodes
        title = title[0].getAttribute('title')
        return title
        file.close()
        return res
 
    def get_id(self,titulo):
        """
        Devuelve el id de un documento a partir de su titulo
        """
        file = self.get_by_attr([('title',titulo)])
        nodos = self.get_nodos(file)
        res = ''
        
        if len(nodos) == 1:     
            res = nodos[0].getAttribute('id')
        file.close()
        return res

    def get_docs_rec(self,carpeta=None, id=None, nivel=1):
        """
        Devuelve todos los documentos de una carpeta
        """

        if not id:
            id_carp = self.get_id(carpeta)
        else:
            id_carp = id
        url = self.URL_BASE + "restAPI/default/%s/browse" % str(id_carp)
        file = self.get_xml(url)
        nodos = self.get_nodos(file)
        docs = []

        for nodo in nodos:
            title = nodo.getAttribute("title")
            url = self.get_url_nodo(nodo)
            id = nodo.getAttribute('id')
            type = nodo.getAttribute('type')
            if type == "Ficha":
                doc = {'url': url, 'titulo': title, 'id': id}
                doc['info'] = self.get_file_info(id)[0]
                docs.append(doc)
            elif type == "Section":
                nivel -= 1
                docs = docs + self.get_docs_rec(id=id, nivel=nivel) 
        return docs
        
    def get_docs(self,carpeta=None, id=None):
        """
        Devuelve todos los documentos de una carpeta
        """  
  
	if not id:
            id_carp = self.get_id(carpeta)
	else:
	    id_carp = id
        url = self.URL_BASE + "restAPI/default/%s/browse" % str(id_carp)
        file = self.get_xml(url)
        nodos = self.get_nodos(file)
        docs = []
        
        for nodo in nodos:
            title = nodo.getAttribute("title")
            url = self.get_url_nodo(nodo)
            id = nodo.getAttribute('id')
            doc = {'url': url, 'titulo': title, 'id': id}
            doc['info'] = self.get_file_info(id)[0]
            docs.append(doc)
        return docs
 
    def get_xml_dublin_core(self,childs):
        dublin_core = {}
        for child in childs:
             if str(child.nodeName) != "#text":
                if child.nodeValue == None:
                   if len(child.childNodes) > 0:
                      dublin_core[str(child.nodeName)[3:]] = smart_str(child.childNodes[0].nodeValue,'iso-8859-1')
                   else:
                      dublin_core[str(child.nodeName)[3:]] = ''
             
        return dublin_core

    def get_xml_ficha(self,childs):
        ficha = {}
        for child in childs:
             if str(child.nodeName) != "#text":
                if child.nodeValue == None:
                   if len(child.childNodes) > 0:
                      ficha[str(child.nodeName)[3:]] = smart_str(child.childNodes[0].nodeValue,'iso-8859-1')
                   else:
                      ficha[str(child.nodeName)[3:]] = ''

        return ficha
 
    def get_xml_file_schema(self, childs):
        info = {}
        info['filename'] = ''
        info['mimetype'] = ''
        for child in childs:
            if child.nodeName == 'content':
                for child2 in child.childNodes:
                    if child2.nodeName == 'mime-type':
                        info['mimetype'] = child2.childNodes[0].nodeValue
                    if child.nodeName == 'filename':
                        info['filename'] = smart_str(child.childNodes[0].nodeValue,'iso-8859-1')
        return info
 
    def get_xml_attachments(self, nodes):
        attachments = []
        index = 0
        for child in nodes:
            for child2 in child.childNodes:
               if child2.nodeName == "item":
                  attachment = {}
                  for child3 in child2.childNodes:
                     if child3.nodeName == "filename":
                        attachment['filename'] = child3.childNodes[0].nodeValue
                        attachment['index'] = index
                        index += 1
                     if child3.nodeName == "file":
                        for child4 in child3.childNodes:
                           print child4.nodeName
                           if child4.nodeName == "mime-type":
                              attachment['mimetype'] = str(child4.childNodes[0].nodeValue)
                  attachments.append(attachment)
               
            
        return attachments
        
    def get_xml_file_info(self,file):
        """
        """
        from django.utils.encoding import smart_str
        
        info = {}
        if file.getvalue():            
            docxml =  minidom.parse(file)
            nodes = docxml.childNodes
            if nodes:
                doc = nodes[0]
                nodes_doc = doc.childNodes
                for node in nodes_doc:
                    if node.nodeName == '#text':
                        continue
                    if node.getAttribute('name') == 'file':
                       childs = node.childNodes
                       info['fileschema'] = self.get_xml_file_schema(node.childNodes)
                    if node.getAttribute('name') == 'dublincore':
                       childs = node.childNodes
                       info['dublincore'] = self.get_xml_dublin_core(node.childNodes)
                    if node.getAttribute('name') == 'ficha':
                       childs = node.childNodes
                       info['ficha'] = childs[0]
                    if node.getAttribute('name') == 'files':
                       childs = node.childNodes
                       info['attachments'] = self.get_xml_attachments(node.childNodes)
                    if node.getAttribute('name') == 'ficha':
                       childs = node.childNodes
                       info['ficha'] = self.get_xml_ficha(node.childNodes)
                    
        return info


    def get_file_info(self, id):
        """
        """
        export_url = self.URL_BASE + "restAPI/default/%s/export?format=XML" % str(id)
        file = self.get_xml(export_url)
        info = self.get_xml_file_info(file)
        return info, str(file)

    def get_imagen(self,id):
        """
        Devuelve un objeto HttpResponse con un fichero determinado
        """
        from django.http import HttpResponse
        export_url = self.URL_BASE + "restAPI/default/%s/export?format=XML" % str(id)
        file = self.get_xml(export_url)
        info = self.get_xml_file_info(file)['fileschema']

        response = HttpResponse()
        url = self.URL_BASE + "nxfile/default/%s/blobholder:0/%s" % (str(id), str(info.get('filename')))
        self.curl.setopt(pycurl.URL, str(url))
        self.curl.setopt(pycurl.WRITEFUNCTION, response.write)
        self.curl.perform()

        response['Content-Disposition'] = 'attachment; filename="%s"' % info.get('filename')
        response['Content-Type'] = info.get('mimetype')

        return response
        
    def get_adjunto(self,id, indice):
        """
        Devuelve un objeto HttpResponse con un fichero determinado
        """
        from django.http import HttpResponse
        export_url = self.URL_BASE + "restAPI/default/%s/export?format=XML" % str(id)
        file = self.get_xml(export_url)
        info = self.get_xml_file_info(file)
        info = info['attachments'][indice]

        response = HttpResponse()
        url = self.URL_BASE + "nxfile/default/%s/files:files/%s/file/%s" % (str(id), str(indice), info['filename'].replace(' ', '%20'))
        self.curl.setopt(pycurl.URL, str(url))
        self.curl.setopt(pycurl.WRITEFUNCTION, response.write)
        self.curl.perform()

        response['Content-Disposition'] = 'attachment; filename="%s"' % info['filename']
        response['Content-Type'] = info['mimetype']

        return response


    def get_fichero(self,id):
        """
        Devuelve un objeto HttpResponse con un fichero determinado
        """
        from django.http import HttpResponse
        
        response = HttpResponse()
        url = self.URL_BASE + "restAPI/default/%s/downloadFile" % str(id)
        self.curl.setopt(pycurl.URL, str(url))
        self.curl.setopt(pycurl.WRITEFUNCTION, response.write)
        self.curl.perform()
        
        export_url = self.URL_BASE + "restAPI/default/%s/export?format=XML" % str(id)
        file = self.get_xml(export_url)
        info = self.get_xml_file_info(file)
        response['Content-Disposition'] = 'attachment; filename="%s"' % info.get('filename')
        response['Content-Type'] = info.get('mimetype')
        
        return response
    
    def get_id_cont(self,contenedor):
        """
        Devuelve el id del contenedor.
        @param contenedor: path del contenedor
        """
        vocales = {'Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U',
                   'á':'A','é':'E','í':'I','ó':'O','ú':'U',}
        
        params = contenedor.split('/')       
        carpeta = params[-1]#.capitalize()
        
        if carpeta in vocales.keys():
            carpeta = vocales.get(carpeta)   
                     
        url = '/'.join(params[0:-1])
        file = self.get_by_attr([('searchpath',url),('title',carpeta)])
        nodos = self.get_nodos(file)
        
        for nodo in nodos:
            if nodo.getAttribute('title') == carpeta:
                return nodo.getAttribute('id')
            
        return ''
     
    def create_doc(self,contenedor,nombre,tipo,id=None):
        """
        Crea un documento de un tipo en un contenedor determinado
        """
        from django.utils.encoding import smart_str
        import urllib
        
        value_url = urllib.quote_plus(smart_str(nombre))
        id_cont = id
        if not id_cont:
            id_cont = self.get_id_cont(contenedor)
        file = None
        if id_cont:
            params = 'docType=%s&dublincore:title=%s' % (tipo,value_url)
            url = self.URL_BASE + "restAPI/default/%s/createDocument?%s" % (id_cont,params)
            file = self.get_xml(smart_str(url))
        
        return file
       
    def upload(self,id_carpeta,path,filename):
        """
        Sube un archivo a una Documento en Nuxeo
        """
        from django.utils.encoding import smart_str
        import urllib
        
        filename = urllib.quote_plus(smart_str(filename))
        b = StringIO()
        
        url = self.URL_BASE + "restAPI/default/%s/%s/uploadFile" % (str(id_carpeta),filename)
        
        self.curl.setopt(pycurl.POST, 1)
        self.curl.setopt(pycurl.URL, url)
        self.curl.setopt(pycurl.WRITEFUNCTION, b.write)
        self.curl.setopt(pycurl.HTTPPOST, [(filename, (pycurl.FORM_FILE , smart_str(path), pycurl.FORM_FILENAME, filename))])
        self.curl.perform()
        
        b.close()
        
        return True   

    def id_folder(self, file):
        """
        """
	from xml.dom import minidom

	docxml =  minidom.parse(file)
	nodes = docxml.childNodes
	for node in nodes:
	    childs = node.childNodes
	    for child in childs:
	       if child.nodeName == 'docRef':
	          id = child.childNodes[0].nodeValue

	return id

    def assign_permissions(self,doc_id,members=[],groups=[],permissions='Read'):
        """
        Asignación de permisos
        """
        from django.utils.encoding import smart_str
        import urllib
        
        if members:
            members_url = ','.join(map(lambda m:str(m.uid),members))
            members_url = urllib.quote_plus(smart_str(members_url))
            url = 'restAPI/default/%s/manageRights?action=add&user=%s&permission=%s&grant=true' % (doc_id,members_url,permissions)
            url = self.URL_BASE + url
            self.get_xml(smart_str(url))
            
        if groups:
            groups_url = ','.join(map(lambda g:str(g.identificador),groups))
            groups_url = urllib.quote_plus(smart_str(groups_url))
            url = 'restAPI/default/%s/manageRights?action=add&group=%s&permission=%s&grant=true' % (doc_id,groups_url,permissions)
            url = self.URL_BASE + url
            self.get_xml(smart_str(url))       
                    
    def close(self):
        """
        Cierra la conexión
        """
        self.curl.close()      
        

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file  = forms.FileField()

    

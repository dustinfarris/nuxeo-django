# Create your views here.
#def create_doc(self,contenedor,nombre,tipo,id=None):
#        """
#        Crea un documento de un tipo en un contenedor
#        determinado
#        """
#        from django.utils.encoding import smart_str
#        import urllib
#        
#        value_url = urllib.quote_plus(smart_str(nombre))
#        id_cont = id
#        if not id_cont:
#            id_cont = self.get_id_cont(contenedor)
#        file = None
#        if id_cont:
#            params = 'docType=%s&dublincore:title=%s' % (tipo,value_url)
#            url = self.URL_BASE + "restAPI/default/%s/createDocument?%s" % (id_cont,params)
#            file = self.get_xml(smart_str(url))
#        
#        return file

import elasticsearch as es
from django.conf import settings
from zipfile import ZipFile
import os

class ElasticSearchClient():
    '''
    Client for requesting elastic search entries.
    Singleton for a max of one instance.
    '''
    __instance = None
    def __init__(self) -> None:
        if ElasticSearchClient.__instance != None:
            raise Exception('ElasticSearchClient is a singleton. Please only use get_client()')
        else:
            self.client = es.Elasticsearch([settings.ELASTIC_URL], 
                                        http_auth=(settings.ELASTIC_USERNAME, settings.ELASTIC_PASSWORD),
                                        sniff_on_start=True,
                                        sniff_timeout=60,
                                        timeout=60)
            ElasticSearchClient.__instance = self

    @staticmethod
    def get_client():
        if settings.USE_ELASTIC:
            if ElasticSearchClient.__instance == None:
                ElasticSearchClient()
            return ElasticSearchClient.__instance
        else:
            return None

    def get_pod_logs(self, namespace, pod_name, page_number, size=100):
        '''
        Returns logs of a pod, and total amount of logs in the provided namespace.
        We have to split pod names at '-', because elastic interpretes '-' as an OR.
        '''
        must_match_query = [ {'match': {'kubernetes.pod_name': pod}} for pod in pod_name.split('-') ]
        must_match_query.append({'match': { 'kubernetes.namespace_name': namespace} })
        body = {
            'query' : {
                'bool': {
                    'must': must_match_query
                }, 
            },
            'size': size,
            'from': page_number * size,
            '_source': ['_id', 'log', 'stream'],
            'sort': {
                '@timestamp': 'desc',
            }
        }
        result = self.client.search(index='fluentd.demo-*', body=body)
        # val = result['hits']['total']['value']
        # relation = result['hits']['total']['relation']
        hits = result['hits']['hits'][::-1]
        return hits, result['hits']['total']

    def create_logs_zip(self, namespace, pod_name, size=100, keep_alive='2m'):
        '''
        Zips all found logs.
        Returns file path and file name of created zip file.
        '''
        must_match_query = [ {'match': {'kubernetes.pod_name': pod}} for pod in pod_name.split('-') ]
        must_match_query.append({'match': { 'kubernetes.namespace_name': namespace} })
        body = {
            'query' : {
                'bool': {
                    'must': must_match_query
                }, 
            },
            'size': size,
            '_source': ['log'],
            'sort': {
                '@timestamp': 'desc',
            }
        }


        file_name = f'tmp_{pod_name}_{namespace}'
        page = self.client.search(index='fluentd.demo-*', body=body, scroll=keep_alive, size=size )
        scroll_id = page['_scroll_id']
        hits = page['hits']['hits']

        txt_file = open( file_name + '.txt', 'a')
        for hit in hits:
            txt_file.write(hit['_source']['log'])

        while len(hits):
            page = self.client.scroll(scroll_id=scroll_id, scroll=keep_alive)
            scroll_id = page['_scroll_id']
            hits = page['hits']['hits']
            for hit in hits:
                txt_file.write(hit['_source']['log'])
        txt_file.close()
 
        with ZipFile( file_name + '.zip','w') as zip:
            zip.write( file_name + '.txt')
        file_path = os.path.realpath(file_name + '.zip') 
        return file_path, file_name + '.zip'
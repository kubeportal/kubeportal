import elasticsearch as es
from django.conf import settings

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
            return ElasticSearchClient.__instance.client
        else:
            return None

    def get_pod_logs(self, namespace, pod_name, page_number, size=100):
        '''
        Returns logs of a pod in the provided namespace.
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

        hits = result['hits']['hits']
        return hits


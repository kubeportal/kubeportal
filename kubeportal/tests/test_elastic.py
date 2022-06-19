from kubeportal.elastic.elastic_client import ElasticSearchClient
from django.conf import settings

def test_elastic_client_singleton(mocker):
    mocker.patch('elasticsearch.Elasticsearch')
    settings.USE_ELASTIC = True
    client = ElasticSearchClient.get_client()
    client2 = ElasticSearchClient.get_client()
    assert client == client2

def test_elastic_client(mocker):
    _example_hit = [
        {
            '_source': {
                'log': 'example log',
                'stream': 'stdout',
                '@timestamp': '2000-01-01T:10:00.000Z'
            },
            '_id': '1'
        }
    ]

    mocker.patch('kubeportal.elastic.elastic_client.ElasticSearchClient.get_pod_logs', return_value=(_example_hit, 1))
    client = ElasticSearchClient.get_client()
    hits, total = client.get_pod_logs('namespace', 'pod_name', 0)
    assert total >= len(hits)
    assert hits[0]['_source']['stream'] == 'stdout'